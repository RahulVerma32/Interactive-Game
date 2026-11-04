"""Copy the local SQLite stories and jobs into an empty PostgreSQL database.

Run from backend/: python -m scripts.migrate_sqlite_to_postgres
"""

import argparse
from pathlib import Path

from sqlalchemy import create_engine, func, insert, select, text
from sqlalchemy.engine import URL

from core.config import settings
from db.database import Base, database_url
from models.job import StoryJob
from models.story import Story, StoryNode


TABLES = (Story.__table__, StoryNode.__table__, StoryJob.__table__)


def copy_records(source_engine, target_engine):
    Base.metadata.create_all(target_engine)
    counts = {}
    with source_engine.connect() as source, target_engine.begin() as target:
        for table in TABLES:
            if target.scalar(select(func.count()).select_from(table)):
                raise ValueError(f"Target table {table.name} already has data; migration stopped")

        for table in TABLES:
            rows = [dict(row) for row in source.execute(select(table)).mappings()]
            if rows:
                target.execute(insert(table), rows)
            counts[table.name] = len(rows)

            if rows and target_engine.dialect.name == "postgresql":
                target.execute(
                    text("SELECT setval(pg_get_serial_sequence(:table, 'id'), :last_id, true)"),
                    {"table": table.name, "last_id": max(row["id"] for row in rows)},
                )
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("database.db"))
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"SQLite source does not exist: {args.source}")
    target_url = database_url(settings.DATABASE_URL_UNPOOLED or settings.DATABASE_URL)
    if target_url.get_backend_name() != "postgresql":
        parser.error("DATABASE_URL must point to PostgreSQL before migration")

    source_url = URL.create("sqlite", database=str(args.source.resolve()))
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url, pool_pre_ping=True)
    try:
        counts = copy_records(source_engine, target_engine)
        print("Migrated records:", counts)
    finally:
        source_engine.dispose()
        target_engine.dispose()


if __name__ == "__main__":
    main()

import time
import unittest
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.config import settings
from core.auth import current_user
from db.database import get_db
from routers import auth, story, job


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.db = MagicMock()
        self.db.execute.return_value.scalar.return_value = 1
        app = FastAPI()
        for router in (auth.router, story.router, job.router):
            app.include_router(router, prefix='/api')
        app.dependency_overrides[get_db] = lambda: self.db
        self.app = app
        self.base = patch.object(settings, 'NEON_AUTH_BASE_URL', 'https://auth.example/neondb/auth')
        self.url = patch.object(settings, 'NEON_AUTH_JWKS_URL', 'https://auth.example/jwks')
        self.jwks = patch('core.auth.jwks_client')
        self.base.start()
        self.url.start()
        mock_jwks = self.jwks.start()
        mock_jwks.return_value.get_signing_key_from_jwt.return_value.key = self.key.public_key()

    def tearDown(self):
        patch.stopall()

    def token(self, **overrides):
        claims = {'sub': 'account-123', 'iss': 'https://auth.example', 'exp': int(time.time()) + 300}
        claims.update(overrides)
        return jwt.encode(claims, self.key, algorithm='EdDSA', headers={'kid': 'test'})

    def test_missing_token_cannot_create_story_or_read_job(self):
        with self.assertRaises(HTTPException) as error:
            current_user(None, self.db)
        self.assertEqual(error.exception.status_code, 401)
        for path in ('/api/stories/create', '/api/jobs/{job_id}', '/api/stories/{story_id}/complete'):
            route = next(route for route in self.app.routes if route.path == path)
            self.assertTrue(any(dep.call is current_user for dep in route.dependant.dependencies))

    def test_valid_token_and_invalid_tokens(self):
        def get(token):
            return current_user(HTTPAuthorizationCredentials(scheme='Bearer', credentials=token), self.db)
        self.assertEqual(get(self.token()), 'user:account-123')
        for token in (self.token(exp=int(time.time()) - 20), self.token(iss='https://other.example'), self.token(iat=int(time.time()) + 30)):
            with self.assertRaises(HTTPException) as error:
                get(token)
            self.assertEqual(error.exception.status_code, 401)
        wrong = jwt.encode({'sub': 'account-123', 'iss': 'https://auth.example', 'exp': int(time.time()) + 300}, Ed25519PrivateKey.generate(), algorithm='EdDSA')
        with self.assertRaises(HTTPException):
            get(wrong)
        self.db.execute.return_value.scalar.return_value = None
        with self.assertRaises(HTTPException):
            get(self.token())

    def test_small_clock_difference_is_allowed(self):
        token = self.token(iat=int(time.time()) + 2)
        credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
        self.assertEqual(current_user(credentials, self.db), 'user:account-123')

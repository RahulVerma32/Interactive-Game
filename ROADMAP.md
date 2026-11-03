# AI Story Game roadmap

The current release generates a complete story tree before play. Stories and job status are private to the browser session that created them. This roadmap moves toward an adaptive story engine while keeping saved adventures playable.

## 1. Player state and saved progress

- Add a `playthroughs` table with story ID, owner session ID, current node ID, inventory, traits, relationships, and updated timestamp. Add a `choices` table recording node, selected option, state changes, and sequence number.
- Expose endpoints to start or resume a playthrough, select a valid choice, restart, and list the session's playthroughs. The server verifies that the selected option belongs to the current node and updates state and history in one transaction.
- Make the React game load progress from the server. Refreshing or returning to a story should resume at the last checkpoint. Show choice history and a map of visited nodes only.
- Acceptance: a choice survives refresh and a new tab in the same browser session; an unrelated session cannot read or change the playthrough; restart creates a clean playthrough without deleting history.

## 2. Generate one scene at a time

- Define a structured scene response containing narrative text, 2-3 choices or an ending, and explicit state changes. Feed the model a compact summary of prior choices plus current inventory, traits, and relationships. Validate all fields before saving.
- Generate the next scene only after a choice. Store the generated result by playthrough and choice so retries and revisits do not call the model twice. Keep the existing completed-tree stories readable during migration.
- Add a durable worker and queue for production generation. Include bounded model retries, a timeout, idempotent job IDs, cancellation or expiration, and failure recovery after a worker restart.
- Record per-scene latency, model, input/output tokens, estimated cost, and validation failures. Compare these with the existing whole-tree approach using the same themes.
- Acceptance: earlier decisions can change a later scene or available choice; revisiting a saved scene returns the stored text; a worker restart does not leave a job pending forever.

## 3. Story controls and replay

- Add genre, tone, target length, and protagonist fields with constrained values and sensible defaults. Offer curated themes and one pre-generated story that works without an API key.
- Build a library with titles, last-played timestamps, and resume actions. Add a choice-history panel and visited-branch map. Keep private stories private; add separate public share tokens and opt-in publishing for shareable stories or endings.
- Acceptance: a new visitor can play the demo immediately; a returning player can find and resume saved stories; a private story URL is inaccessible to another session, while an explicitly shared link works.

## 4. Quality and launch

- Add backend tests for scene validation, choice/state transactions, authorization, duplicate jobs, and worker failures. Add a browser test for generate, play, refresh, resume, and restart with a mocked model.
- Evaluate a fixed set of themes for JSON validity, continuity, choice consequences, win/loss endings, latency, and cost. Report sample size and measured results in the README.
- Add database migrations, CI, container setup, structured logs, rate limits, a hosted demo, screenshots, and an architecture diagram. Audit keyboard interaction, contrast, mobile layout, and loading/error states.
- Acceptance: CI passes, the demo can be played without secrets, and the README shows reproducible setup plus measured results rather than unverified claims.

# Sahifa Quiz V34 — Hardened

Professional Telegram book-quiz bot for **Sahifa orqasida**.

## What changed in V34

- User navigation is centralized and registered before feature/FSM handlers.
- Admin question creation and TXT import use unique callback namespaces (`admqbook:*`, `admimportbook:*`).
- TXT import only requires question + A/B/C/D + ANSWER. `DIFFICULTY` and `EXPLANATION` are ignored when present.
- Parser accepts `A:`, `A)`, `A.` and `ANSWER: A/B/C/D/1/2/3/4`.
- Quiz answer callbacks bind `attempt_id + question index + option`.
- Redis lock + PostgreSQL unique constraint prevent double-answer recording.
- Completed and abandoned attempts are separated.
- Webhook always refreshes `allowed_updates` so `channel_post` cannot remain missing from an old configuration.
- Webhook returns non-2xx on processing failure so Telegram can retry delivery.
- `/live` is a cheap UptimeRobot liveness endpoint; `/health` checks PostgreSQL and Redis.
- Automatic channel reaction stores the last channel post, checks configured reaction availability, and exposes an admin test button.
- HTML is centralized, dynamic content is escaped, and UI uses structured blocks, progress bars, spacing, emoji and inline buttons.
- Referral and weekly/monthly/seasonal TOP features are absent by design.

## TXT format

```text
1. Savol matni?
A: Variant A
B: Variant B
C: Variant C
D: Variant D
ANSWER: B

2. Ikkinchi savol?
A: Variant A
B: Variant B
C: Variant C
D: Variant D
ANSWER: 1
```

Maximum import: **100 questions**.

## Render

Build:

```bash
pip install -r requirements.txt
```

Start:

```bash
alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

UptimeRobot:

```text
https://YOUR-SERVICE.onrender.com/live
```

Render health check:

```text
/health
```

## Channel reaction requirements

1. Set `TARGET_CHANNEL_ID`.
2. Add the bot as an administrator in the target channel.
3. Make sure the target channel permits the emoji reaction selected in the admin panel.
4. Keep `reaction_enabled` ON.
5. Publish a new channel post; the bot stores that post ID and attempts the configured reaction.
6. Use **❤️ REACTION → 🧪 TEST REACTION** for a deterministic diagnostic.

## Research basis

The structure follows patterns observed in modern public aiogram templates: modular Routers, explicit webhook handling, PostgreSQL/SQLAlchemy migrations, Redis FSM, middleware-based dependencies, rate/ban guards, service/repository separation, logging and test suites. The project was rebuilt as original code rather than copying project source.


## Verification

Offline verification included in this package:

```text
compileall: PASS
pytest: 28 passed
TXT parser: verified against a 54-question sample
constants import audit: PASS
render.yaml parse: PASS
```

The runtime dependencies are pinned for deployment. A real Telegram/Render smoke test still requires the project to be run against your actual bot token, PostgreSQL, Redis/Valkey and channel; this package does not claim a live production test from the build environment.

# ExileQuest Tracker

A Django web app for tracking Path of Exile 1 campaign quest completion (Acts 1–10), with a focus on passive skill points and refund points from quests.

## ToS Compliance

**This application is fully compliant with Grinding Gear Games' Terms of Service.**

- It is a **standalone web application** — no overlays, no memory reading, no client hooks, no game file modifications.
- It does **not** automate any input or provide macros.
- It does **not** read `Client.txt` or any game files.
- All quest data is sourced from the community-maintained [PoE Wiki](https://www.poewiki.net/).

> "Not affiliated with or endorsed by Grinding Gear Games."

References:
- [GGG Developer Docs](https://www.pathofexile.com/developer/docs)
- [GGG Third Party Policy](https://www.pathofexile.com/developer/docs)

## Features

- **User accounts** with Django auth (register/login)
- **Character profiles** with league, realm, and bandits choice
- **Quest checklist** grouped by Act 1–10 with:
  - Quest name, NPC, zone, location hints
  - Reward badges: passive points, refund points, other
  - Status tracking: Not started / In progress / Completed / Skipped
  - Reward collected (yes/no) — because you can complete a quest but forget to claim
  - Per-quest notes
- **Pinned quests** section — passive point quests and key quests pinned by default
- **Progress summary bars**:
  - Passive Points from Quests: X / 22 (or X / 24 with Kill All bandits)
  - Refund Points from Quests: Y / 20
- **In-game verification**: `/passives` command help box
- **Filters & search**: by act, reward type, status, text search
- **HTMX inline updates** — change status/reward/notes without page reload
- **Public share links** — read-only, no user info exposed
- **JSON export/import** for progress backup
- **Dark mode** Bootstrap 5 UI

## Quick Start (Local, venv)

```bash
# Clone and enter the project
cd poe_tracker

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed quest data
python manage.py seed_quests

# Create a superuser (optional, for admin)
python manage.py createsuperuser

# Run the dev server
python manage.py runserver
```

Open http://localhost:8000 in your browser.

## Quick Start (Docker Compose)

```bash
docker compose up --build
```

This will:
1. Build the Docker image
2. Run migrations
3. Seed quest data
4. Start the server on http://localhost:8000

## Running Tests

```bash
source venv/bin/activate
python manage.py test quests
```

## Switching to PostgreSQL

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL=postgres://user:password@localhost:5432/exilequest
python manage.py migrate
python manage.py seed_quests
```

Or in `docker-compose.yml`, add a `db` service and update `DATABASE_URL`.

## Quest Dataset

### Source
Quest data is stored in `quests/data/quests.json` and sourced from:
- [PoE Wiki - Quest Rewards](https://www.poewiki.net/wiki/Quest_Rewards)
- [PoE Wiki - Passive skill](https://www.poewiki.net/wiki/Passive_skill)
- [PoE Wiki - Deal with the Bandits](https://www.poewiki.net/wiki/Deal_with_the_Bandits)
- [PoE Wiki - Quest list](https://www.poewiki.net/wiki/Quest)

### Updating the Dataset

1. Edit `quests/data/quests.json`
2. Bump `dataset_version` (e.g. `"1.0.0"` → `"1.1.0"`)
3. Update `last_verified_at` to today's date
4. Run: `python manage.py seed_quests`

The seed command uses `update_or_create` keyed on `slug`, so existing quests are updated and new ones are created.

### Data Summary
- **22 passive skill points** from quests (base, without bandits)
- **+2 passive skill points** if Kill All bandits (Deal with the Bandits quest)
- **20 refund/respec points** from quests
- Total quests tracked: ~50+ across Acts 1–10

### Verifying In-Game
Type `/passives` in the PoE chat window to see which quests have granted passive skill points to your character. Compare against the app's checklist.

## Project Structure

```
poe_tracker/
├── exilequest/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── quests/              # Main app
│   ├── data/
│   │   └── quests.json  # Quest seed data with versioning
│   ├── management/
│   │   └── commands/
│   │       └── seed_quests.py
│   ├── migrations/
│   ├── templatetags/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py        # Quest, CharacterProfile, QuestProgress
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/
│   ├── base.html
│   ├── registration/
│   │   ├── login.html
│   │   └── register.html
│   └── quests/
│       ├── home.html
│       ├── character_list.html
│       ├── character_edit.html
│       ├── character_delete.html
│       ├── quest_list.html
│       └── partials/
│           └── quest_row.html
├── static/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
└── README.md
```

## License

MIT

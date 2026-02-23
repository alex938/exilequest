# ExileQuest

PoE1 quest & reward reference (Acts 1–10). Tracks passive points, refund points, and key quest rewards.

Not affiliated with or endorsed by Grinding Gear Games. Quest data sourced from [PoE Wiki](https://www.poewiki.net/).

## Run

```bash
docker compose up --build
```

Or locally:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate && python manage.py seed_quests
python manage.py runserver
```

## Environment

Copy `.env.example` to `.env` and set `SECRET_KEY` and `ALLOWED_HOSTS`. See `.env.example` for details.

## License

MIT

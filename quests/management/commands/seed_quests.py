import json
from pathlib import Path

from django.core.management.base import BaseCommand

from quests.models import Quest


class Command(BaseCommand):
    help = "Load quest data from quests/data/quests.json into the Quest model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=str(Path(__file__).resolve().parent.parent.parent / "data" / "quests.json"),
            help="Path to the quests.json file",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing quests even if they exist",
        )

    def handle(self, *args, **options):
        filepath = Path(options["file"])
        if not filepath.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {filepath}"))
            return

        with open(filepath, "r") as f:
            data = json.load(f)

        version = data.get("dataset_version", "unknown")
        last_verified = data.get("last_verified_at", "unknown")
        quests = data.get("quests", [])

        self.stdout.write(
            f"Loading dataset v{version} (verified: {last_verified}) — {len(quests)} quests"
        )

        created = 0
        updated = 0
        for q in quests:
            slug = q["slug"]
            fields = {
                "act": q["act"],
                "name": q["name"],
                "npc": q.get("npc", ""),
                "primary_zone": q.get("primary_zone", ""),
                "zones_json": q.get("zones_json", []),
                "hint_text": q.get("hint_text", ""),
                "is_required": q.get("is_required", False),
                "gives_passive_point": q.get("gives_passive_point", False),
                "passive_points": q.get("passive_points", 0),
                "gives_refund_points": q.get("gives_refund_points", False),
                "refund_points": q.get("refund_points", 0),
                "gives_other": q.get("gives_other", False),
                "other_reward_text": q.get("other_reward_text", ""),
                "is_pinned_default": q.get("is_pinned_default", False),
                "sort_order": q.get("sort_order", 0),
            }

            obj, was_created = Quest.objects.update_or_create(
                slug=slug, defaults=fields
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created} created, {updated} updated, {created + updated} total"
            )
        )

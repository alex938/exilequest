import json
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Quest

DATA_FILE = Path(__file__).resolve().parent / "data" / "quests.json"

# The manifest storage needs collectstatic to have run; tests don't need hashed names.
PLAIN_STATIC = override_settings(STORAGES={
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


class DatasetTest(TestCase):
    """Sanity-check the raw quest dataset."""

    @classmethod
    def setUpTestData(cls):
        cls.quests = json.loads(DATA_FILE.read_text())["quests"]

    def test_slugs_unique(self):
        slugs = [q["slug"] for q in self.quests]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_sort_order_unique_within_act(self):
        keys = [(q["act"], q["sort_order"]) for q in self.quests]
        self.assertEqual(len(keys), len(set(keys)))

    def test_reward_flags_match_counts(self):
        for q in self.quests:
            with self.subTest(q["slug"]):
                self.assertEqual(q["gives_passive_point"], q["passive_points"] > 0)
                self.assertEqual(q["gives_refund_points"], q["refund_points"] > 0)
                if q["other_reward_text"]:
                    self.assertTrue(q["gives_other"])

    def test_acts_in_range(self):
        self.assertEqual({q["act"] for q in self.quests}, set(range(1, 11)))


class SeedQuestsTest(TestCase):
    """Test the seed_quests management command."""

    def test_seed_creates_quests(self):
        self.assertEqual(Quest.objects.count(), 0)
        call_command("seed_quests")
        self.assertGreater(Quest.objects.count(), 0)

    def test_seed_idempotent(self):
        call_command("seed_quests")
        count1 = Quest.objects.count()
        call_command("seed_quests")
        self.assertEqual(count1, Quest.objects.count())

    def test_seed_removes_stale_quests(self):
        Quest.objects.create(act=1, name="Old Quest", slug="old-quest")
        call_command("seed_quests")
        self.assertFalse(Quest.objects.filter(slug="old-quest").exists())

    def test_passive_point_total(self):
        # 23 from quests, +1 for killing all bandits
        call_command("seed_quests")
        total = sum(q.passive_points for q in Quest.objects.filter(gives_passive_point=True))
        self.assertEqual(total, 24)

    def test_bandits_quest(self):
        call_command("seed_quests")
        bandits = Quest.objects.get(slug="deal-with-the-bandits")
        self.assertTrue(bandits.gives_passive_point)
        self.assertEqual(bandits.passive_points, 1)

    def test_refund_point_total(self):
        call_command("seed_quests")
        total = sum(q.refund_points for q in Quest.objects.filter(gives_refund_points=True))
        self.assertEqual(total, 20)


@PLAIN_STATIC
class QuestListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_quests")

    def get(self, **params):
        return self.client.get(reverse("quest_list"), params)

    def test_renders_all_acts(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["acts"]), list(range(1, 11)))
        self.assertEqual(response.context["total_passive"], 24)
        self.assertEqual(response.context["total_refund"], 20)
        self.assertEqual(response.context["total_quests"], Quest.objects.count())

    def test_filter_act(self):
        response = self.get(act="3")
        self.assertEqual(list(response.context["acts"]), [3])

    def test_invalid_act_ignored(self):
        response = self.get(act="abc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["acts"]), 10)
        self.assertEqual(response.context["filter_act"], "")

    def test_filter_passive(self):
        response = self.get(reward="passive")
        quests = [q for qs in response.context["acts"].values() for q in qs]
        self.assertTrue(quests)
        self.assertTrue(all(q.gives_passive_point for q in quests))

    def test_filter_required(self):
        response = self.get(reward="required")
        quests = [q for qs in response.context["acts"].values() for q in qs]
        self.assertTrue(quests)
        self.assertTrue(all(q.is_required for q in quests))

    def test_search(self):
        response = self.get(q="Kitava")
        names = {q.name for qs in response.context["acts"].values() for q in qs}
        self.assertIn("The Ravenous God", names)
        self.assertIn("An End to Hunger", names)

    def test_no_results(self):
        response = self.get(q="zzzz-nothing")
        self.assertContains(response, "No quests match your filters.")

    def test_query_count(self):
        with self.assertNumQueries(2):
            self.get()

    def test_post_not_allowed(self):
        response = self.client.post(reverse("quest_list"))
        self.assertEqual(response.status_code, 405)


class HealthzTest(TestCase):
    def test_healthz(self):
        response = self.client.get(reverse("healthz"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

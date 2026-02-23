import uuid
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse

from .models import CharacterProfile, Quest, QuestProgress


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
        count2 = Quest.objects.count()
        self.assertEqual(count1, count2)

    def test_passive_point_quests_exist(self):
        call_command("seed_quests")
        passive_quests = Quest.objects.filter(gives_passive_point=True)
        # Should have multiple passive point quests
        self.assertGreaterEqual(passive_quests.count(), 15)

    def test_bandits_quest_exists(self):
        call_command("seed_quests")
        bandits = Quest.objects.get(slug="deal-with-the-bandits")
        self.assertTrue(bandits.gives_passive_point)
        self.assertEqual(bandits.passive_points, 1)
        self.assertTrue(bandits.is_pinned_default)

    def test_refund_point_quests_exist(self):
        call_command("seed_quests")
        refund_quests = Quest.objects.filter(gives_refund_points=True)
        total_refund = sum(q.refund_points for q in refund_quests)
        self.assertEqual(total_refund, 20)


class ProgressUpdateTest(TestCase):
    """Test HTMX quest progress updates."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")
        call_command("seed_quests")

        self.character = CharacterProfile.objects.create(
            user=self.user, name="TestChar", league="Standard"
        )
        # Create progress entries
        for quest in Quest.objects.all():
            QuestProgress.objects.create(character=self.character, quest=quest)

    def test_update_status(self):
        quest = Quest.objects.first()
        url = reverse("update_quest_progress", args=[self.character.pk, quest.pk])
        response = self.client.post(url, {"status": "COMPLETED"})
        self.assertEqual(response.status_code, 200)

        progress = QuestProgress.objects.get(character=self.character, quest=quest)
        self.assertEqual(progress.status, "COMPLETED")
        self.assertIsNotNone(progress.completed_at)

    def test_update_reward_collected(self):
        quest = Quest.objects.first()
        url = reverse("update_quest_progress", args=[self.character.pk, quest.pk])
        response = self.client.post(url, {"status": "COMPLETED", "reward_collected": "on"})
        self.assertEqual(response.status_code, 200)

        progress = QuestProgress.objects.get(character=self.character, quest=quest)
        self.assertTrue(progress.reward_collected)

    def test_cannot_update_other_users_character(self):
        other_user = User.objects.create_user("otheruser", password="otherpass123")
        other_char = CharacterProfile.objects.create(
            user=other_user, name="OtherChar", league="Standard"
        )
        quest = Quest.objects.first()
        QuestProgress.objects.create(character=other_char, quest=quest)

        url = reverse("update_quest_progress", args=[other_char.pk, quest.pk])
        response = self.client.post(url, {"status": "COMPLETED"})
        self.assertEqual(response.status_code, 404)


class ShareLinkTest(TestCase):
    """Test share link is read-only and requires enabled token."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        call_command("seed_quests")
        self.character = CharacterProfile.objects.create(
            user=self.user, name="ShareChar", league="Standard",
        )
        for quest in Quest.objects.all():
            QuestProgress.objects.create(character=self.character, quest=quest)

    def test_share_disabled_returns_404(self):
        self.assertFalse(self.character.is_share_enabled)
        url = reverse("shared_quest_list", args=[self.character.share_token])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_share_enabled_returns_200(self):
        self.character.is_share_enabled = True
        self.character.save()
        url = reverse("shared_quest_list", args=[self.character.share_token])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ShareChar")
        self.assertContains(response, "Read-only view")

    def test_share_no_edit_forms(self):
        self.character.is_share_enabled = True
        self.character.save()
        url = reverse("shared_quest_list", args=[self.character.share_token])
        response = self.client.get(url)
        # Should NOT have hx-post (HTMX update forms)
        self.assertNotContains(response, "hx-post")

    def test_invalid_token_returns_404(self):
        url = reverse("shared_quest_list", args=[uuid.uuid4()])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_share_no_user_info(self):
        self.character.is_share_enabled = True
        self.character.save()
        url = reverse("shared_quest_list", args=[self.character.share_token])
        response = self.client.get(url)
        # Username should NOT appear in the share page
        self.assertNotContains(response, self.user.username)


class CharacterModelTest(TestCase):
    """Test character model properties."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")

    def test_max_passive_points_unknown(self):
        char = CharacterProfile.objects.create(
            user=self.user, name="Test", bandits_choice="UNKNOWN"
        )
        self.assertEqual(char.max_passive_points, 23)

    def test_max_passive_points_kill_all(self):
        char = CharacterProfile.objects.create(
            user=self.user, name="Test", bandits_choice="KILL_ALL"
        )
        self.assertEqual(char.max_passive_points, 24)

    def test_max_passive_points_help_alira(self):
        char = CharacterProfile.objects.create(
            user=self.user, name="Test", bandits_choice="HELP_ALIRA"
        )
        self.assertEqual(char.max_passive_points, 23)


class QuestListViewTest(TestCase):
    """Test the character quest list view."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")
        call_command("seed_quests")
        self.character = CharacterProfile.objects.create(
            user=self.user, name="ViewChar", league="Standard",
        )

    def test_quest_list_requires_login(self):
        self.client.logout()
        url = reverse("character_quests", args=[self.character.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_quest_list_shows_acts(self):
        url = reverse("character_quests", args=[self.character.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Act 1")
        self.assertContains(response, "Act 10")

    def test_quest_list_shows_pinned(self):
        url = reverse("character_quests", args=[self.character.pk])
        response = self.client.get(url)
        self.assertContains(response, "Pinned Quests")

    def test_quest_list_shows_verify_box(self):
        url = reverse("character_quests", args=[self.character.pk])
        response = self.client.get(url)
        self.assertContains(response, "/passives")

    def test_quest_list_shows_disclaimer(self):
        url = reverse("character_quests", args=[self.character.pk])
        response = self.client.get(url)
        self.assertContains(response, "Not affiliated with or endorsed by Grinding Gear Games")

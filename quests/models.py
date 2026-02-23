from django.db import models
from django.utils.text import slugify


class Quest(models.Model):
    """A quest in PoE1 Acts 1-10. Populated from seed data."""

    act = models.PositiveSmallIntegerField(db_index=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    npc = models.CharField(max_length=200, blank=True, help_text="NPC who gives/completes the quest")
    primary_zone = models.CharField(max_length=200, blank=True)
    zones_json = models.JSONField(
        default=list, blank=True,
        help_text="List of zone names involved in the quest",
    )
    hint_text = models.TextField(blank=True, help_text="Rough location / gameplay hint")
    is_required = models.BooleanField(default=False, help_text="Required for campaign progression")

    # Reward flags
    gives_passive_point = models.BooleanField(default=False, db_index=True)
    passive_points = models.PositiveSmallIntegerField(
        default=0, help_text="Number of passive skill points granted",
    )
    gives_refund_points = models.BooleanField(default=False, db_index=True)
    refund_points = models.PositiveSmallIntegerField(
        default=0, help_text="Number of refund/respec points granted",
    )
    gives_other = models.BooleanField(
        default=False, help_text="Grants non-point rewards (gems, items, etc.)",
    )
    other_reward_text = models.CharField(max_length=300, blank=True)

    is_pinned_default = models.BooleanField(
        default=False, help_text="Pinned by default in the quest list",
    )

    # Ordering within an act
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["act", "sort_order", "name"]

    def __str__(self):
        return f"Act {self.act}: {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

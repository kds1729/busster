"""
Songs and the GT-1000 patches they use.

A Song has up to SLOT_COUNT slots (the 8 footswitches). Each Slot holds one
GT-1000 patch and a short label saying what that sound is for ("clean intro",
"solo"). Stepping through the slots in order walks through the song.

Patches are stored as a raw 0-based index 0..499 so the same row works for
both units:
    index   0..249  -> user patches    (CORE: U001..U250, full-size: U01-1..U50-5)
    index 250..499  -> preset patches  (CORE: P001..P250, full-size: P01-1..P50-5)
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

SLOT_COUNT = 8
USER_PATCHES = 250
PRESET_PATCHES = 250
TOTAL_PATCHES = USER_PATCHES + PRESET_PATCHES


def format_patch_core(index: int) -> str:
    """GT-1000CORE style: U001 .. U250, P001 .. P250."""
    area, local = ("U", index) if index < USER_PATCHES else ("P", index - USER_PATCHES)
    return f"{area}{local + 1:03d}"


def format_patch_full(index: int) -> str:
    """Full-size GT-1000 style: U01-1 .. U50-5, P01-1 .. P50-5."""
    area, local = ("U", index) if index < USER_PATCHES else ("P", index - USER_PATCHES)
    bank, slot = divmod(local, 5)
    return f"{area}{bank + 1:02d}-{slot + 1}"


class Song(models.Model):
    name = models.CharField(max_length=200, unique=True)
    artist = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Slot(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="slots")
    position = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(SLOT_COUNT)],
        help_text=f"Footswitch number, 1 to {SLOT_COUNT}.",
    )
    patch = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(TOTAL_PATCHES - 1)],
        help_text="0-based patch index: 0-249 user (U001/U01-1 ...), 250-499 preset.",
    )
    patch_name = models.CharField(
        max_length=16, blank=True,
        help_text="Name as shown on the GT-1000. Read from the unit automatically when the slot is saved.",
    )
    label = models.CharField(max_length=100, blank=True, help_text='e.g. "Clean intro", "Solo".')

    class Meta:
        ordering = ["song", "position"]
        constraints = [
            models.UniqueConstraint(fields=["song", "position"], name="unique_slot_per_song"),
        ]

    def __str__(self) -> str:
        return f"{self.song} #{self.position}: {self.patch_core}"

    @property
    def patch_core(self) -> str:
        return format_patch_core(self.patch)

    @property
    def patch_full(self) -> str:
        return format_patch_full(self.patch)

    def display_text(self, style: str = "core") -> str:
        """What the display shows for this slot, e.g. "U061 - GIG READY"."""
        number = self.patch_full if style == "full" else self.patch_core
        return f"{number} - {self.patch_name}" if self.patch_name else number

    def clean(self):
        if self.patch is not None and not 0 <= self.patch < TOTAL_PATCHES:
            raise ValidationError({"patch": f"Patch index must be 0 to {TOTAL_PATCHES - 1}."})

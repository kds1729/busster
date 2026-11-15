"""
Songs and the GT-1000 patches they use.

A Song has slots, one per footswitch. Each Slot holds one GT-1000 patch and a
short label saying what that sound is for ("clean intro", "solo"). Stepping
through the slots in order walks through the song.

Normally a song has up to SLOT_COUNT slots (the 8 footswitches). A song with
`paginate` on gives up switch 8 to page through its slots PAGE_SIZE (7) at a
time, so it can have any number of slots: positions 1-7 are page 1, 8-14 are
page 2, and so on. See junior/docs/profiles-format.md, "Pagination".

Patches are stored as a raw 0-based index 0..499 so the same row works for
both units:
    index   0..249  -> user patches    (CORE: U001..U250, full-size: U01-1..U50-5)
    index 250..499  -> preset patches  (CORE: P001..P250, full-size: P01-1..P50-5)
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

SLOT_COUNT = 8   # footswitches, and the slot limit for a song that does not paginate
PAGE_SIZE = 7    # slots per page when a song paginates (switch 8 turns the page)
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
    paginate = models.BooleanField(
        default=False,
        help_text=f"Rarely needed: only for a song with more than {SLOT_COUNT} patches. Switch 8 then "
                  f"pages through the slots {PAGE_SIZE} at a time instead of selecting a patch, and its "
                  f"LED turns red.",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def page_count(self) -> int:
        """Pages of PAGE_SIZE slots when paginating; always 1 otherwise."""
        if not self.paginate:
            return 1
        top = max((s.position for s in self.slots.all()), default=1)
        return max(1, -(-top // PAGE_SIZE))

    @property
    def slot_capacity(self) -> int:
        """Length of the slot array the floor unit sees: 8, or a whole number of pages."""
        return self.page_count * PAGE_SIZE if self.paginate else SLOT_COUNT

    def max_position(self) -> int | None:
        """Highest allowed slot position, or None when paginating (no limit)."""
        return None if self.paginate else SLOT_COUNT


class Slot(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="slots")
    position = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text=f"Footswitch number, 1 to {SLOT_COUNT}. On a paginating song any number: "
                  f"1-{PAGE_SIZE} is page 1, {PAGE_SIZE + 1}-{2 * PAGE_SIZE} is page 2, and so on.",
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

    @property
    def page(self) -> int:
        """0-based page this slot is on when its song paginates; 0 otherwise."""
        return (self.position - 1) // PAGE_SIZE if self.song.paginate else 0

    @property
    def switch(self) -> int:
        """Footswitch (1-based) that selects this slot on its page."""
        return (self.position - 1) % PAGE_SIZE + 1 if self.song.paginate else self.position

    def clean(self):
        errors = {}
        if self.patch is not None and not 0 <= self.patch < TOTAL_PATCHES:
            errors["patch"] = f"Patch index must be 0 to {TOTAL_PATCHES - 1}."
        # The song is unknown while the admin validates slots of a song that is
        # not saved yet (RelatedObjectDoesNotExist is an AttributeError); then
        # only the field validators apply.
        song = getattr(self, "song", None)
        if song is not None and self.position is not None:
            limit = song.max_position()
            if limit is not None and self.position > limit:
                errors["position"] = (f"Position must be 1 to {limit}. Turn on pagination for "
                                      f"the song to use more than {limit} slots.")
        if errors:
            raise ValidationError(errors)

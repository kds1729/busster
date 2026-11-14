"""
Re-read patch names from the connected GT-1000.

Owners rename and overwrite their user patches, so a name captured when a slot
was assigned can go stale. Refreshing reads the current name for every patch
the songs use and updates the slots whose name changed, so the next export
carries what the unit shows today.

User patches are read straight from the unit's memory. Preset names are
factory-fixed and reading one means switching the unit to that patch, so
presets are skipped unless asked for.
"""

from dataclasses import dataclass, field

from . import midi
from .models import USER_PATCHES, Slot


@dataclass
class Change:
    slot: Slot
    old: str
    new: str


@dataclass
class RefreshResult:
    patches_read: int = 0
    slots_checked: int = 0
    changes: list[Change] = field(default_factory=list)
    failures: dict[int, str] = field(default_factory=dict)  # patch index -> error
    aborted: str | None = None  # set when the unit could not be reached at all

    @property
    def changed(self) -> int:
        return len(self.changes)

    def summary(self) -> str:
        parts = [f"{self.patches_read} patch{'es' if self.patches_read != 1 else ''} read",
                 f"{self.slots_checked} slot{'s' if self.slots_checked != 1 else ''} checked",
                 f"{self.changed} name{'s' if self.changed != 1 else ''} changed"]
        if self.failures:
            parts.append(f"{len(self.failures)} could not be read")
        return ", ".join(parts)


def refresh_names(slots, include_presets: bool = False) -> RefreshResult:
    """Read each distinct patch once and update every slot whose name differs."""
    result = RefreshResult()
    slots = list(slots)
    if not include_presets:
        slots = [s for s in slots if s.patch < USER_PATCHES]
    result.slots_checked = len(slots)

    names: dict[int, str] = {}
    for index in sorted({s.patch for s in slots}):
        try:
            names[index] = midi.read_patch_name(index)
            result.patches_read += 1
        except ConnectionError as e:
            # No unit: don't repeat the same failure for every patch.
            result.aborted = str(e)
            return result
        except (TimeoutError, OSError, ValueError) as e:
            result.failures[index] = str(e)

    for slot in slots:
        new = names.get(slot.patch)
        if new is None or new == slot.patch_name:
            continue
        result.changes.append(Change(slot, slot.patch_name, new))
        slot.patch_name = new
        slot.save(update_fields=["patch_name"])
    return result

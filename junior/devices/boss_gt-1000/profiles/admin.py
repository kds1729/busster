from django.contrib import admin, messages
from django.forms.models import BaseInlineFormSet

from . import midi
from .models import PAGE_SIZE, SLOT_COUNT, Slot, Song
from .names import refresh_names


def fill_patch_name(slot: Slot, request) -> None:
    """Read the patch name from the connected GT-1000 and store it on the slot."""
    try:
        slot.patch_name = midi.read_patch_name(slot.patch)
    except (ConnectionError, TimeoutError, OSError, ValueError) as e:
        messages.warning(request, f"Switch {slot.position} ({slot.patch_core}): could not read the patch name from the GT-1000: {e}")


def needs_name(slot: Slot) -> bool:
    if not slot.pk:
        return True
    old = Slot.objects.filter(pk=slot.pk).values_list("patch", "patch_name").first()
    return old is None or old[0] != slot.patch or not slot.patch_name


def report_refresh(request, result) -> None:
    if result.aborted:
        messages.error(request, f"Could not reach the GT-1000: {result.aborted}")
        return
    for c in result.changes:
        messages.info(request, f'{c.slot.song} switch {c.slot.position} ({c.slot.patch_core}): "{c.old}" is now "{c.new}"')
    for index, err in result.failures.items():
        messages.warning(request, f"Patch index {index}: {err}")
    messages.success(request, f"Patch names refreshed: {result.summary()}.")


@admin.action(description="Re-read patch names from the GT-1000")
def refresh_song_names(modeladmin, request, queryset):
    report_refresh(request, refresh_names(Slot.objects.filter(song__in=queryset).select_related("song")))


@admin.action(description="Re-read patch names from the GT-1000")
def refresh_slot_names(modeladmin, request, queryset):
    report_refresh(request, refresh_names(queryset.select_related("song")))


class SlotFormSet(BaseInlineFormSet):
    """Give each slot its song before validation, so Slot.clean() can apply the
    song's position limit. Django only sets the song *id* here, and on a change
    the slot would otherwise load the song from the database, with the
    pagination setting as it was before this submit rather than as posted."""

    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        form.instance.song = self.instance
        return form


class SlotInline(admin.TabularInline):
    model = Slot
    formset = SlotFormSet
    fields = ("position", "on_page", "patch", "patch_core", "patch_full", "patch_name", "label")
    readonly_fields = ("on_page", "patch_core", "patch_full")
    ordering = ("position",)

    def get_max_num(self, request, obj=None, **kwargs):
        """8 rows for a plain song; no limit once the song paginates."""
        return None if obj is not None and obj.paginate else SLOT_COUNT

    def get_extra(self, request, obj=None, **kwargs):
        return PAGE_SIZE if obj is not None and obj.paginate else SLOT_COUNT

    @admin.display(description="Page / switch")
    def on_page(self, obj):
        if not obj.pk or not obj.song.paginate:
            return ""
        return f"page {obj.page + 1}, switch {obj.switch}"

    @admin.display(description="CORE")
    def patch_core(self, obj):
        return obj.patch_core if obj.pk else ""

    @admin.display(description="GT-1000")
    def patch_full(self, obj):
        return obj.patch_full if obj.pk else ""


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("name", "artist", "slot_count", "paginate", "updated")
    list_filter = ("paginate",)
    search_fields = ("name", "artist")
    inlines = [SlotInline]
    actions = [refresh_song_names]

    @admin.display(description="Slots")
    def slot_count(self, obj):
        return obj.slots.count()

    def save_formset(self, request, form, formset, change):
        for slot in formset.save(commit=False):
            if needs_name(slot):
                fill_patch_name(slot, request)
            slot.save()
        for slot in formset.deleted_objects:
            slot.delete()
        formset.save_m2m()


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("song", "position", "patch_core", "patch_full", "patch_name", "label")
    list_filter = ("song",)
    ordering = ("song__name", "position")
    actions = [refresh_slot_names]

    def save_model(self, request, obj, form, change):
        if needs_name(obj):
            fill_patch_name(obj, request)
        super().save_model(request, obj, form, change)

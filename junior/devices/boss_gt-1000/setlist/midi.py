"""
Send GT-1000 patch changes from the laptop.

Message sequence (Roland GT-1000/GT-1000CORE MIDI Implementation v4.01):
    CC#0  = bank             Bank Select MSB
    CC#32 = 0                Bank Select LSB, always 0
    Program Change = 0..124

Measured on a GT-1000CORE on 2026-11-14 (MAP SEL = PROG, factory map):
each bank holds 125 patches, i.e. 25 of the full-size unit's 5-patch banks.
    bank 0, PC 0..124 -> U001..U125
    bank 1, PC 0..124 -> U126..U250
    bank 2, PC 0..124 -> P001..P125
    bank 3, PC 0..124 -> P126..P250   (not yet verified on hardware)
PC 125..127 clamp to the bank's last patch. So patch index = bank * 125 + program.
"""

import logging
import threading

import mido
from django.conf import settings

log = logging.getLogger(__name__)

PROGRAMS_PER_BANK = 125
MAX_BANK = 3
MAX_REACHABLE = (MAX_BANK + 1) * PROGRAMS_PER_BANK  # 500


def port_name() -> str:
    return getattr(settings, "GT1000_MIDI_PORT", "GT-1000")


def channel() -> int:
    return int(getattr(settings, "GT1000_MIDI_CHANNEL", 1))


def patch_to_bank_program(index: int) -> tuple[int, int]:
    if not 0 <= index < MAX_REACHABLE:
        raise ValueError(f"patch index {index} is out of range (0-{MAX_REACHABLE - 1})")
    return divmod(index, PROGRAMS_PER_BANK)


def patch_messages(index: int, ch: int | None = None) -> list[mido.Message]:
    bank, program = patch_to_bank_program(index)
    c = (ch or channel()) - 1
    return [
        mido.Message("control_change", channel=c, control=0, value=bank),
        mido.Message("control_change", channel=c, control=32, value=0),
        mido.Message("program_change", channel=c, program=program),
    ]


class _Output:
    """Opens the GT-1000 output for each send and closes it again.

    Opening a CoreMIDI port costs about a millisecond. Keeping one open across
    Django's request threads proved unreliable (sends reported success but the
    unit never saw them), so each send gets a fresh port.
    """

    def __init__(self):
        self._lock = threading.Lock()

    def available_names(self) -> list[str]:
        return mido.get_output_names()

    def _find_name(self) -> str | None:
        wanted = port_name()
        names = self.available_names()
        if wanted in names:
            return wanted
        for n in names:  # e.g. "GT-1000" vs "GT-1000 DAW CTRL": prefer the plain one
            if n.startswith(wanted) and "DAW" not in n:
                return n
        return None

    def send(self, messages: list[mido.Message]) -> None:
        with self._lock:
            name = self._find_name()
            if name is None:
                raise ConnectionError(f'MIDI port "{port_name()}" not found. Is the GT-1000 connected over USB?')
            with mido.open_output(name) as port:
                for m in messages:
                    port.send(m)
            log.debug("sent %d messages to %s", len(messages), name)


output = _Output()


def send_patch(index: int) -> dict:
    """Send the patch-select sequence. Returns details for the UI."""
    bank, program = patch_to_bank_program(index)
    output.send(patch_messages(index))
    return {"bank": bank, "program": program, "channel": channel()}


# --- SysEx: reading patch names from the unit --------------------------------
#
# Roland "Request Data 1" (RQ1):
#   F0 41 dev 00 00 00 4F 11  aa bb cc dd  ss tt uu vv  sum F7
# Reply "Data Set 1" (DT1):
#   F0 41 dev 00 00 00 4F 12  aa bb cc dd  data...  sum F7
# dev = device id - 1 (unit shows 1..32, wire value is 00H..1FH).
# Checksum: low 7 bits of (128 - sum(address + size/data) mod 128).
#
# Addresses (all bytes are 7-bit):
#   10 00 00 00   temporary patch (what the unit is currently on)
#   20 00 00 00   user patch 1 ... 21 79 00 00 user patch 250
# The first 16 bytes of a patch are its name (ASCII 32-126).

ROLAND_ID = 0x41
MODEL_ID = (0x00, 0x00, 0x00, 0x4F)
CMD_RQ1 = 0x11
CMD_DT1 = 0x12
NAME_LEN = 16
TEMP_PATCH_ADDRESS = (0x10, 0x00, 0x00, 0x00)
USER_PATCH_BASE = 0x20
USER_PATCHES = 250


def device_id() -> int:
    return int(getattr(settings, "GT1000_DEVICE_ID", 17)) - 1


def roland_checksum(data) -> int:
    return (128 - (sum(data) % 128)) % 128


def user_patch_address(index: int) -> tuple[int, int, int, int]:
    if not 0 <= index < USER_PATCHES:
        raise ValueError(f"not a user patch: {index}")
    return (USER_PATCH_BASE + index // 128, index % 128, 0x00, 0x00)


def rq1_bytes(address, size: int) -> list[int]:
    """Full SysEx request including F0/F7, as a byte list."""
    size_bytes = (0x00, 0x00, (size >> 7) & 0x7F, size & 0x7F)
    body = list(address) + list(size_bytes)
    return [0xF0, ROLAND_ID, device_id(), *MODEL_ID, CMD_RQ1, *body, roland_checksum(body), 0xF7]


def parse_dt1(data: list[int]):
    """Return (address, payload) for a DT1 reply, or None if it isn't one.
    `data` is the SysEx body without F0/F7, as mido provides it."""
    if len(data) < 8 or data[0] != ROLAND_ID or tuple(data[2:6]) != MODEL_ID or data[6] != CMD_DT1:
        return None
    address = tuple(data[7:11])
    payload = data[11:-1]
    return address, payload


def decode_name(payload) -> str:
    return "".join(chr(b) if 32 <= b <= 126 else " " for b in payload[:NAME_LEN]).strip()


def _input_name() -> str | None:
    wanted = port_name()
    names = mido.get_input_names()
    if wanted in names:
        return wanted
    for n in names:
        if n.startswith(wanted) and "DAW" not in n:
            return n
    return None


def request_name(address, timeout: float = 1.0) -> str:
    """Send an RQ1 for the 16-byte name at `address` and wait for the DT1 reply."""
    in_name = _input_name()
    if in_name is None:
        raise ConnectionError(f'MIDI input "{port_name()}" not found. Is the GT-1000 connected over USB?')
    import time

    with mido.open_input(in_name) as inp:
        for _ in inp.iter_pending():  # drop anything stale
            pass
        output.send([mido.Message("sysex", data=rq1_bytes(address, NAME_LEN)[1:-1])])
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for msg in inp.iter_pending():
                if msg.type != "sysex":
                    continue
                parsed = parse_dt1(list(msg.data))
                if parsed and parsed[0] == tuple(address):
                    return decode_name(parsed[1])
            time.sleep(0.01)
    raise TimeoutError("GT-1000 did not answer the patch name request")


def read_patch_name(index: int) -> str:
    """Name of patch `index` as the unit displays it.

    User patches are read straight from memory. Preset patches aren't
    addressable that way, so the unit is switched to the patch and the
    temporary patch name is read instead.
    """
    if index < USER_PATCHES:
        return request_name(user_patch_address(index))
    send_patch(index)
    import time

    time.sleep(0.15)
    return request_name(TEMP_PATCH_ADDRESS)

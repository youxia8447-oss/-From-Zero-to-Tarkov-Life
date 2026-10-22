"""Replace the embedded icon and exit-sound assets in a PyInstaller archive.

Defaults: base/base_branded.exe -> build/base_custom.exe
Usage:    python patch_assets.py [source.exe] [output.exe]

Note: the archive slot named assets\\duckov_extract.wav holds the Itachi exit
sound in this build. assets\\subaru_clean.ico holds the Subaru icon.
"""
import struct
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "base" / "base_branded.exe"
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "build" / "base_custom.exe"
ICO = BASE / "assets" / "icons" / "first_icon.ico"
WAV = BASE / "assets" / "audio" / "itachi_exit_v2_35.wav"

COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"

REPLACEMENTS = {
    "assets\\subaru_clean.ico": ICO.read_bytes(),
    "assets\\duckov_extract.wav": WAV.read_bytes(),
}


def parse(buf):
    cp = buf.rfind(COOKIE)
    if cp < 0:
        raise RuntimeError("cookie not found")
    magic, pkg_len, toc_off, toc_len, pyver, pylib = struct.unpack(
        "!8sIIii64s", buf[cp:cp + 88]
    )
    tail = len(buf) - cp - 88
    overlay = len(buf) - (pkg_len + tail)
    toc = bytes(buf[overlay + toc_off:overlay + toc_off + toc_len])
    entries = {}
    pos = 0
    while pos < len(toc):
        es, = struct.unpack("!i", toc[pos:pos + 4])
        epos, cmprsd, uncmprsd, flag, typ, name = struct.unpack(
            "!IIIBc" + str(es - 18) + "s", toc[pos + 4:pos + es]
        )
        nm = name.decode("utf-8", "replace").rstrip("\0")
        entries[nm] = {
            "pos": epos, "cmprsd": cmprsd, "uncmprsd": uncmprsd,
            "flag": flag, "type": typ,
        }
        pos += es
    if pos != toc_len:
        raise RuntimeError("TOC parse mismatch")
    return overlay, entries, (magic, pkg_len, toc_off, toc_len, pyver)


orig = SRC.read_bytes()
size_before = len(orig)
buf = bytearray(orig)
overlay, entries, header = parse(orig)
print("overlay", overlay, "entries", len(entries))

for name, payload in REPLACEMENTS.items():
    e = entries[name]
    if e["flag"] != 1 or e["type"] != b"b":
        raise RuntimeError(f"{name}: not a compressed binary entry: {e}")
    old_comp = bytes(buf[overlay + e["pos"]:overlay + e["pos"] + e["cmprsd"]])
    if e["cmprsd"] == e["uncmprsd"]:
        raise RuntimeError(f"{name}: entry is stored, not compressed")
    old = zlib.decompress(old_comp)
    if len(old) != e["uncmprsd"]:
        raise RuntimeError(f"{name}: old size mismatch")
    for level in (9, 8, 7, 6, 5, 4, 3, 2, 1):
        new_comp = zlib.compress(payload, level)
        if len(new_comp) <= e["cmprsd"]:
            break
    print(name, "old", len(old), "new", len(payload),
          "comp", len(new_comp), "level", level, "slot", e["cmprsd"])
    if len(new_comp) > e["cmprsd"]:
        raise RuntimeError(f"{name}: does not fit slot")
    slot = new_comp + b"\0" * (e["cmprsd"] - len(new_comp))
    buf[overlay + e["pos"]:overlay + e["pos"] + e["cmprsd"]] = slot
    if zlib.decompress(bytes(buf[overlay + e["pos"]:overlay + e["pos"] + e["cmprsd"]])) != payload:
        raise RuntimeError(f"{name}: round-trip failed")

if len(buf) != size_before:
    raise RuntimeError("size changed")
overlay2, entries2, header2 = parse(buf)
if header2 != header or overlay2 != overlay:
    raise RuntimeError("archive header changed")
if entries2 != entries:
    raise RuntimeError("TOC changed")

DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_bytes(buf)
print("written", DST, len(buf))

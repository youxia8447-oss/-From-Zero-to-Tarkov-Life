"""Verify a rebuilt EXE against the generated modules and optional assets.

Usage:
    python scripts/validate_final.py [target.exe]
"""
import hashlib
import marshal
import struct
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXE = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "build" / "从零开始的塔科夫生活_V1.exe"
COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"

buf = EXE.read_bytes()
cp = buf.rfind(COOKIE)
if cp < 0:
    raise SystemExit("cookie not found")
magic, pkg_len, toc_off, toc_len, pyver, pylib = struct.unpack(
    "!8sIIii64s", buf[cp:cp + 88]
)
tail = len(buf) - cp - 88
overlay = len(buf) - (pkg_len + tail)
toc = buf[overlay + toc_off:overlay + toc_off + toc_len]

entries = {}
pos = 0
while pos < len(toc):
    es, = struct.unpack("!i", toc[pos:pos + 4])
    epos, cmprsd, uncmprsd, flag, typ, name = struct.unpack(
        "!IIIBc" + str(es - 18) + "s", toc[pos + 4:pos + es]
    )
    entries[name.decode("utf-8", "replace").rstrip("\0")] = {
        "pos": epos, "cmprsd": cmprsd, "uncmprsd": uncmprsd,
        "flag": flag, "type": typ,
    }
    pos += es


def asset(name):
    e = entries[name]
    raw = buf[overlay + e["pos"]:overlay + e["pos"] + e["cmprsd"]]
    return zlib.decompress(raw) if e["flag"] == 1 else raw


ico = BASE / "build" / "icons" / "first_icon.ico"
wav = BASE / "assets" / "audio" / "itachi_exit_v2_35.wav"
if ico.is_file():
    print("icon asset match", asset("assets\\subaru_clean.ico") == ico.read_bytes())
else:
    print("icon asset check skipped (build/icons/first_icon.ico not found)")
if wav.is_file():
    print("sound asset match", asset("assets\\duckov_extract.wav") == wav.read_bytes())
else:
    print("sound asset check skipped (assets/audio/itachi_exit_v2_35.wav not found)")

pyz_e = entries["PYZ.pyz"]
pyz_off = overlay + pyz_e["pos"]
pyz = buf[pyz_off:pyz_off + pyz_e["cmprsd"]]
pyz_toc_pos = struct.unpack(">i", pyz[8:12])[0]
pyz_toc = dict(marshal.loads(pyz[pyz_toc_pos:]))
for name, file in (("primary_ui", "ui_compact.marshal"),
                   ("sound_library", "sound_library.marshal"),
                   ("detector", "detector.marshal")):
    is_pkg, mpos, mlen = pyz_toc[name]
    blob = zlib.decompress(pyz[mpos:mpos + mlen])
    want = (BASE / file).read_bytes()
    print(name, "match", blob == want, "slot", mlen, "unc", len(blob))
    print(name, "sha", hashlib.sha256(blob).hexdigest()[:16])

print("size", len(buf), "sha256", hashlib.sha256(buf).hexdigest().upper())

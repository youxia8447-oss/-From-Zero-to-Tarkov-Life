"""Verify the rebuilt EXE against the project modules and embedded assets."""
import hashlib
import marshal
import struct
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXE = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "build" / "从零开始的塔科夫生活_V1.2.7.exe"
COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"

REQUIRED_ASSETS = {
    "assets\\bar.png",
    "assets\\bar_horizontal.png",
    "assets\\bar_vertical.png",
    "assets\\confirm_subtitle.png",
    "assets\\confirm_title.png",
    "assets\\extract_title.png",
    "assets\\extract_zero.png",
    "assets\\health.png",
    "assets\\label_shape.png",
    "assets\\menu_return.png",
    "assets\\menu_tabs.png",
    "assets\\pause_logo_left.png",
    "assets\\pause_logo_right.png",
    "assets\\settings_return.png",
    "assets\\settings_title.png",
    "assets\\subaru_clean.ico",
    "assets\\body_shape.npz",
    "assets\\timer_digits.npz",
    "assets\\enabled.wav",
    "assets\\disabled.wav",
    "assets\\return_by_death.wav",
    "assets\\return_by_death.mp3",
    "assets\\killer_queen.wav",
    "assets\\duckov_extract.wav",
}

REMOVED_ASSETS = {
    "assets\\bin.png",
    "assets\\emilia.ico",
    "assets\\emilia.png",
    "assets\\emilia_head.png",
    "assets\\mascot.png",
    "assets\\mascot_ui.png",
    "assets\\return_by_death.ico",
    "assets\\subaru_clean.png",
    "assets\\rewind.wav",
    "assets\\quest_completed.wav",
    "assets\\ui_v2\\manifest.json",
    "assets\\fonts\\Arvo-Bold.ttf",
    "assets\\fonts\\Arvo-Italic-4.ttf",
    "assets\\fonts\\Plix-Medium.otf",
    "assets\\fonts\\Plix-Regular.otf",
    "assets\\fonts\\Plix-SemiBold.otf",
}

buf = EXE.read_bytes()
cp = buf.rfind(COOKIE)
magic, pkg_len, toc_off, toc_len, pyver, pylib = struct.unpack("!8sIIii64s", buf[cp:cp + 88])
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


missing_required = sorted(REQUIRED_ASSETS - set(entries))
if missing_required:
    raise RuntimeError(f"missing required assets: {missing_required}")
still_removed = sorted(REMOVED_ASSETS & set(entries))
if still_removed:
    raise RuntimeError(f"unused assets still embedded: {still_removed}")
ui_v2 = sorted(name for name in entries if name.startswith("assets\\ui_v2\\"))
fonts = sorted(name for name in entries if name.startswith("assets\\fonts\\"))
if ui_v2 or fonts:
    raise RuntimeError(f"legacy ui_v2/fonts remain: {ui_v2 + fonts}")
if len(entries) != 1218:
    raise RuntimeError(f"unexpected archive entry count: {len(entries)}")
print("asset cleanup", len(REQUIRED_ASSETS), "required present;",
      len(REMOVED_ASSETS), "legacy absent; entries", len(entries))

ico_path = BASE / "build" / "icons" / "first_icon.ico"
wav_path = BASE / "assets" / "audio" / "itachi_exit_v2_35.wav"
if ico_path.exists():
    ico = ico_path.read_bytes()
    print("icon asset match", asset("assets\\subaru_clean.ico") == ico,
          len(asset("assets\\subaru_clean.ico")))
else:
    print("icon asset check skipped: build/icons/first_icon.ico not found")
if wav_path.exists():
    wav = wav_path.read_bytes()
    print("sound asset match", asset("assets\\duckov_extract.wav") == wav,
          len(asset("assets\\duckov_extract.wav")))
else:
    print("sound asset check skipped: assets/audio/itachi_exit_v2_35.wav not found")

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

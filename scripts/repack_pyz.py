"""Rebuild the embedded PYZ with new module blobs, growing the archive safely.

The original inject_modules.py only works while every module fits its old slot.
This script appends new blobs at the end of the PYZ data area, updates the PYZ
TOC, then rebuilds the outer CArchive TOC/cookie. PYZ is the last data entry,
so no other archive entry has to move.
"""
import hashlib
import marshal
import struct
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "base" / "base_branded.exe"
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "build" / "从零开始的塔科夫生活_V1.2.7.exe"
MODULES = {
    "primary_ui": BASE / "ui_compact.marshal",
    "sound_library": BASE / "sound_library.marshal",
    "detector": BASE / "detector.marshal",
}

try:
    from zopfli.zlib import compress as deflate
except ImportError:
    deflate = lambda data: zlib.compress(data, 9)

COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"


def parse_archive(buf):
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
    order = []
    pos = 0
    while pos < len(toc):
        es, = struct.unpack("!i", toc[pos:pos + 4])
        epos, cmprsd, uncmprsd, flag, typ, name = struct.unpack(
            "!IIIBc" + str(es - 18) + "s", toc[pos + 4:pos + es]
        )
        nm = name.decode("utf-8", "replace").rstrip("\0")
        entries[nm] = {
            "pos": epos, "cmprsd": cmprsd, "uncmprsd": uncmprsd,
            "flag": flag, "type": typ, "es": es,
        }
        order.append(nm)
        pos += es
    if pos != toc_len:
        raise RuntimeError("outer TOC parse mismatch")
    return overlay, entries, order, (magic, pkg_len, toc_off, toc_len, pyver, pylib)


orig = SRC.read_bytes()
overlay, entries, order, header = parse_archive(orig)
pyz_e = entries["PYZ.pyz"]
if pyz_e["flag"] != 0 or pyz_e["type"] != b"z" or pyz_e["cmprsd"] != pyz_e["uncmprsd"]:
    raise RuntimeError(f"unexpected PYZ entry: {pyz_e}")
pyz_off = overlay + pyz_e["pos"]
pyz_end = pyz_off + pyz_e["cmprsd"]
pyz = orig[pyz_off:pyz_end]
if pyz[:4] != b"PYZ\0":
    raise RuntimeError("PYZ header mismatch")
toc_pos = struct.unpack(">i", pyz[8:12])[0]
pyz_toc = dict(marshal.loads(pyz[toc_pos:]))

new_pyz = bytearray(pyz[:toc_pos])
for name, path in MODULES.items():
    if name not in pyz_toc:
        raise RuntimeError(f"{name} not in PYZ")
    blob = path.read_bytes()
    comp = deflate(blob)
    pos = len(new_pyz)
    pyz_toc[name] = (pyz_toc[name][0], pos, len(comp))
    new_pyz += comp
    print(name, "marshal", len(blob), "compressed", len(comp), "new pos", pos)

new_pyz_toc = marshal.dumps(pyz_toc)
new_pyz_toc_pos = len(new_pyz)
new_pyz += new_pyz_toc
struct.pack_into(">i", new_pyz, 8, new_pyz_toc_pos)
new_pyz_size = len(new_pyz)
print("PYZ", len(pyz), "->", new_pyz_size, "delta", new_pyz_size - len(pyz))

# Rebuild the outer TOC, changing only the PYZ size fields.
old_toc = bytearray(orig[overlay + header[2]:overlay + header[2] + header[3]])
new_toc = bytearray(old_toc)
pos = 0
found = False
while pos < len(old_toc):
    es, = struct.unpack("!i", old_toc[pos:pos + 4])
    name = old_toc[pos + 18:pos + es].decode("utf-8", "replace").rstrip("\0")
    if name == "PYZ.pyz":
        struct.pack_into("!II", new_toc, pos + 8, new_pyz_size, new_pyz_size)
        found = True
    pos += es
if not found:
    raise RuntimeError("PYZ record not found in outer TOC")

new_toc_off = pyz_e["pos"] + new_pyz_size
new_pkg_len = new_toc_off + len(new_toc) + 88
magic, _, _, _, pyver, pylib = header
cookie = struct.pack("!8sIIii64s", magic, new_pkg_len, new_toc_off, len(new_toc), pyver, pylib)
out = orig[:pyz_off] + bytes(new_pyz) + bytes(new_toc) + cookie
DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_bytes(out)
print("written", DST)
print("size", len(out), "delta", len(out) - len(orig))
print("sha256", hashlib.sha256(out).hexdigest().upper())

# Verify by parsing the output and comparing every new module blob.
check_overlay, check_entries, _, check_header = parse_archive(out)
check_pyz_e = check_entries["PYZ.pyz"]
check_pyz = out[check_overlay + check_pyz_e["pos"]:check_overlay + check_pyz_e["pos"] + check_pyz_e["cmprsd"]]
check_toc_pos = struct.unpack(">i", check_pyz[8:12])[0]
check_toc = dict(marshal.loads(check_pyz[check_toc_pos:]))
for name, path in MODULES.items():
    _, mpos, mlen = check_toc[name]
    if zlib.decompress(check_pyz[mpos:mpos + mlen]) != path.read_bytes():
        raise RuntimeError(f"{name} round-trip failed")
print("round-trip ok")

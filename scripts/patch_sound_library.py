"""Generate sound_library.marshal from the base EXE and rename the exit sounds.

The repository does not ship a compiled copy of the upstream sound module.
This script reads it from the base PyInstaller archive, replaces the preset
labels, and writes the marshal blob used by repack_pyz.py.

Usage:
    python scripts/patch_sound_library.py [source.exe] [output.marshal]
"""
import marshal
import struct
import sys
import types
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "base" / "base_branded.exe"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "sound_library.marshal"
COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"

REPLACE = {
    "原版死亡回归": "486回归音效",
    "鸭科夫仓库区撤离": "宇智波鼬 · 幻术",
}


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
        raise RuntimeError("outer TOC parse mismatch")
    return overlay, entries


def replace_value(value):
    if isinstance(value, str):
        new = REPLACE.get(value, value)
        return new, new != value
    if isinstance(value, tuple):
        items = []
        changed = False
        for item in value:
            new, hit = replace_value(item)
            items.append(new)
            changed = changed or hit
        return tuple(items), changed
    if isinstance(value, list):
        items = []
        changed = False
        for item in value:
            new, hit = replace_value(item)
            items.append(new)
            changed = changed or hit
        return items, changed
    if isinstance(value, frozenset):
        items = set()
        changed = False
        for item in value:
            new, hit = replace_value(item)
            items.add(new)
            changed = changed or hit
        return frozenset(items), changed
    if isinstance(value, dict):
        items = {}
        changed = False
        for key, item in value.items():
            new_key, hit_key = replace_value(key)
            new_item, hit_item = replace_value(item)
            items[new_key] = new_item
            changed = changed or hit_key or hit_item
        return items, changed
    return value, False


def patch_code(code):
    consts = []
    changed = False
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            new, hit = patch_code(value)
        else:
            new, hit = replace_value(value)
        consts.append(new)
        changed = changed or hit
    return code.replace(co_consts=tuple(consts)), changed


def all_strings(code):
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            yield from all_strings(value)
        elif isinstance(value, str):
            yield value


buf = SRC.read_bytes()
overlay, entries = parse_archive(buf)
pyz_e = entries["PYZ.pyz"]
pyz = bytes(buf[overlay + pyz_e["pos"]:overlay + pyz_e["pos"] + pyz_e["cmprsd"]])
if pyz[:4] != b"PYZ\0":
    raise RuntimeError("PYZ header mismatch")
toc_pos = struct.unpack(">i", pyz[8:12])[0]
pyz_toc = dict(marshal.loads(pyz[toc_pos:]))
is_pkg, pos, length = pyz_toc["sound_library"]
blob = zlib.decompress(pyz[pos:pos + length])
code = marshal.loads(blob)

patched, changed = patch_code(code)
new_blob = marshal.dumps(patched)
OUT.write_bytes(new_blob)

labels = set(all_strings(patched))
print("changed", changed)
print("has 486", "486回归音效" in labels)
print("has itachi", "宇智波鼬 · 幻术" in labels)
print("old labels left", sorted(set(REPLACE) & labels))
print("marshal", len(blob), "->", len(new_blob))
print("written", OUT)

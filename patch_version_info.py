"""Replace the PE version-info strings in place, without moving the overlay.

Usage: python patch_version_info.py [target.exe]
Default target: base/base_branded.exe (modified in place; make a backup first).
"""
import struct
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "base" / "base_branded.exe"
APP = "从零开始的塔科夫生活"
VERSION = "1.2.2.0"

data = bytearray(PATH.read_bytes())
pe = struct.unpack_from("<I", data, 0x3C)[0]
assert data[pe:pe + 4] == b"PE\0\0"
coff = pe + 4
num_sec, = struct.unpack_from("<H", data, coff + 2)
size_opt, = struct.unpack_from("<H", data, coff + 16)
opt = coff + 20
magic, = struct.unpack_from("<H", data, opt)
dd = opt + (112 if magic == 0x20B else 96)
res_rva, res_size = struct.unpack_from("<II", data, dd + 2 * 8)

sections = []
sec_off = opt + size_opt
for i in range(num_sec):
    o = sec_off + i * 40
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
    sections.append((vaddr, vsize, rawptr, rawsize))


def rva_to_off(rva):
    for vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    raise ValueError(hex(rva))


def find_version():
    def walk(rva, path=()):
        off = rva_to_off(rva)
        named, ids = struct.unpack_from("<HH", data, off + 12)
        for i in range(named + ids):
            eo = off + 16 + i * 8
            name_id, offset = struct.unpack_from("<II", data, eo)
            if name_id & 0x80000000:
                so = rva_to_off(res_rva + (name_id & 0x7FFFFFFF))
                ln, = struct.unpack_from("<H", data, so)
                nm = data[so + 2:so + 2 + ln * 2].decode("utf-16le")
            else:
                nm = name_id
            if offset & 0x80000000:
                r = walk(res_rva + (offset & 0x7FFFFFFF), path + (nm,))
                if r:
                    return r
            elif path + (nm,) == (16, 1, 0):
                do = rva_to_off(res_rva + offset)
                drva, dsize, cp, res = struct.unpack_from("<IIII", data, do)
                return do, drva, dsize, cp
    return walk(res_rva)


entry_off, ver_rva, ver_size, codepage = find_version()
ver_off = rva_to_off(ver_rva)
old = bytes(data[ver_off:ver_off + ver_size])
fixed = old[40:40 + 52]
var_info = old[ver_size - 68:ver_size]
assert len(fixed) == 52 and len(var_info) == 68


def wstr(s):
    return s.encode("utf-16le") + b"\x00\x00"


def block(key, value, value_len, wtype):
    raw = struct.pack("<HHH", 0, value_len, wtype) + wstr(key)
    raw += b"\x00" * ((4 - len(raw) % 4) % 4)
    raw += value
    raw += b"\x00" * ((4 - len(raw) % 4) % 4)
    return struct.pack("<H", len(raw)) + raw[2:]


def string_block(name, value):
    return block(name, wstr(value), len(value) + 1, 1)


strings = [
    string_block("CompanyName", ""),
    string_block("FileDescription", APP),
    string_block("FileVersion", VERSION),
    string_block("OriginalFilename", APP + ".exe"),
    string_block("ProductName", APP),
    string_block("ProductVersion", VERSION),
]
table_body = b"".join(strings)
table = block("080404B0", table_body, 0, 1)
sfi = block("StringFileInfo", table, 0, 1)
root_body = wstr("VS_VERSION_INFO")
root_body += b"\x00" * ((4 - (6 + len(root_body)) % 4) % 4)
root_body += fixed
root = block("VS_VERSION_INFO", root_body, 52, 0)
root = struct.pack("<HHH", 0, 52, 0) + wstr("VS_VERSION_INFO")
root += b"\x00" * ((4 - len(root) % 4) % 4)
root += fixed
root += sfi + var_info
root = struct.pack("<H", len(root)) + root[2:]
root += b"\x00" * ((4 - len(root) % 4) % 4)

print("old", len(old), "new", len(root), "slot", ver_size)
if len(root) > ver_size:
    raise SystemExit("new version block does not fit old slot")

data[ver_off:ver_off + ver_size] = root + b"\x00" * (ver_size - len(root))
struct.pack_into("<I", data, entry_off + 4, len(root))
PATH.write_bytes(data)
print("patched", PATH, "entry", hex(entry_off), "rva", hex(ver_rva), "new size", len(root))

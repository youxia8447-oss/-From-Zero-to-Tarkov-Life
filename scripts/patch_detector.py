"""Lower the embedded detector's first-arm HUD thresholds.

Reads the detector module from base/base_branded.exe, replaces the constants
inside start_hud_evidence, and writes detector.marshal for injection.

NOTE: the normalize_top replacement below is derived from the upstream
ID486-Tarkov-Assistant detector and is not covered by this repository's MIT
license. See NOTICE.md.
"""
import marshal
import struct
import sys
import types
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "base" / "base_branded.exe"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "detector.marshal"
COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"
SLOT = 15392  # compressed detector slot inside the PYZ

REPLACE = {0.48: 0.30, 0.45: 0.28, 0.22: 0.19}

NORMALIZE_SOURCE = '''
def normalize_top(self, frame, full_size=None):
    h,w=frame.shape[:2]
    full_w,full_h=full_size or (w,h)
    custom=getattr(self,'custom_size',None)
    if custom:
        if full_size is not None and (full_w,full_h)!=tuple(custom):
            raise ValueError('Configured resolution does not match game area')
        if w!=full_w:
            raise ValueError('Configured resolution does not match game area')
    elif w!=full_w or abs(full_w/full_h-1.6888888888888889)>0.1:
        raise ValueError('Only 16:10 game area supported by this HUD profile')
    strip_h=round(full_h*240/1080)
    if h<strip_h:raise ValueError('Capture strip is too short')
    top=cv2.resize(frame[:strip_h],(1920,240))
    if top.shape[2]==4:
        top=cv2.cvtColor(top,cv2.COLOR_BGRA2BGR)
    return top
'''


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
    return overlay, entries


def find_code(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            found = find_code(const, name)
            if found is not None:
                return found
    return None


def patch_consts(code):
    changed = []
    consts = []
    for value in code.co_consts:
        if isinstance(value, float) and value in REPLACE:
            consts.append(REPLACE[value])
            changed.append((value, REPLACE[value]))
        else:
            consts.append(value)
    if not changed:
        raise RuntimeError("no threshold constants replaced")
    return code.replace(co_consts=tuple(consts)), changed


def replace_code(code, name, new):
    consts = []
    hit = False
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            if value.co_name == name:
                consts.append(new)
                hit = True
            else:
                replaced, found = replace_code(value, name, new)
                consts.append(replaced)
                hit = hit or found
        else:
            consts.append(value)
    return code.replace(co_consts=tuple(consts)), hit


buf = SRC.read_bytes()
overlay, entries = parse_archive(buf)
pyz = entries["PYZ.pyz"]
pyz_bytes = bytes(buf[overlay + pyz["pos"]:overlay + pyz["pos"] + pyz["cmprsd"]])
toc_pos = struct.unpack(">i", pyz_bytes[8:12])[0]
toc = dict(marshal.loads(pyz_bytes[toc_pos:]))
is_pkg, pos, length = toc["detector"]
if length != SLOT:
    print("warning: detector slot is", length, "expected", SLOT)
blob = zlib.decompress(pyz_bytes[pos:pos + length])
code = marshal.loads(blob)
func = find_code(code, "start_hud_evidence")
if func is None:
    raise RuntimeError("start_hud_evidence not found")

patched, changed = patch_consts(func)
compiled = compile(NORMALIZE_SOURCE, "detector.py", "exec")
new_normalize = find_code(compiled, "normalize_top")
if new_normalize is None:
    raise RuntimeError("normalize_top source compile failed")

# Rebuild the module code object with both functions replaced in place.
module, hit_arm = replace_code(code, "start_hud_evidence", patched)
module, hit_norm = replace_code(module, "normalize_top", new_normalize)
if not (hit_arm and hit_norm):
    raise RuntimeError("detector functions not replaced")
new_blob = marshal.dumps(module)

# Execute the patched function in isolation (it only uses features.get).
namespace = {"__builtins__": {}}
check = types.FunctionType(patched, namespace)
sample = {
    "body_shape": 0.31623741483105067,
    "bar_frames": 0.2993544638156891,
    "label_shape": 0.6750180125236511,
    "combat_score": 0.42809425535922097,
}
low = {
    "body_shape": 0.33865421278274993,
    "bar_frames": 0.27085378766059875,
    "label_shape": 0.6215365529060364,
    "combat_score": 0.3760760128756303,
}
assert check(sample) is True
assert check(low) is True

from zopfli.zlib import compress as deflate
packed = deflate(new_blob)
print("replaced", changed)
print("marshal", len(blob), "->", len(new_blob))
print("zopfli", len(packed), "slot", length, "headroom", length - len(packed))
if len(packed) > length:
    raise SystemExit("patched detector does not fit its PYZ slot")
OUT.write_bytes(new_blob)
print("written", OUT)

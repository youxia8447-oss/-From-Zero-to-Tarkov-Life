"""Compile sound_library.py into a Python 3.11 marshal module for the PYZ."""
import marshal
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "sound_library.py"
OUT = BASE / "sound_library.marshal"

source = SRC.read_text(encoding="utf-8")
code = compile(source, "sound_library.py", "exec")
blob = marshal.dumps(code)
OUT.write_bytes(blob)

print("python", sys.version.split()[0])
print("marshal", len(blob))
print("zlib9", len(zlib.compress(blob, 9)))

try:
    from zopfli.zlib import compress as zopfli_compress

    print("zopfli", len(zopfli_compress(blob)), "· repack_pyz.py 会按实际大小重排 PYZ")
except ImportError:
    print("zopfli unavailable, repack_pyz.py will fall back to zlib")

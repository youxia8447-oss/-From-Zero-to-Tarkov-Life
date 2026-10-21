"""Compile ui_compact.py into a Python 3.11 marshal module for the embedded PYZ."""
import marshal
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "ui_compact.py"
OUT = BASE / "ui_compact.marshal"

source = SRC.read_text(encoding="utf-8")
code = compile(source, "primary_ui.py", "exec")
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

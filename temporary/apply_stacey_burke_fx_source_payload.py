from __future__ import annotations

import base64
import hashlib
import json
import zlib
from pathlib import Path

EXPECTED_PAYLOAD_SHA256 = "baef5505697bf626a35a764978cbf282634705a5466255d4efdf293ab5716493"
parts = sorted(Path("temporary").glob("sb_payload_*.b64"))
if len(parts) != 6:
    raise RuntimeError(f"expected six payload parts, found {len(parts)}")
encoded = "".join(path.read_text(encoding="utf-8").strip() for path in parts)
payload = zlib.decompress(base64.b64decode(encoded))
observed = hashlib.sha256(payload).hexdigest()
if observed != EXPECTED_PAYLOAD_SHA256:
    raise RuntimeError(f"payload checksum mismatch: {observed}")
files = json.loads(payload.decode())
for relative, content in files.items():
    path = Path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
for path in parts:
    path.unlink()
Path(__file__).unlink()

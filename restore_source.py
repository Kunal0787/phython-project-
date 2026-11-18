#!/usr/bin/env python3
"""Reconstruct pdf_layout_engine.py from the compressed source parts."""

from __future__ import annotations

import base64
import bz2
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "source"
PART_NAMES = [f"pdf_layout_engine.bz2.b64.part{i:02d}" for i in range(1, 7)]
EXPECTED_PART_LENGTHS = [8000, 8000, 8000, 8000, 8000, 6768]
EXPECTED_SOURCE_BYTES = 204036
EXPECTED_SHA256 = "683805486348f65e17ac91d99f02c7ae874921a2246eaf18b078d7f8001292df"


def main() -> int:
    try:
        chunks = []
        for name, expected_length in zip(PART_NAMES, EXPECTED_PART_LENGTHS):
            path = SOURCE_DIR / name
            if not path.is_file():
                raise FileNotFoundError(f"Missing source part: {path}")
            chunk = path.read_text(encoding="ascii").strip()
            if len(chunk) != expected_length:
                raise ValueError(
                    f"{name} has {len(chunk)} characters; expected {expected_length}."
                )
            chunks.append(chunk)

        compressed = base64.b64decode("".join(chunks), validate=True)
        source = bz2.decompress(compressed)
        digest = hashlib.sha256(source).hexdigest()
        if len(source) != EXPECTED_SOURCE_BYTES or digest != EXPECTED_SHA256:
            raise ValueError(
                "Reconstructed source validation failed "
                f"(bytes={len(source)}, sha256={digest})."
            )

        output = ROOT / "pdf_layout_engine.py"
        output.write_bytes(source)
        print(f"Restored {output.name} ({len(source):,} bytes).")
        print(f"SHA-256 verified: {digest}")
        return 0
    except (OSError, ValueError, EOFError, OSError) as error:
        print(f"Could not restore the application source: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

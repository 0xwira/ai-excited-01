#!/usr/bin/env python3
"""Validate the bundled image and copy it to the make.fun output directory."""

import hashlib
import os
import shutil
import sys
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def is_complete_image(path: Path) -> bool:
    with path.open("rb") as image:
        head = image.read(8)
        if head == PNG_SIGNATURE:
            data = image.read()
            return len(data) >= 12 and data[-8:-4] == b"IEND" and data[-4:] == b"\xaeB`\x82"
        if head[:2] == b"\xff\xd8":
            image.seek(-2, os.SEEK_END)
            return image.read(2) == b"\xff\xd9"
    return False


def digest_and_size(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def main() -> None:
    source = Path(__file__).resolve().with_name("entry.png")
    if not source.is_file():
        fail(f"missing image: {source}")
    try:
        if not is_complete_image(source):
            fail("entry.png is not a complete PNG or JPEG")
        source_size, source_digest = digest_and_size(source)
        output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / "entry.png"
        with source.open("rb") as source_stream, target.open("wb") as target_stream:
            shutil.copyfileobj(source_stream, target_stream, length=1024 * 1024)
        target_size, target_digest = digest_and_size(target)
        if (target_size, target_digest) != (source_size, source_digest):
            fail("copied image failed size or SHA-256 verification")
        print(f"source sha256: {source_digest}")
        print(f"output sha256: {target_digest}")
    except OSError as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()

"""Validate entry.png, copy it in chunks, and verify its size and SHA-256 hash."""

import hashlib
import os
import sys


CHUNK_SIZE = 1024 * 1024


def validate_image(path):
    with open(path, "rb") as source:
        prefix = source.read(8)
        source.seek(0, os.SEEK_END)
        size = source.tell()
        if prefix == b"\x89PNG\r\n\x1a\n":
            if size < 12:
                raise ValueError("source is not a complete PNG image")
            source.seek(-12, os.SEEK_END)
            tail = source.read(12)
            if tail != b"\x00\x00\x00\x00IEND\xaeB\x60\x82":
                raise ValueError("source is not a complete PNG image")
            return
        source.seek(0)
        if source.read(2) == b"\xff\xd8":
            if size < 2:
                raise ValueError("source is not a complete JPEG image")
            source.seek(-2, os.SEEK_END)
            if source.read(2) != b"\xff\xd9":
                raise ValueError("source is not a complete JPEG image")
            return
    raise ValueError("source is not a supported complete PNG or JPEG image")


def copy_entry(source, destination):
    with open(source, "rb") as src, open(destination, "wb") as dst:
        while True:
            chunk = src.read(CHUNK_SIZE)
            if not chunk:
                break
            dst.write(chunk)
    source_hash = hashlib.sha256()
    destination_hash = hashlib.sha256()
    with open(source, "rb") as src, open(destination, "rb") as dst:
        while True:
            src_chunk = src.read(CHUNK_SIZE)
            dst_chunk = dst.read(CHUNK_SIZE)
            if not src_chunk and not dst_chunk:
                break
            source_hash.update(src_chunk)
            destination_hash.update(dst_chunk)
    if (os.path.getsize(source) != os.path.getsize(destination)
            or source_hash.digest() != destination_hash.digest()):
        raise ValueError("copy verification failed: output differs from source")


def main():
    source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    destination = os.path.join(output_dir, "entry.png")
    try:
        validate_image(source)
        os.makedirs(output_dir, exist_ok=True)
        copy_entry(source, destination)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

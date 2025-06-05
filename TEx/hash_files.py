"""Utility to compute file hashes for verification purposes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Dict

_EXCLUDE_DIRS = {'.git', '.venv', '__pycache__'}


def _hash_file(path: str, algorithm: str) -> str:
    """Return the file hash using the selected algorithm."""
    if algorithm.lower() == 'md5':
        hasher = hashlib.md5()
    else:
        hasher = hashlib.sha256()

    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def hash_directory(directory: str, algorithm: str = 'sha256') -> Dict[str, str]:
    """Return a mapping from relative file paths to hashes."""
    hashes: Dict[str, str] = {}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, directory)
            hashes[rel_path] = _hash_file(file_path, algorithm)
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser(description='Compute and store file hashes.')
    parser.add_argument('-d', '--directory', default='.', help='Directory to scan')
    parser.add_argument(
        '-a', '--algorithm', choices=['md5', 'sha256'], default='sha256',
        help='Hash algorithm to use'
    )
    parser.add_argument(
        '-o', '--output', default='file_hashes.json',
        help='Output file to store the hashes'
    )
    args = parser.parse_args()

    base_dir = os.path.abspath(args.directory)
    hashes = hash_directory(base_dir, args.algorithm)

    with open(args.output, 'w') as f:
        json.dump(hashes, f, indent=2)

    print(f'Wrote {len(hashes)} hashes to {args.output}')


if __name__ == '__main__':
    main()

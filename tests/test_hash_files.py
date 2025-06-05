import os
import tempfile
from hashlib import sha256

from TEx.hash_files import hash_directory


def test_hash_directory_creates_hashes(tmp_path):
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"

    file1.write_text("hello")
    file2.write_text("world")

    hashes = hash_directory(str(tmp_path), "sha256")

    expected1 = sha256(b"hello").hexdigest()
    expected2 = sha256(b"world").hexdigest()

    rel1 = os.path.relpath(file1, tmp_path)
    rel2 = os.path.relpath(file2, tmp_path)

    assert hashes[rel1] == expected1
    assert hashes[rel2] == expected2

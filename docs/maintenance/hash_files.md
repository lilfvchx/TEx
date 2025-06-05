# Maintenance - File Hashing

Telegram Explorer includes a helper task to compute the SHA256 (or MD5) hash of every file in a directory. The generated table can be used to detect duplicates, validate integrity in the future and create unique identifiers for traceability.

## Usage

```bash
python3 -m TEx.hash_files --directory PATH_TO_SCAN --algorithm sha256 --output file_hashes.json
```

The command scans the directory recursively, ignoring common virtual environment and Git folders, and stores the hashes in the chosen output file.

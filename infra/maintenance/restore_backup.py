"""Decrypt and validate into an isolated directory; never overwrite live data."""
import argparse
import hashlib
import io
import json
import os
import sqlite3
import tarfile
from pathlib import Path

from backup_crypto import decrypt


def restore(backup: Path, private: Path, password: Path, destination: Path):
    os.umask(0o077)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Restore destination must be empty')
    plaintext = decrypt(backup.read_bytes(), private.read_bytes(), password.read_bytes().strip())
    with tarfile.open(fileobj=io.BytesIO(plaintext), mode='r:gz') as tar:
        member = tar.getmember('manifest.json')
        if not member.isfile() or member.size > 65536:
            raise ValueError('Invalid manifest size')
        manifest = json.load(tar.extractfile(member))
        if manifest.get('version') != 1:
            raise ValueError('Unsupported archive version')
        verified = {}
        total = 0
        if len(manifest['sha256']) > 1000:
            raise ValueError('Too many archive entries')
        for name, expected in manifest['sha256'].items():
            parts = Path(name).parts
            if Path(name).is_absolute() or '..' in parts or not parts:
                raise ValueError('Unsafe archive path')
            member = tar.getmember(name)
            total += member.size
            if total > 256 * 1024 * 1024:
                raise ValueError('Archive exceeds restore limit')
            if not member.isfile() or member.size > 256 * 1024 * 1024:
                raise ValueError('Unexpected archive member')
            content = tar.extractfile(member).read()
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError('Archive checksum mismatch')
            verified[name] = content
    # Only create output after all authenticated payloads and checksums pass.
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in verified.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        target.chmod(0o600)
    with sqlite3.connect(destination / 'data/accounts.sqlite3') as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Restored database integrity failed')
        for table in ('users', 'tokens', 'sessions'):
            if db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] != manifest['counts'][table]:
                raise ValueError('Restored row counts differ from snapshot')
    print('Isolated restore passed: authenticated encryption, file hashes, SQLite and row counts')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--private-key', type=Path, required=True)
    parser.add_argument('--password-file', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    restore(args.backup, args.private_key, args.password_file, args.destination)

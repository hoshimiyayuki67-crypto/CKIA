#!/usr/bin/env python3
"""Consistent SQLite snapshot, encrypted configuration archive and bounded retention."""
import fcntl
import grp
import hashlib
import io
import json
import os
import re
import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from backup_crypto import encrypt

ROOT = Path('/var/backups/ckia')
SNAPSHOT = '/app/data/.maintenance-snapshot.sqlite3'
CONTAINER = 'campus-assistant-api-1'


def docker(*args, **kwargs):
    subprocess.run(['docker', *args], check=True, timeout=120, capture_output=True, **kwargs)


def main():
    os.umask(0o077)
    ROOT.mkdir(parents=True, exist_ok=True)
    gid = grp.getgrnam('ckia-backup').gr_gid
    os.chown(ROOT, 0, gid)
    ROOT.chmod(0o750)
    with (ROOT / '.maintenance.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(prefix='.snapshot-', dir=ROOT) as directory:
            stage = Path(directory)
            snapshot = stage / 'accounts.sqlite3'
            try:
                docker('exec', CONTAINER, 'python', '-c',
                    'import sqlite3,os; '
                    's=sqlite3.connect("file:/app/data/accounts.sqlite3?mode=ro",uri=True); '
                    f'd=sqlite3.connect("{SNAPSHOT}"); '
                    's.backup(d,pages=256,sleep=0.05); d.close(); s.close(); '
                    f'os.chmod("{SNAPSHOT}",0o600)')
                docker('cp', f'{CONTAINER}:{SNAPSHOT}', str(snapshot))
                snapshot.chmod(0o600)
                with sqlite3.connect(snapshot) as db:
                    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise RuntimeError('Snapshot integrity check failed')
                    counts = {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                              for table in ('users', 'tokens', 'sessions')}
                timestamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
                archive = stage / 'payload.tar.gz'
                manifest = {'version': 1, 'created_at': timestamp, 'counts': counts, 'sha256': {}}
                with tarfile.open(archive, 'w:gz', dereference=True) as tar:
                    inputs = [(snapshot, 'data/accounts.sqlite3'),
                        (Path('/opt/campus-assistant/infra/.env'), 'configuration/deployment.env')]
                    for folder in ('live', 'archive', 'renewal'):
                        certs = Path('/etc/letsencrypt') / folder
                        if certs.is_dir():
                            for source in certs.rglob('*'):
                                if source.is_file():
                                    inputs.append((source, 'letsencrypt/' + str(source.relative_to('/etc/letsencrypt'))))
                    for source, name in [(Path('/root/.secrets/ckia-cloudflare.ini'), 'configuration/cloudflare.ini')]:
                        if source.is_file():
                            inputs.append((source, name))
                    for source, name in inputs:
                        content = source.read_bytes()
                        manifest['sha256'][name] = hashlib.sha256(content).hexdigest()
                        info = tarfile.TarInfo(name)
                        info.size, info.mode = len(content), 0o600
                        tar.addfile(info, io.BytesIO(content))
                    content = json.dumps(manifest).encode()
                    info = tarfile.TarInfo('manifest.json')
                    info.size, info.mode = len(content), 0o600
                    tar.addfile(info, io.BytesIO(content))
                ciphertext = encrypt(archive.read_bytes(), Path('/etc/ckia/backup-recipient.pem').read_bytes())
                destination = ROOT / f'ckia-{timestamp}.enc'
                temp = ROOT / '.encrypted.tmp'
                temp.write_bytes(ciphertext)
                os.chown(temp, 0, gid)
                temp.chmod(0o640)
                temp.replace(destination)
                link = ROOT / '.latest.tmp'
                link.unlink(missing_ok=True)
                link.symlink_to(destination.name)
                link.replace(ROOT / 'latest.enc')
                candidates = sorted(p for p in ROOT.glob('ckia-*.enc')
                    if re.fullmatch(r'ckia-\d{8}T\d{6}Z\.enc', p.name))
                for old in candidates[:-7]:
                    if old.resolve().parent != ROOT.resolve():
                        raise RuntimeError('Unsafe retention path')
                    old.unlink()
                print('Encrypted backup created and SQLite integrity verified:', destination.name)
            finally:
                docker('exec', CONTAINER, 'python', '-c',
                       f'from pathlib import Path; Path("{SNAPSHOT}").unlink(missing_ok=True)')


if __name__ == '__main__':
    main()

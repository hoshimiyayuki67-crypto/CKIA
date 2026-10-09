#!/usr/bin/env python3
"""SSH forced command: export only the current, fresh encrypted backup."""
import os
import re
import sys
import time
from pathlib import Path

root = Path('/var/backups/ckia').resolve()
source = (root / 'latest.enc').resolve(strict=True)
if (source.parent != root or not re.fullmatch(r'ckia-\d{8}T\d{6}Z\.enc', source.name)
        or time.time() - source.stat().st_mtime > 30 * 3600
        or source.stat().st_size > 256 * 1024 * 1024 + 16384):
    raise SystemExit('No valid fresh encrypted backup available')
# Ignore SSH_ORIGINAL_COMMAND entirely: this key never obtains a shell or arbitrary files.
os.environ.pop('SSH_ORIGINAL_COMMAND', None)
with source.open('rb') as file:
    while chunk := file.read(65536):
        sys.stdout.buffer.write(chunk)

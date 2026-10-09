import re
import sys
from pathlib import Path

output = Path(sys.argv[1]).read_text()
digests = re.findall(r'Signer #\d+ certificate SHA-256 digest: ([a-fA-F0-9]+)', output)
expected = Path(sys.argv[2]).read_text().strip().lower()
if len(digests) != 1 or digests[0].lower() != expected:
    raise SystemExit('APK signature does not match pinned release certificate')
print('APK uses the pinned fixed release certificate')

import re
import sys
from pathlib import Path

def verify(output, expected):
    digests = re.findall(
        r'^(?:Signer (?:#\d+|\([^\n]+\))|V\d(?:\.\d+)? Signer:) certificate SHA-256 digest: ([a-fA-F0-9]{64})\s*$',
        output, re.M)
    counts = re.findall(r'^Number of signers: (\d+)\s*$', output, re.M)
    if counts != ['1'] or {value.lower() for value in digests} != {expected.strip().lower()}:
        raise ValueError('APK signature does not match pinned release certificate')


if __name__ == '__main__':
    try:
        verify(Path(sys.argv[1]).read_text(), Path(sys.argv[2]).read_text())
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print('APK uses the pinned fixed release certificate')

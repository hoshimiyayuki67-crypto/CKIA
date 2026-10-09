"""Decode a task-created Actions secret and pin its public signing certificate."""
import base64
import hashlib
import json
import os
import re
import ssl
import subprocess
from pathlib import Path


def main():
    raw = os.environ.get('CKIA_CI_BUNDLE', '')
    if not raw:
        raise SystemExit('CKIA_CI_BUNDLE is required. Release builds never fall back to debug signing.')
    try:
        bundle = json.loads(raw)['signing']
        key = base64.b64decode(bundle['keystore_base64'], validate=True)
        password, alias = bundle['password'], bundle['alias']
        if not password or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', alias):
            raise ValueError('invalid signing configuration')
    except (ValueError, KeyError, TypeError):
        raise SystemExit('Invalid signing bundle') from None
    target = Path(os.environ['RUNNER_TEMP']) / 'campus-release.p12'
    target.write_bytes(key)
    target.chmod(0o600)
    result = subprocess.run(['openssl', 'pkcs12', '-in', str(target), '-clcerts', '-nokeys',
        '-passin', 'env:CAMPUS_TEMP_SIGNING_PASSWORD'], capture_output=True, text=True,
        env={**os.environ, 'CAMPUS_TEMP_SIGNING_PASSWORD': password})
    match = re.search(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', result.stdout, re.S)
    if result.returncode != 0 or not match:
        raise SystemExit('Signing keystore could not be verified')
    fingerprint = hashlib.sha256(ssl.PEM_cert_to_DER_cert(match.group())).hexdigest()
    pinned = Path('infra/keys/android-signing.sha256').read_text().strip()
    if fingerprint != pinned:
        raise SystemExit('Signing certificate differs from pinned release identity')
    print('::add-mask::' + password)
    with Path(os.environ['GITHUB_ENV']).open('a') as output:
        for name, value in {'CAMPUS_RELEASE_KEYSTORE': str(target),
            'CAMPUS_RELEASE_STORE_PASSWORD': password, 'CAMPUS_RELEASE_KEY_PASSWORD': password,
            'CAMPUS_RELEASE_ALIAS': alias}.items():
            if '\n' in value or '\r' in value:
                raise SystemExit('Multiline signing values are not supported')
            output.write(f'{name}={value}\n')
    print('Verified pinned release certificate SHA256:', fingerprint)


if __name__ == '__main__':
    main()

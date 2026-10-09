"""Create persistent Android/backup keys once. Private output must never enter Git."""
import base64
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'artifacts/ops-private'
PUBLIC = ROOT / 'infra/keys'


def main():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    if (PUBLIC / 'android-signing.sha256').exists() or (PRIVATE / 'ci-bundle.json').exists():
        raise SystemExit('Keys already exist. Restore them; never silently rotate release signing.')
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Campus Assistant Release')])
    now = datetime.now(UTC)
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=10950))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256()))
    password = secrets.token_urlsafe(48)
    archive = pkcs12.serialize_key_and_certificates(b'campus-release', key, certificate, None,
        serialization.BestAvailableEncryption(password.encode()))
    fingerprint = certificate.fingerprint(hashes.SHA256()).hex()
    (PUBLIC / 'android-signing.pem').write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    (PUBLIC / 'android-signing.sha256').write_text(fingerprint + '\n')
    (PRIVATE / 'campus-release.p12').write_bytes(archive)
    recovery = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    recovery_password = secrets.token_urlsafe(48)
    (PRIVATE / 'backup-recovery.pem').write_bytes(recovery.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(recovery_password.encode())))
    (PRIVATE / 'recovery-password.txt').write_text(recovery_password)
    (PUBLIC / 'backup-recipient.pem').write_bytes(recovery.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    ssh = ed25519.Ed25519PrivateKey.generate()
    private_ssh = ssh.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.OpenSSH,
        serialization.NoEncryption()).decode()
    (PUBLIC / 'backup-ssh.pub').write_bytes(ssh.public_key().public_bytes(
        serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH) + b' ckia-backup-export\n')
    bundle = {'signing': {'keystore_base64': base64.b64encode(archive).decode(),
        'password': password, 'alias': 'campus-release'},
        'backup': {'ssh_private_key': private_ssh, 'host': 'v4.yukifn.xyz', 'port': 7022,
                   'user': 'ckia-backup', 'known_hosts': ''}}
    (PRIVATE / 'ci-bundle.json').write_text(json.dumps(bundle, indent=2), encoding='utf-8')
    for path in PRIVATE.iterdir():
        path.chmod(0o600)
    print('Created private signing/recovery files in artifacts/ops-private; do not upload as artifacts.')
    print('Public Android certificate SHA256:', fingerprint)


if __name__ == '__main__':
    main()

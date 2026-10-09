"""Authenticated envelope encryption. The server holds only the public recipient key."""
import base64
import json
import secrets
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b'CKIABK1\n'
LIMIT = 256 * 1024 * 1024


def encrypt(data: bytes, recipient: bytes) -> bytes:
    if len(data) > LIMIT:
        raise ValueError('Backup exceeds size limit')
    public = serialization.load_pem_public_key(recipient)
    key, nonce = AESGCM.generate_key(bit_length=256), secrets.token_bytes(12)
    wrapped = public.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
        algorithm=hashes.SHA256(), label=None))
    header = json.dumps({'version': 1, 'wrapped_key': base64.b64encode(wrapped).decode(),
        'nonce': base64.b64encode(nonce).decode()}, separators=(',', ':')).encode()
    ciphertext = AESGCM(key).encrypt(nonce, data, header)
    return MAGIC + struct.pack('!I', len(header)) + header + ciphertext


def decrypt(data: bytes, private: bytes, password: bytes) -> bytes:
    if not data.startswith(MAGIC) or len(data) > LIMIT + 16384:
        raise ValueError('Invalid backup envelope')
    start = len(MAGIC) + 4
    length = struct.unpack('!I', data[len(MAGIC):start])[0]
    if length > 16384 or len(data) < start + length + 16:
        raise ValueError('Invalid backup header')
    header = data[start:start + length]
    metadata = json.loads(header)
    if metadata.get('version') != 1:
        raise ValueError('Unsupported backup version')
    key = serialization.load_pem_private_key(private, password)
    symmetric = key.decrypt(base64.b64decode(metadata['wrapped_key'], validate=True),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    return AESGCM(symmetric).decrypt(base64.b64decode(metadata['nonce'], validate=True),
        data[start + length:], header)

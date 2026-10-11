"""vault.py - Cryptographic core of the Secure Password Manager.

* Key derivation : PBKDF2-HMAC-SHA256 (600,000 iterations, 16-byte random salt)
* Encryption     : AES-256-GCM (authenticated encryption, 12-byte random nonce)
* Storage        : single file `vault.dat` (JSON: salt, nonce, ciphertext - all base64)
"""
import base64
import json
import math
import os
import secrets
import string
import time
import uuid

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "letmein", "admin",
    "welcome", "iloveyou", "password1", "111111", "123123", "dragon", "monkey",
}


class VaultError(Exception):
    """Raised for wrong master password or corrupted vault."""


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _b64d(text: str) -> bytes:
    return base64.b64decode(text.encode())


def derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=ITERATIONS)
    return kdf.derive(master_password.encode("utf-8"))


class Vault:
    def __init__(self, path="vault.dat"):
        self.path = path
        self.key = None
        self.salt = None
        self.entries = []

    # ------------------------------------------------------------ lifecycle
    def exists(self) -> bool:
        return os.path.exists(self.path)

    def create(self, master_password: str):
        if self.exists():
            raise VaultError("Vault already exists.")
        self.salt = os.urandom(16)
        self.key = derive_key(master_password, self.salt)
        self.entries = []
        self.save()

    def unlock(self, master_password: str):
        with open(self.path, "r") as fh:
            blob = json.load(fh)
        self.salt = _b64d(blob["salt"])
        key = derive_key(master_password, self.salt)
        try:
            plain = AESGCM(key).decrypt(_b64d(blob["nonce"]),
                                        _b64d(blob["data"]), None)
        except InvalidTag:
            raise VaultError("Incorrect master password.")
        self.key = key
        self.entries = json.loads(plain.decode("utf-8"))

    def lock(self):
        self.key = None
        self.entries = []

    def save(self):
        nonce = os.urandom(12)
        data = AESGCM(self.key).encrypt(
            nonce, json.dumps(self.entries).encode("utf-8"), None)
        with open(self.path, "w") as fh:
            json.dump({"salt": _b64e(self.salt), "nonce": _b64e(nonce),
                       "data": _b64e(data)}, fh)

    # ----------------------------------------------------------------- CRUD
    def add(self, site, username, password, notes=""):
        entry = {"id": uuid.uuid4().hex[:8], "site": site, "username": username,
                 "password": password, "notes": notes,
                 "updated": time.strftime("%Y-%m-%d %H:%M")}
        self.entries.append(entry)
        self.save()
        return entry

    def get(self, entry_id):
        return next((e for e in self.entries if e["id"] == entry_id), None)

    def update(self, entry_id, **fields):
        entry = self.get(entry_id)
        if not entry:
            raise VaultError("Entry not found.")
        entry.update(fields)
        entry["updated"] = time.strftime("%Y-%m-%d %H:%M")
        self.save()

    def delete(self, entry_id):
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        self.save()

    def search(self, term=""):
        term = term.lower()
        return sorted((e for e in self.entries
                       if term in e["site"].lower() or term in e["username"].lower()),
                      key=lambda e: e["site"].lower())


# ------------------------------------------------------------------ helpers
def generate_password(length=16, upper=True, digits=True, symbols=True):
    """Cryptographically secure random password (uses `secrets`)."""
    pools = [string.ascii_lowercase]
    if upper:
        pools.append(string.ascii_uppercase)
    if digits:
        pools.append(string.digits)
    if symbols:
        pools.append("!@#$%^&*()-_=+[]{};:,.?")
    length = max(length, len(pools))
    chars = [secrets.choice(p) for p in pools]          # one from each pool
    allchars = "".join(pools)
    chars += [secrets.choice(allchars) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def check_strength(password: str):
    """Return (score 0-4, label, entropy bits, tips)."""
    tips, pool = [], 0
    if any(c.islower() for c in password): pool += 26
    else: tips.append("add lowercase letters")
    if any(c.isupper() for c in password): pool += 26
    else: tips.append("add uppercase letters")
    if any(c.isdigit() for c in password): pool += 10
    else: tips.append("add digits")
    if any(not c.isalnum() for c in password): pool += 32
    else: tips.append("add symbols")
    if len(password) < 12:
        tips.append("use at least 12 characters")
    entropy = len(password) * math.log2(pool) if pool else 0
    if password.lower() in COMMON_PASSWORDS:
        entropy, tips = 0, ["this is a very common password"]
    score = 0 if entropy < 28 else 1 if entropy < 40 else 2 if entropy < 60 \
        else 3 if entropy < 80 else 4
    label = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"][score]
    return score, label, round(entropy, 1), tips

#!/usr/bin/env python3
"""Optional cryptographic authorship: ed25519 signatures over chain entries.

The hash chain (chain.py) proves the audit log was not edited after the fact. It
does NOT prove *who* wrote an entry — identity is still a declared string. This
module closes that gap for deployments that need it: each actor holds an ed25519
private key; the entry's `sig` signs its `entry_hash`; the validator verifies it
against the actor's registered public key. A forged event then needs the actor's
private key, not just their name — real non-repudiation across trust domains.

Signing is OPT-IN and pulls the ONE optional dependency (`cryptography`):

    pip install "procheiron[crypto]"

The governance core stays zero-dependency: without keys configured, deployments
run exactly as before (honor-system + hash chain). This module raises a clear,
actionable error if signing/verification is requested without `cryptography`
installed — it never silently degrades a trust check to a pass.

Keys are raw 32-byte ed25519, hex-encoded. Public keys register per-actor in the
profile (`known_actor_keys`); private keys stay with the actor (never in the repo;
0600 on disk). This is a reference implementation — production key custody
(HSM/KMS, separate OS users, Sigstore keyless) is a deployment concern.
"""
from __future__ import annotations

from typing import Optional, Tuple

_IMPORT_ERROR: Optional[Exception] = None
try:  # optional dependency — never required for the governance core
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    _HAVE_CRYPTO = True
except Exception as exc:  # noqa: BLE001 — record why, surface on use
    _HAVE_CRYPTO = False
    _IMPORT_ERROR = exc


class SigningUnavailable(RuntimeError):
    """Raised when a signing/verification op is requested without `cryptography`."""


def available() -> bool:
    """True if cryptographic signing/verification can run in this environment."""
    return _HAVE_CRYPTO


def _require() -> None:
    if not _HAVE_CRYPTO:
        raise SigningUnavailable(
            "cryptographic signing requires the optional 'cryptography' package. "
            "Install it with:  pip install \"procheiron[crypto]\"  "
            f"(import failed: {_IMPORT_ERROR})"
        )


def generate_keypair() -> Tuple[str, str]:
    """Return (private_key_hex, public_key_hex) — raw 32-byte ed25519, hex-encoded.
    Store the private hex with 0600 perms, register the public hex per actor."""
    _require()
    from cryptography.hazmat.primitives import serialization

    priv = Ed25519PrivateKey.generate()
    priv_raw = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_raw = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_raw.hex(), pub_raw.hex()


def public_key_of(private_key_hex: str) -> str:
    """Derive the public key hex from a private key hex."""
    _require()
    from cryptography.hazmat.primitives import serialization

    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    return priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def sign(private_key_hex: str, message: str) -> str:
    """Sign a UTF-8 message (an entry_hash / content_hash) → signature hex."""
    _require()
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    return priv.sign(message.encode("utf-8")).hex()


def verify(public_key_hex: str, message: str, sig_hex: str) -> bool:
    """Verify a signature. Returns True/False; never raises on a bad signature.
    Raises SigningUnavailable only if `cryptography` is missing (a verification
    that cannot run must NOT be silently treated as valid)."""
    _require()
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        pub.verify(bytes.fromhex(sig_hex), message.encode("utf-8"))
        return True
    except InvalidSignature:
        return False
    except Exception:  # noqa: BLE001 — malformed key/sig hex = not a valid signature
        return False


def _demo() -> None:
    if not available():
        print("signing self-check: SKIP (cryptography not installed — optional extra)")
        return
    priv, pub = generate_keypair()
    assert public_key_of(priv) == pub, "derived public key must match"
    msg = "a" * 64  # stand-in for an entry_hash
    sig = sign(priv, msg)
    assert verify(pub, msg, sig) is True, "honest signature must verify"
    assert verify(pub, msg + "x", sig) is False, "tampered message must fail"
    _, other_pub = generate_keypair()
    assert verify(other_pub, msg, sig) is False, "wrong key must fail"
    print("signing self-check: PASS (verify ok; tamper + wrong-key rejected)")


if __name__ == "__main__":
    _demo()

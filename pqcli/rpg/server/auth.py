from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import hmac
import secrets


@dataclass
class Account:
    account_id: str
    username: str
    password_hash: str
    roles: set[str] = field(default_factory=lambda: {"player"})
    character_ids: list[str] = field(default_factory=list)


class AuthService:
    """Small dependency-free authentication service for the game server."""

    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.sessions: dict[str, str] = {}

    @staticmethod
    def hash_password(password: str, salt: bytes | None = None) -> str:
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
        return f"pbkdf2_sha256$200000${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, rounds, salt_hex, digest_hex = encoded.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
            )
            return hmac.compare_digest(digest.hex(), digest_hex)
        except (ValueError, TypeError):
            return False

    def register(self, account_id: str, username: str, password: str) -> Account:
        if any(a.username.casefold() == username.casefold() for a in self.accounts.values()):
            raise ValueError("username already exists")
        account = Account(account_id, username, self.hash_password(password))
        self.accounts[account_id] = account
        return account

    def login(self, username: str, password: str) -> str:
        account = next((a for a in self.accounts.values() if a.username.casefold() == username.casefold()), None)
        if account is None or not self.verify_password(password, account.password_hash):
            raise ValueError("invalid credentials")
        token = secrets.token_urlsafe(32)
        self.sessions[token] = account.account_id
        return token

    def logout(self, token: str) -> None:
        self.sessions.pop(token, None)

    def account_for(self, token: str) -> Account | None:
        account_id = self.sessions.get(token)
        return self.accounts.get(account_id) if account_id else None

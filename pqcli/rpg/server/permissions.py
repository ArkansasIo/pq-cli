from __future__ import annotations

DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "player": {"chat", "trade", "party", "guild", "pvp"},
    "moderator": {"chat", "trade", "party", "guild", "pvp", "mute", "kick"},
    "gm": {"chat", "trade", "party", "guild", "pvp", "mute", "kick", "teleport", "grant"},
    "admin": {"*"},
}


def can(role_set: set[str], permission: str) -> bool:
    for role in role_set:
        permissions = DEFAULT_ROLE_PERMISSIONS.get(role, set())
        if "*" in permissions or permission in permissions:
            return True
    return False

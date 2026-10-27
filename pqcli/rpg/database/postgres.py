from __future__ import annotations

from typing import Any, Protocol


class ConnectionLike(Protocol):
    def cursor(self) -> Any: ...


class PostgresCharacterStore:
    """Small DB-API repository; psycopg is intentionally an optional dependency."""

    def __init__(self, connection: ConnectionLike) -> None:
        self.connection = connection

    def put(self, character_id: str, payload: dict[str, Any]) -> None:
        import json

        with self.connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO characters (id, name, level, data)
                   VALUES (%s, %s, %s, %s::jsonb)
                   ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name,
                   level=EXCLUDED.level, data=EXCLUDED.data""",
                (character_id, str(payload.get("name", "")), int(payload.get("level", 1)), json.dumps(payload)),
            )
        self.connection.commit()

    def get(self, character_id: str) -> dict[str, Any] | None:
        import json

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT data FROM characters WHERE id = %s", (character_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        value = row[0]
        return json.loads(value) if isinstance(value, str) else dict(value)

    def delete(self, character_id: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM characters WHERE id = %s", (character_id,))
        self.connection.commit()

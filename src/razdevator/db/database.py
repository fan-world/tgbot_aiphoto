from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

import aiosqlite


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected.")
        return self._conn

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> aiosqlite.Cursor:
        cursor = await self.conn.execute(query, params or [])
        await self.conn.commit()
        return cursor

    async def executemany(
        self,
        query: str,
        params: Iterable[Sequence[Any]],
    ) -> None:
        await self.conn.executemany(query, params)
        await self.conn.commit()

    async def fetchone(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(query, params or [])
        return await cursor.fetchone()

    async def fetchall(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(query, params or [])
        rows = await cursor.fetchall()
        return list(rows)

    async def fetchval(
        self,
        query: str,
        params: Sequence[Any] | None = None,
        default: Any = None,
    ) -> Any:
        row = await self.fetchone(query, params)
        if row is None:
            return default
        return next(iter(row))


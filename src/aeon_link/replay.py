"""Durable SQLite replay protection for signed, expiring AEON-Link messages."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .auth import VerifiedMessage
from .core import ProtocolError

class SQLiteReplayGuard:
    """Transactional uniqueness for (authenticated sender, message ID).

    Requires a separate DB per security domain or coordinated shared storage.
    Call after signature verification and before performing any side effect.
    """
    def __init__(self, path: str | Path):
        self.path = str(path)
        conn = self._connection()
        try:
            conn.execute('CREATE TABLE IF NOT EXISTS seen (sender TEXT NOT NULL, message_id TEXT NOT NULL, expires_at INTEGER NOT NULL, PRIMARY KEY(sender,message_id))')
        finally:
            conn.close()

    def _connection(self):
        return sqlite3.connect(self.path, timeout=10, isolation_level=None)

    def check(self, verified: VerifiedMessage, *, now: int) -> None:
        if not isinstance(verified, VerifiedMessage) or isinstance(now, bool) or not isinstance(now, int) or verified.expires_at < now:
            raise ProtocolError('Expected verified, unexpired message')
        conn = self._connection()
        try:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute('DELETE FROM seen WHERE expires_at < ?', (now,))
            conn.execute('INSERT INTO seen(sender,message_id,expires_at) VALUES (?,?,?)',
                         (verified.verified_sender, verified.envelope['message_id'], verified.expires_at))
            conn.execute('COMMIT')
        except sqlite3.IntegrityError as e:
            conn.execute('ROLLBACK')
            raise ProtocolError('Repeated authenticated message') from e
        except Exception:
            if conn.in_transaction:
                conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()

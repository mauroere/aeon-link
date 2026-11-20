"""Transactional persistent replay protection for VERIFIED AEON-Link messages."""
import sqlite3
from pathlib import Path
from aeon_link import ProtocolError
from aeon_auth import VerifiedMessage

class SQLiteReplayGuard:
    def __init__(self,path):
        self.path=str(Path(path))
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS seen(sender TEXT NOT NULL,message_id TEXT NOT NULL,expires_at INTEGER NOT NULL,PRIMARY KEY(sender,message_id))")

    def connect(self):
        return sqlite3.connect(self.path,timeout=10,isolation_level=None)

    def check(self,verified,*,now):
        if not isinstance(verified,VerifiedMessage) or isinstance(now,bool) or not isinstance(now,int) or verified.expires_at<now:
            raise ProtocolError("Expected verified unexpired message")
        db=self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM seen WHERE expires_at < ?",(now,))
            db.execute("INSERT INTO seen(sender,message_id,expires_at) VALUES (?,?,?)",
                       (verified.verified_sender,verified.envelope["message_id"],verified.expires_at))
            db.execute("COMMIT")
        except sqlite3.IntegrityError as e:
            db.execute("ROLLBACK")
            raise ProtocolError("Replay detected") from e
        except Exception:
            if db.in_transaction:db.execute("ROLLBACK")
            raise
        finally:
            db.close()

"""AEON-Link v0.3 optional HS256 envelope authentication.
Requires pre-provisioned trusted 32-byte minimum shared keys and HTTPS/TLS.
It proves message integrity under a shared secret, NOT authority or source truth.
"""
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Mapping
from aeon_link import ProtocolError, validate
from aeon_canonical import canonical_bytes

DOMAIN=b"AEON-LINK-HMAC-SHA256-v1\x00"
MAX_TTL=300
CLOCK_SKEW=30

@dataclass(frozen=True)
class TrustedKey:
    sender:str
    secret:bytes

@dataclass(frozen=True)
class VerifiedMessage:
    envelope:dict
    verified_sender:str
    key_id:str
    expires_at:int

def _mac(envelope,meta,secret):
    return hmac.new(secret,DOMAIN+canonical_bytes({"envelope":envelope,"meta":meta}),hashlib.sha256).hexdigest()

def sign_envelope(envelope,*,key_id,secret,issued_at=None,ttl_seconds=60):
    validate(envelope)
    if not isinstance(key_id,str) or not key_id or not isinstance(secret,bytes) or len(secret)<32:
        raise ProtocolError("Expected key ID and >=32-byte shared secret")
    if isinstance(ttl_seconds,bool) or not isinstance(ttl_seconds,int) or not 1<=ttl_seconds<=MAX_TTL:
        raise ProtocolError("Invalid TTL")
    now=int(time.time()) if issued_at is None else issued_at
    if isinstance(now,bool) or not isinstance(now,int):raise ProtocolError("Invalid issued_at")
    meta={"alg":"HS256","key_id":key_id,"issued_at":now,"expires_at":now+ttl_seconds}
    return {"envelope":envelope,"meta":meta,"signature":_mac(envelope,meta,secret)}

def verify_signed(wrapper, trusted_keys:Mapping[str,TrustedKey],*,now=None):
    if not isinstance(wrapper,dict) or set(wrapper)!={"envelope","meta","signature"}:
        raise ProtocolError("Invalid signed wrapper")
    e,m=wrapper["envelope"],wrapper["meta"]
    validate(e)
    if not isinstance(m,dict) or set(m)!={"alg","key_id","issued_at","expires_at"} or m["alg"]!="HS256":
        raise ProtocolError("Invalid signed metadata")
    key_id=m["key_id"]
    key=trusted_keys.get(key_id) if isinstance(key_id,str) else None
    if not isinstance(key,TrustedKey) or not isinstance(key.secret,bytes) or len(key.secret)<32:
        raise ProtocolError("Unknown trusted key")
    start,end=m["issued_at"],m["expires_at"]
    if any(isinstance(v,bool) or not isinstance(v,int) for v in (start,end)) or not 1<=end-start<=MAX_TTL:
        raise ProtocolError("Invalid signed time window")
    clock=int(time.time()) if now is None else now
    if isinstance(clock,bool) or not isinstance(clock,int) or start>clock+CLOCK_SKEW or end<clock:
        raise ProtocolError("Expired or future message")
    sig=wrapper["signature"]
    if not isinstance(sig,str) or len(sig)!=64 or not hmac.compare_digest(sig,_mac(e,m,key.secret)):
        raise ProtocolError("Bad message signature")
    if e["sender"]!=key.sender:raise ProtocolError("Key does not bind to claimed sender")
    return VerifiedMessage(e,key.sender,key_id,end)

def verify_evidence_bytes(evidence,content):
    """SHA-256 content integrity only; does not prove evidence source or claim truth."""
    if not isinstance(evidence,dict) or not isinstance(content,bytes):
        raise ProtocolError("Expected evidence record and bytes")
    expected=evidence.get("sha256")
    if not isinstance(expected,str) or len(expected)!=64:
        raise ProtocolError("Evidence requires a sha256 digest")
    if not hmac.compare_digest(expected,hashlib.sha256(content).hexdigest()):
        raise ProtocolError("Evidence does not match SHA-256")
    return True

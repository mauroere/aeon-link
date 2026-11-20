"""AEON-Link v0.3 restricted cross-runtime canonical JSON (not RFC 8785)."""
import hashlib
import json
import re

class CanonicalizationError(ValueError): pass
KEY=re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
MAX_INTEGER=2**53-1
MAX_BYTES=1048576

def _check(x,depth=0):
    if depth>64: raise CanonicalizationError("Maximum depth exceeded")
    if x is None or isinstance(x,bool):return
    if isinstance(x,int):
        if abs(x)>MAX_INTEGER:raise CanonicalizationError("Unsafe integer")
        return
    if isinstance(x,str):
        try: x.encode("utf-8",errors="strict")
        except UnicodeError as e: raise CanonicalizationError("Unpaired surrogate") from e
        return
    if isinstance(x,list):
        for item in x:_check(item,depth+1)
        return
    if isinstance(x,dict):
        for k,v in x.items():
            if not isinstance(k,str) or not KEY.fullmatch(k):raise CanonicalizationError("Expected ASCII identifier keys")
            _check(v,depth+1)
        return
    raise CanonicalizationError("Unsupported JSON value or float")

def canonical_bytes(value):
    _check(value)
    encoded=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")
    if len(encoded)>MAX_BYTES: raise CanonicalizationError("Message exceeds 1 MiB")
    return encoded

def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def parse_canonical(data):
    if not isinstance(data,bytes) or len(data)>MAX_BYTES:raise CanonicalizationError("Invalid bytes/size")
    try: value=json.loads(data.decode("utf-8",errors="strict"))
    except (UnicodeError,json.JSONDecodeError) as e: raise CanonicalizationError("Invalid JSON/UTF-8") from e
    if canonical_bytes(value)!=data:raise CanonicalizationError("Noncanonical JSON (including duplicate keys)")
    return value

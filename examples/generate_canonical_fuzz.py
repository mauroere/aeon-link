"""Deterministic, cross-runtime Python->Node canonicalization vectors.

No hypothesis about randomly generated *semantic* understanding is implied.
"""
import json
import random
import sys
from aeon_link.canonical import canonical_bytes, digest

R = random.Random(0xA30F15)
ALPHABET = 'aBxyZ\n\t\b é漢🚀\u2028\u2029"\\' + chr(0) + chr(127)

def value(depth=0):
    kind = R.randrange(5 if depth < 4 else 3)
    if kind == 0: return None
    if kind == 1: return bool(R.randrange(2))
    if kind == 2: return R.choice([0,1,-1,2**53-1,-(2**53-1),R.randrange(-1000000,1000000)])
    if kind == 3: return [value(depth+1) for _ in range(R.randrange(0,5))]
    if kind == 4: return {f'k{i}':value(depth+1) for i in R.sample(range(25),R.randrange(0,5))}
    return ''.join(R.choice(ALPHABET) for _ in range(R.randrange(0,24)))

def main():
    vectors=[]
    for i in range(400):
        obj={'case':i,'payload':value()}
        vectors.append({'value':obj,'sha256':digest(obj),'canonical_hex':canonical_bytes(obj).hex()})
    json.dump(vectors,sys.stdout,ensure_ascii=True,separators=(',',':'))

if __name__=='__main__': main()

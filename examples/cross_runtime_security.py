"""Round-trip HMAC across Python and Node.js without any model API credentials."""
import json
import os
import subprocess
import sys
from pathlib import Path
from aeon_link import message, sign_envelope, verify_signed, TrustedKey, canonical_bytes, digest

root=Path(__file__).resolve().parents[1]
key=bytes(range(32))
objective={'id':'o1','text':'Validar Unicode 🚀 y ñ','success_criteria':['Echo objective']}
msg=message('task','agent-a','agent-b',{'objective':objective,'constraints':{'read_only':True},'action':'observe','claims':[],'evidence':[]})
signed=sign_envelope(msg,key_id='demo-1',secret=key,issued_at=1_700_000_000,ttl_seconds=120)
result=subprocess.run(['node',str(root/'js'/'verify-python-signature.mjs')],input=json.dumps(signed,ensure_ascii=False),capture_output=True,text=True,check=True)
response=json.loads(result.stdout)
assert response['digest']==digest(objective)
reply=verify_signed(response['signed'],{'demo-1':TrustedKey('agent-b',key)},now=1_700_000_010)
assert reply.envelope['body']['in_reply_to']==msg['message_id']
print('PASS: Python→Node HMAC, Node→Python HMAC, and Unicode objective digest')

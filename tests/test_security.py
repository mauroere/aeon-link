"""v0.3 standalone reference tests. Pure stdlib, no external credentials."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from aeon_link import message, hello, negotiate, ProtocolError, LocalPolicy, authorize
from aeon_canonical import canonical_bytes, parse_canonical, CanonicalizationError
from aeon_auth import TrustedKey, sign_envelope, verify_signed, verify_evidence_bytes
from aeon_replay import SQLiteReplayGuard
KEY=bytes(range(32))
TRUST={'demo':TrustedKey('alpha',KEY)}
def task():
    return message('task','alpha','beta',{
      'objective':{'id':'o1','text':'Conexión 🚀'},'constraints':{'read_only':True},
      'action':'observe','claims':[],'evidence':[]})
class TestV03(unittest.TestCase):
    def signed(self):
        return sign_envelope(task(),key_id='demo',secret=KEY,issued_at=1700000000)
    def test_handshake(self):
        self.assertEqual(negotiate(hello('alpha','beta'),hello('beta','alpha')).version,'0.3.0')
    def test_canonical_unicode(self):
        self.assertEqual(canonical_bytes({'z':'é 🚀','a':[1,True]}),b'{"a":[1,true],"z":"\xc3\xa9 \xf0\x9f\x9a\x80"}')
    def test_duplicate_wire_keys(self):
        with self.assertRaises(CanonicalizationError):parse_canonical(b'{"a":1,"a":2}')
    def test_float_rejected(self):
        with self.assertRaises(CanonicalizationError):canonical_bytes({'x':0.1})
    def test_unsafe_integer_rejected(self):
        with self.assertRaises(CanonicalizationError):canonical_bytes({'x':2**53})
    def test_hmac_verifies(self):
        v=verify_signed(self.signed(),TRUST,now=1700000001)
        self.assertEqual(v.verified_sender,'alpha')
    def test_tampering_rejected(self):
        s=self.signed();s['envelope']['body']['objective']['text']='tampered'
        with self.assertRaises(ProtocolError):verify_signed(s,TRUST,now=1700000001)
    def test_wrong_sender_binding(self):
        with self.assertRaises(ProtocolError):verify_signed(self.signed(),{'demo':TrustedKey('other',KEY)},now=1700000001)
    def test_wrong_key_rejected(self):
        with self.assertRaises(ProtocolError):verify_signed(self.signed(),{'demo':TrustedKey('alpha',b'x'*32)},now=1700000001)
    def test_expired_rejected(self):
        with self.assertRaises(ProtocolError):verify_signed(self.signed(),TRUST,now=1700000061)
    def test_future_rejected(self):
        with self.assertRaises(ProtocolError):verify_signed(self.signed(),TRUST,now=1699999969)
    def test_persistent_replay(self):
        s=self.signed();v=verify_signed(s,TRUST,now=1700000001)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'seen.sqlite'
            SQLiteReplayGuard(p).check(v,now=1700000001)
            with self.assertRaises(ProtocolError):SQLiteReplayGuard(p).check(v,now=1700000001)
    def test_local_authorization(self):
        v=verify_signed(self.signed(),TRUST,now=1700000001)
        self.assertTrue(authorize(v.envelope,LocalPolicy(v.verified_sender,frozenset({'observe'}))))
        with self.assertRaises(ProtocolError):authorize(v.envelope,LocalPolicy(v.verified_sender,frozenset({'execute'})))
    def test_evidence_bytes_integrity(self):
        b=b'DNS result';h=hashlib.sha256(b).hexdigest()
        self.assertTrue(verify_evidence_bytes({'sha256':h},b))
        with self.assertRaises(ProtocolError):verify_evidence_bytes({'sha256':h},b'altered')
if __name__=='__main__':unittest.main()

"""Security and JSON canonicalization tests: protocol 0.3.0."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from aeon_link import (
    CanonicalizationError, ProtocolError, LocalPolicy, authorize_task,
    canonical_bytes, digest, hello, message, negotiate, parse_canonical,
    SQLiteReplayGuard, TrustedKey, sign_envelope, verify_signed, verify_evidence_content,
)

KEY = bytes(range(32))
TRUST = {'demo-key': TrustedKey('alpha', KEY)}


def task():
    return message('task', 'alpha', 'beta', {
        'objective': {'id': 'o1', 'text': 'Revisar conexión 🚀', 'success_criteria': ['Sin pérdidas']},
        'constraints': {'read_only': True}, 'action': 'observe', 'claims': [], 'evidence': []})


class CanonicalTests(unittest.TestCase):
    def test_key_order_and_utf8(self):
        self.assertEqual(canonical_bytes({'z': 'é 🚀', 'a': [1, True]}), b'{"a":[1,true],"z":"\xc3\xa9 \xf0\x9f\x9a\x80"}')

    def test_reject_floating_point(self):
        with self.assertRaises(CanonicalizationError): canonical_bytes({'x':1.5})
        with self.assertRaises(CanonicalizationError): canonical_bytes({'x':1.0})

    def test_reject_big_int(self):
        with self.assertRaises(CanonicalizationError): canonical_bytes({'x':2**53})

    def test_reject_unicode_key(self):
        with self.assertRaises(CanonicalizationError): canonical_bytes({'clé':'foo'})

    def test_reject_unpaired_surrogate(self):
        with self.assertRaises(CanonicalizationError): canonical_bytes({'x':'\ud800'})

    def test_reject_excessive_nesting(self):
        x = None
        for _ in range(80): x = [x]
        with self.assertRaises(CanonicalizationError): canonical_bytes(x)

    def test_duplicate_wire_keys_rejected(self):
        with self.assertRaises(CanonicalizationError): parse_canonical(b'{"a":1,"a":2}')

    def test_noncannonical_wire_rejected(self):
        with self.assertRaises(CanonicalizationError): parse_canonical(b'{ "a": 1 }')

    def test_canonical_parse_roundtrip(self):
        raw = canonical_bytes({'alpha':'ß', 'x':42})
        self.assertEqual(parse_canonical(raw), {'alpha':'ß','x':42})


class EvidenceTests(unittest.TestCase):
    def test_matching_bytes(self):
        import hashlib
        data=b'dns probe result'
        self.assertTrue(verify_evidence_content({'sha256': hashlib.sha256(data).hexdigest()}, data))
    def test_mismatching_bytes(self):
        import hashlib
        with self.assertRaises(ProtocolError):
            verify_evidence_content({'sha256': hashlib.sha256(b'true').hexdigest()}, b'false')


class AuthTests(unittest.TestCase):
    def signed(self, issued=1000):
        return sign_envelope(task(),key_id='demo-key',secret=KEY,issued_at=issued,ttl_seconds=60)

    def test_verify_and_host_policy(self):
        t=self.signed()
        verified=verify_signed(t,TRUST,now=1010)
        self.assertEqual(verified.verified_sender,'alpha')
        authorize_task(verified.envelope,LocalPolicy(frozenset({'observe'}),verified.verified_sender))

    def test_tamper_message(self):
        t=self.signed(); t['envelope']['body']['objective']['text']='Alterado'
        with self.assertRaises(ProtocolError): verify_signed(t,TRUST,now=1010)

    def test_tamper_meta(self):
        t=self.signed(); t['meta']['expires_at']+=1
        with self.assertRaises(ProtocolError): verify_signed(t,TRUST,now=1010)

    def test_missing_key(self):
        with self.assertRaises(ProtocolError): verify_signed(self.signed(),{},now=1010)

    def test_wrong_signing_key(self):
        t=sign_envelope(task(),key_id='demo-key',secret=b'X'*32,issued_at=1000)
        with self.assertRaises(ProtocolError): verify_signed(t,TRUST,now=1010)

    def test_identity_binding(self):
        with self.assertRaises(ProtocolError): verify_signed(self.signed(),{'demo-key':TrustedKey('omega', KEY)},now=1010)

    def test_expired(self):
        with self.assertRaises(ProtocolError): verify_signed(self.signed(),TRUST,now=1061)

    def test_future(self):
        with self.assertRaises(ProtocolError): verify_signed(self.signed(),TRUST,now=969)

    def test_oversized_ttl_rejected(self):
        with self.assertRaises(ProtocolError): sign_envelope(task(),key_id='demo-key',secret=KEY,issued_at=1000,ttl_seconds=1000)

    def test_short_key_rejected(self):
        with self.assertRaises(ProtocolError): sign_envelope(task(),key_id='demo-key',secret=b'short')

    def test_bad_signature_rejected(self):
        t=self.signed(); t['signature']='z'*64
        with self.assertRaises(ProtocolError): verify_signed(t,TRUST,now=1010)

    def test_durable_replay_rejected_after_restart(self):
        t=self.signed(); v=verify_signed(t,TRUST,now=1010)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'replays.sqlite'
            SQLiteReplayGuard(path).check(v,now=1010)
            with self.assertRaises(ProtocolError):
                SQLiteReplayGuard(path).check(v,now=1010)

    def test_distinct_signed_messages_allowed(self):
        a=self.signed(); b=self.signed()
        with tempfile.TemporaryDirectory() as d:
            g=SQLiteReplayGuard(Path(d)/'seen.db')
            for s in (a,b): g.check(verify_signed(s,TRUST,now=1010),now=1010)

    def test_replay_guard_requires_verified(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ProtocolError): SQLiteReplayGuard(Path(d)/'seen.db').check(task(), now=1010)


if __name__ == '__main__': unittest.main()

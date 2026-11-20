import copy
import tempfile
import unittest
from pathlib import Path
from aeon_link import (message, ProtocolError, LocalPolicy, TrustedKey,
                       sign_envelope, SQLiteReplayGuard, canonical_bytes,
                       receive_signed, prepare_semantic_probe,
                       analyze_responses, metamorphic_cases)
from aeon_link.semantics import respond_to_challenge, evaluate_contract, PROFILE

KEY = bytes(range(32))
CLOCK=1700000005

def task(action='observe', target='beta'):
    return message('task','alpha',target,{'objective':{'id':'case-1','text':'Observe',
            'success_criteria':['Report status']},
            'constraints':{'read_only':True},'action':action,'claims':[],'evidence':[]})

def contract():
    return {'profile':PROFILE,'allowed_actions':['read'],
            'clauses':[{'id':'authenticated','mode':'require',
                        'path':'/authenticated','op':'eq','value':True},
                       {'id':'locked','mode':'forbid','path':'/locked','op':'eq','value':True}]}

class InboundTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guard=SQLiteReplayGuard(Path(self.tmp.name)/'replay.sqlite')
        self.trust={'k1':TrustedKey('alpha',KEY)}
        self.policy=LocalPolicy(frozenset({'observe'}),'alpha')
    def signed(self, env=None):
        return canonical_bytes(sign_envelope(env or task(),key_id='k1',secret=KEY,issued_at=CLOCK))
    def recv(self,raw, **overrides):
        args={'trusted_keys':self.trust,'local_recipient':'beta',
              'local_policy':self.policy,'replay_guard':self.guard,'now':CLOCK+1}
        args.update(overrides)
        return receive_signed(raw,**args)
    def test_valid(self):
        r=self.recv(self.signed())
        self.assertEqual((r.verified_sender,r.recipient),('alpha','beta'))
        self.assertTrue(r.replay_recorded)
    def test_replay_even_after_restart(self):
        raw=self.signed()
        self.recv(raw)
        with self.assertRaisesRegex(ProtocolError,'Repeated'):
            self.recv(raw,replay_guard=SQLiteReplayGuard(Path(self.tmp.name)/'replay.sqlite'))
    def test_wrong_target_never_consumes_replay(self):
        raw=self.signed(task(target='gamma'))
        with self.assertRaisesRegex(ProtocolError,'recipient'):
            self.recv(raw)
        self.assertEqual(self.recv(raw,local_recipient='gamma').recipient,'gamma')
    def test_task_without_policy_denied(self):
        with self.assertRaises(ProtocolError):self.recv(self.signed(),local_policy=None)
    def test_bad_policy_denied(self):
        with self.assertRaises(ProtocolError):self.recv(self.signed(),local_policy=LocalPolicy(frozenset({'execute'}),'alpha'))
    def test_policy_wrong_sender_denied(self):
        with self.assertRaises(ProtocolError):self.recv(self.signed(),local_policy=LocalPolicy(frozenset({'observe'}),'other'))
    def test_tamper_denied(self):
        signed=sign_envelope(task(),key_id='k1',secret=KEY,issued_at=CLOCK)
        signed['envelope']['body']['objective']['text']='Not the original'
        with self.assertRaises(ProtocolError):self.recv(canonical_bytes(signed))
    def test_duplicate_json_key_denied(self):
        raw=self.signed().replace(b'"envelope":',b'"junk":0,"envelope":',1)
        with self.assertRaises(ProtocolError):self.recv(raw)
    def test_unsafe_wire_denied(self):
        with self.assertRaises(ProtocolError):self.recv(b'{"envelope":NaN}')
    def test_expiration_denied(self):
        with self.assertRaises(ProtocolError):self.recv(self.signed(),now=CLOCK+61)
    def test_reject_non_guard(self):
        with self.assertRaises(ProtocolError):self.recv(self.signed(),replay_guard=None)
    def test_reject_invalid_wall_clock(self):
        with self.assertRaises(ProtocolError):self.recv(self.signed(),now=True)
    def test_hello_also_requires_replay(self):
        h=message('hello','alpha','beta',{'versions':['0.4.0'], 'ontologies':['urn:aeon-link:ontology:core:0.4.0'], 'features':[]})
        raw=self.signed(h)
        r=self.recv(raw,local_policy=None)
        self.assertEqual(r.envelope['kind'],'hello')
        with self.assertRaises(ProtocolError):self.recv(raw,local_policy=None)

class MetamorphicTest(unittest.TestCase):
    def test_invariance_cases(self):
        c=contract(); baseline={'authenticated':True,'locked':False}
        cases=metamorphic_cases(c,baseline,'read')
        ids={case['id'] for case in cases}
        self.assertIn('baseline',ids)
        self.assertIn('invariant_unicode',ids)
        for case in cases:
            if case['id'].startswith('invariant_'):
                self.assertEqual(evaluate_contract(c,case['state'],'read')['status'],'satisfied')
    def test_probe_and_compare(self):
        c=contract(); baseline={'authenticated':True,'locked':False}
        public,private=prepare_semantic_probe(c,baseline,'read')
        good=respond_to_challenge(c,public)
        self.assertTrue(analyze_responses(private,{'agent-one':good})['agents']['agent-one']['passed'])
        bad=copy.deepcopy(good);bad['answers'][0]['status']='violated'
        result=analyze_responses(private,{'a':good,'b':bad})
        self.assertFalse(result['agents']['b']['passed'])
    def test_baseline_must_satisfy(self):
        with self.assertRaises(Exception):metamorphic_cases(contract(),{'authenticated':False,'locked':True},'read')
    def test_maximum(self):
        with self.assertRaises(Exception):metamorphic_cases(contract(),{'authenticated':True,'locked':False},'read',maximum=0)

if __name__=='__main__':unittest.main()

import unittest
from aeon_link import *

class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.task=message("task","a","b",{"objective":{"id":"1","text":"Identify issues"},
            "constraints":{"read_only":True},"action":"observe","claims":[],"evidence":[]})
    def test_handshake(self):
        self.assertEqual(negotiate(hello("a","b"),hello("b","a")).version,VERSION)
    def test_reject_write(self):
        b=dict(self.task["body"]);b["action"]="write"
        with self.assertRaises(ProtocolError):message("task","a","b",b)
    def test_fact_requires_evidence(self):
        b=dict(self.task["body"]);b["claims"]=[{"id":"x","status":"fact","evidence_ids":[]}]
        with self.assertRaises(ProtocolError):message("task","a","b",b)
    def test_ack(self):
        self.assertTrue(verify_ack(self.task,acknowledge(self.task,"b")))
    def test_host_permission(self):
        self.assertTrue(authorize(self.task,LocalPolicy("a",frozenset({"observe"}))))
        with self.assertRaises(ProtocolError):authorize(self.task,LocalPolicy("z",frozenset({"observe"})))
if __name__=="__main__":unittest.main()

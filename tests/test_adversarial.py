"""Regression tests for hostile data at the semantic/profile trust boundaries."""
import copy
import unittest
from aeon_link.semantics import (PROFILE, ContractError, evaluate_contract, normalize_contract,
                                  create_challenge, respond_to_challenge, score_challenge)
from aeon_link.evidence_graph import PROFILE as GRAPH_PROFILE, GraphError, validate_graph


def contract():
    return {'profile':PROFILE, 'allowed_actions':['observe'], 'clauses':[
        {'id':'block', 'mode':'forbid', 'path':'/permissions/write', 'op':'eq','value':True},
    ]}

class AdversarialTests(unittest.TestCase):
    def test_reject_unhashable_mode(self):
        c=contract();c['clauses'][0]['mode']=['forbid']
        with self.assertRaises(ContractError): normalize_contract(c)
    def test_reject_unhashable_operator(self):
        c=contract();c['clauses'][0]['op']=['eq']
        with self.assertRaises(ContractError): normalize_contract(c)
    def test_reject_unhashable_answer_status(self):
        c=contract();case={'id':'x','state':{'permissions':{'write':False}},'action':'observe'}
        public,key=create_challenge(c,[case]);resp=respond_to_challenge(c,public)
        resp['answers'][0]['status']=['satisfied']
        with self.assertRaises(ContractError):score_challenge(key,resp)
    def test_prohibition_missing_is_not_clearance(self):
        self.assertEqual(evaluate_contract(contract(),{},'observe')['status'],'incomplete')
    def test_explicit_prohibition_rejected(self):
        self.assertEqual(evaluate_contract(contract(),{'permissions':{'write':True}},'observe')['status'],'violated')
    def test_unexpected_graph_field_rejected(self):
        graph={'profile':GRAPH_PROFILE,'nodes':[{'id':'e','kind':'evidence','trusted':True}],'edges':[]}
        with self.assertRaises(GraphError):validate_graph(graph)
    def test_unhashable_graph_kind_rejected(self):
        graph={'profile':GRAPH_PROFILE,'nodes':[{'id':'e','kind':['evidence']}],'edges':[]}
        with self.assertRaises(GraphError):validate_graph(graph)
    def test_wrong_graph_relation_rejected(self):
        graph={'profile':GRAPH_PROFILE,'nodes':[{'id':'e','kind':'evidence'}],
               'edges':[{'from':'e','to':'e','type':'execute'}]}
        with self.assertRaises(GraphError):validate_graph(graph)
    def test_hostile_pointer_not_evaluated(self):
        c=contract();c['clauses'][0]['path']='/permissions/constructor'
        with self.assertRaises(ContractError):normalize_contract(c)

if __name__=='__main__':unittest.main()

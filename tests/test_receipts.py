import copy
import unittest
from aeon_link.receipts import make_decision_receipt, verify_decision_receipt
from aeon_link.semantics import PROFILE, ContractError

C={'profile':PROFILE,'allowed_actions':['read'], 'clauses':[
 {'id':'a','mode':'require','path':'/authenticated','op':'eq','value':True},
 {'id':'b','mode':'forbid','path':'/blocked','op':'eq','value':True}]}

class ReceiptTests(unittest.TestCase):
    def test_success(self):
        s={'authenticated':True,'blocked':False}
        r=make_decision_receipt(C,s,'read')
        self.assertEqual([v['outcome'] for v in r['trace']],['pass','pass'])
        self.assertTrue(verify_decision_receipt(C,s,'read',r))
    def test_unknown(self):
        r=make_decision_receipt(C,{'authenticated':True},'read')
        self.assertEqual(r['decision']['status'],'incomplete')
        self.assertEqual(r['trace'][1]['outcome'],'unknown')
    def test_unauthorized(self):
        r=make_decision_receipt(C,{'authenticated':True},'execute')
        self.assertEqual(r['trace'],[{'id':'action:unauthorized','outcome':'fail'}])
    def test_modified_receipt(self):
        s={'authenticated':True,'blocked':False}
        r=make_decision_receipt(C,s,'read');r['trace'][0]['outcome']='fail'
        with self.assertRaises(ContractError):verify_decision_receipt(C,s,'read',r)
    def test_modified_input(self):
        s={'authenticated':True,'blocked':False}
        r=make_decision_receipt(C,s,'read')
        with self.assertRaises(ContractError):verify_decision_receipt(C,{**s,'blocked':True},'read',r)

if __name__=='__main__':unittest.main()

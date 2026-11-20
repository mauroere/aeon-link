import unittest
from aeon_link.semantics import *

def contract():
    return {"profile": PROFILE, "allowed_actions": ["observe", "read"], "clauses": [
        {"id": "dns", "mode": "require", "op": "eq", "path": "/dns/resolved", "value": True},
        {"id": "no-change", "mode": "forbid", "op": "eq", "path": "/changes/config", "value": True},
        {"id": "loss", "mode": "require", "op": "lte", "path": "/metrics/loss_percent", "value": 1},
    ]}

def state(dns=True, change=False, loss=1):
    return {"dns": {"resolved": dns}, "changes": {"config": change}, "metrics": {"loss_percent": loss}}

class SemanticsTests(unittest.TestCase):
    def test_contract_success(self):
        self.assertEqual(evaluate_contract(contract(),state(),"observe")['status'],"satisfied")
    def test_forbidden_change(self):
        self.assertEqual(evaluate_contract(contract(),state(change=True),"observe")['violations'],["no-change"])
    def test_wrong_dns(self):
        self.assertIn("dns",evaluate_contract(contract(),state(dns=False),"observe")['violations'])
    def test_bad_loss(self):
        self.assertEqual(evaluate_contract(contract(),state(loss=2),"observe")['status'],"violated")
    def test_unknown_not_false(self):
        self.assertEqual(evaluate_contract(contract(),{"dns": {"resolved":True}},"observe")['status'],"incomplete")
    def test_unauthorized_action(self):
        self.assertEqual(evaluate_contract(contract(),state(),"write")['status'],"violated")
    def test_fingerprint_order_independent(self):
        c=contract();d=contract();d['clauses'].reverse();d['allowed_actions'].reverse()
        self.assertEqual(contract_fingerprint(c),contract_fingerprint(d))
    def test_fingerprint_changes_on_contract_change(self):
        c=contract();d=contract();d['clauses'][0]['value']=False
        self.assertNotEqual(contract_fingerprint(c),contract_fingerprint(d))
    def test_reject_duplicate_clause(self):
        c=contract();c['clauses'].append(c['clauses'][0])
        with self.assertRaises(ContractError):normalize_contract(c)
    def test_reject_bad_pointer(self):
        c=contract();c['clauses'][0]['path']='/dns/~2bad'
        with self.assertRaises(ContractError):normalize_contract(c)
    def test_reject_bool_int_comparison(self):
        c=contract();c['clauses'][2]['value']=True
        with self.assertRaises(ContractError):normalize_contract(c)
    def test_bool_not_equal_int(self):
        c=contract();c['clauses'][0]['value']=1
        self.assertIn("dns",evaluate_contract(c,state(),"observe")['violations'])
    def test_challenge_correct(self):
        c=contract();pub,key=create_challenge(c,[{"id": "ok", "state":state(),"action":"observe"},{"id":"bad", "state":state(change=True),"action":"observe"},{"id":"missing","state":{},"action":"observe"}])
        response={"nonce":pub["nonce"],"contract_digest":pub["contract_digest"],"answers":[{"id":"ok","status":"satisfied"},{"id":"bad","status":"violated"},{"id":"missing","status":"incomplete"}]}
        self.assertTrue(score_challenge(key,response)['passed'])
        response['answers'][0]['status']='violated'
        self.assertEqual(score_challenge(key,response)['correct'],2)
    def test_challenge_nonce_replay(self):
        public,key=create_challenge(contract(),[{"id":"x","state":state(),"action":"read"}])
        resp={"nonce":"old-nonce","contract_digest":public['contract_digest'],"answers":[{"id":"x","status":"satisfied"}]}
        with self.assertRaises(ContractError):score_challenge(key,resp)
    def test_noncanonical_input(self):
        c=contract(); c['clauses'][0]['value']=1.1
        with self.assertRaises(ContractError):normalize_contract(c)
    def test_pointer_escape_outside_profile_rejected(self):
        c={"profile":PROFILE,"allowed_actions":["observe"],"clauses":[{"id":"escape","mode":"require","op":"eq","path":"/a~1b/~0","value":"yes"}]}
        with self.assertRaises(ContractError):normalize_contract(c)



class CounterfactualTests(unittest.TestCase):
    def test_generated_probes(self):
        c = contract()
        cases = counterfactual_cases(c, state(), "observe")
        self.assertGreaterEqual(len(cases), 4)
        outcomes = [evaluate_contract(c, e["state"], e["action"])["status"] for e in cases]
        self.assertIn("satisfied", outcomes)
        self.assertIn("violated", outcomes)
        self.assertIn("incomplete", outcomes)
        public, key = create_challenge(c, cases)
        self.assertTrue(score_challenge(key, respond_to_challenge(c, public))["passed"])
    def test_baseline_must_satisfy(self):
        with self.assertRaises(ContractError):
            counterfactual_cases(contract(), state(dns=False), "observe")
    def test_maximum(self):
        cases = counterfactual_cases(contract(), state(), "observe", maximum=2)
        self.assertEqual(len(cases),2)
    def test_cannot_forge_challenge(self):
        c = contract()
        pub, key = create_challenge(c, counterfactual_cases(c, state(), "read"))
        reply = respond_to_challenge(c, pub)
        reply["answers"][0]["status"] = "violated"
        self.assertFalse(score_challenge(key, reply)["passed"])
    def test_unknown_action_does_not_grant_permission(self):
        c = contract()
        cases=counterfactual_cases(c, state(), "observe")
        bad=next(x for x in cases if x["id"] == "unauthorized_action")
        self.assertEqual(evaluate_contract(c,bad["state"],bad["action"])["status"],"violated")

if __name__ == "__main__": unittest.main()

import copy
import json
import tempfile
import unittest
from unittest.mock import patch

from aeon_link.research_eval import (
    DOMAINS, METHODS, SPLITS, VERSION, _binom_two_sided, _paired_ci,
    make_cases, dataset_digest, prompt_for, extract_status,
    score_records, run_live
)
from aeon_link.providers import ModelReply, ProviderError
from aeon_link.semantics import evaluate_contract

class ResearchExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus=make_cases()

    def test_corpus_size_and_split(self):
        self.assertEqual(len(self.corpus['splits']['pilot']),144)
        self.assertEqual(len(self.corpus['splits']['evaluation']),216)
        self.assertEqual(len({x['case_id'] for s in SPLITS for x in self.corpus['splits'][s]}),360)

    def test_strict_determinism(self):
        self.assertEqual(dataset_digest(self.corpus), 'aa2d2d9ffc28ed085d99c00e771db9d6bafabbc350b41e974f555bff89392c34')
        self.assertEqual(self.corpus,make_cases())
        self.assertEqual(dataset_digest(self.corpus),dataset_digest(make_cases()))

    def test_six_domains_in_each_split(self):
        self.assertEqual({c['domain'] for c in self.corpus['splits']['pilot']}, {d[0] for d in DOMAINS})
        self.assertEqual({c['domain'] for c in self.corpus['splits']['evaluation']}, {d[0] for d in DOMAINS})

    def test_all_three_statuses_in_each_split(self):
        for split in SPLITS:
            self.assertEqual({x['expected'] for x in self.corpus['splits'][split]},
                             {'satisfied','violated','incomplete'})

    def test_oracle_recomputable(self):
        for split in SPLITS:
            for c in self.corpus['splits'][split]:
                self.assertEqual(evaluate_contract(c['contract'],c['state'],c['action'])['status'],c['expected'])

    def test_payloads_distinct_and_no_label_leak(self):
        c=self.corpus['splits']['pilot'][0]
        messages=[prompt_for(m,c) for m in METHODS]
        self.assertEqual(len(set(messages)),3)
        for p in messages:
            self.assertNotIn('"expected"',p)
            self.assertIn(c['action'],p)
        self.assertIn('Prohibition:',messages[0])
        self.assertIn('"conditions"',messages[1])
        self.assertIn('"semantic_profile"',messages[2])

    def test_counterfactual_invariance(self):
        cases=self.corpus['splits']['pilot']+self.corpus['splits']['evaluation']
        for c in cases:
            if 'comment' not in c['state']:continue
            state=dict(c['state']);state['comment']='revised malicious instructions'
            self.assertEqual(evaluate_contract(c['contract'],c['state'],c['action']),
                             evaluate_contract(c['contract'],state,c['action']))

    def test_challenge_unauthorized_action(self):
        for c in self.corpus['splits']['pilot']:
            if c['action']=='execute':self.assertEqual(c['expected'],'violated')

    def test_invalid_status_is_error(self):
        for bad in ('ok','{"status":"allow"}','{"status":"satisfied","extra":true}',
                    '```json\n{"status":"violated"}\n```','[]','{"status":null}'):
            self.assertEqual(extract_status(bad),'error')

    def records(self,split='pilot',mode='perfect'):
        records=[]
        for c in self.corpus['splits'][split]:
            for m in METHODS:
                status=c['expected']
                if mode=='aeon-advantage' and m!='aeon-semantic' and c['case_id'].endswith('0001'):
                    status='error'
                records.append({'case_id':c['case_id'],'method':m,'predicted':status,
                                'latency_ms':10,'total_tokens':20})
        return records

    def test_perfect_scoring(self):
        result=score_records(self.corpus,self.records())
        self.assertEqual(result['paired_cases'],144)
        self.assertTrue(all(d['accuracy']==1.0 for d in result['methods'].values()))
        self.assertEqual(result['comparisons']['natural']['mcnemar_exact_p'],1.)

    def test_advantage_recorded_but_not_claimed(self):
        r=score_records(self.corpus,self.records(mode='aeon-advantage'))
        self.assertGreater(r['comparisons']['natural']['difference_pp'],0)
        self.assertIn('DESCRIPTIVE ONLY',r['interpretation'])

    def test_duplicate_row_rejected(self):
        rows=self.records();rows[0]=rows[1]
        with self.assertRaises(ValueError):score_records(self.corpus,rows)

    def test_missing_row_rejected(self):
        with self.assertRaises(ValueError):score_records(self.corpus,self.records()[:-1])

    def test_forged_gold_rejected(self):
        manipulated=copy.deepcopy(self.corpus)
        manipulated['splits']['pilot'][0]['expected']='wrong'
        with self.assertRaises(ValueError):score_records(manipulated,self.records())

    def test_result_pairing_not_silently_filtered(self):
        rows=self.records();rows[0]['predicted']='error'
        result=score_records(self.corpus,rows)
        self.assertEqual(result['methods'][rows[0]['method']]['errors'],1)

    def test_invalid_measurement_rejected(self):
        rows=self.records();rows[0]['latency_ms']=-1
        with self.assertRaises(ValueError):score_records(self.corpus,rows)

    def test_exact_mcnemar(self):
        self.assertEqual(_binom_two_sided(0,0),1.)
        self.assertEqual(_binom_two_sided(10,0),2/1024)
        self.assertEqual(_binom_two_sided(4,2),1.)

    def test_bootstrap_reproducible(self):
        a=_paired_ci([1,0,-1,1]*8)
        self.assertEqual(a,_paired_ci([1,0,-1,1]*8))
        self.assertEqual(len(a),2)

    def test_paid_call_opt_in(self):
        with self.assertRaises(ValueError):run_live(self.corpus,'openai','mock',limit=1)

    def test_mocked_three_call_trial(self):
        reply=ModelReply('openai','mock','{"status":"satisfied"}',9,4,6)
        with patch('aeon_link.research_eval.ask_model',return_value=reply) as api:
            r=run_live(self.corpus,'openai','mock',limit=2,confirmed_cost=True)
        self.assertEqual(api.call_count,6)
        self.assertEqual(r['analysis']['paired_cases'],2)

    def test_api_failure_counted(self):
        with patch('aeon_link.research_eval.ask_model',side_effect=ProviderError('blocked')):
            r=run_live(self.corpus,'openai','mock',limit=1,confirmed_cost=True)
        self.assertEqual(len(r['observations']),3)
        self.assertEqual(sum(x['predicted']=='error' for x in r['observations']),3)

if __name__=='__main__':unittest.main()

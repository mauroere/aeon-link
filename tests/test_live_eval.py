import unittest
from unittest.mock import patch
from aeon_link.live_eval import benchmark_cases, prompt_for,extract_status,run_live,score_live
from aeon_link.providers import ModelReply,ProviderError

class LiveEvaluationTest(unittest.TestCase):
    def test_36_fixed_cases(self):
        contract,cases=benchmark_cases()
        self.assertEqual(len(cases),36)
        self.assertEqual((contract,cases),benchmark_cases())
        self.assertTrue(all(x['expected'] in ('satisfied','violated','incomplete') for x in cases))
    def test_methods_share_contract_and_state(self):
        c,cases=benchmark_cases()
        for method in ('plain-json','aeon-semantic'):
            p=prompt_for(method,c,cases[0])
            self.assertIn('"dns"',p)
            self.assertIn('"read"',p)
    def test_exact_json_only(self):
        self.assertEqual(extract_status('{"status":"violated"}'),'violated')
        self.assertEqual(extract_status('```json\n{"status":"violated"}\n```'),'error')
        self.assertEqual(extract_status('{"status":"violated","extra":1}'),'error')
    def test_mocked_provider_36_calls_for_18_cases(self):
        with patch('aeon_link.live_eval.ask_model',return_value=ModelReply('openai','mock','{"status":"satisfied"}',10,3,1)) as api:
            report=run_live('openai','mock',limit=18)
        self.assertEqual(api.call_count,36)
        self.assertEqual(report['analysis']['paired_cases'],18)
        self.assertEqual(len(report['records']),36)
    def test_unpaired_fails(self):
        with self.assertRaises(ValueError):score_live([{'provider':'a','model':'b','case_id':'1','method':'plain-json','expected':'violated','predicted':'violated'}])
    def test_errors_are_incorrect(self):
        with patch('aeon_link.live_eval.ask_model',side_effect=ProviderError('offline')):
            report=run_live('gemini','mock',limit=1)
        self.assertEqual(report['analysis']['accuracies']['aeon-semantic'],0)
        self.assertEqual(report['analysis']['accuracies']['plain-json'],0)

if __name__=='__main__':unittest.main()

import unittest
from aeon_link.benchmark import score_records,BenchmarkError


def row(method,cid,expected='satisfied',predicted='satisfied',latency=100,tokens=10):
    return {'method':method,'case_id':cid,'expected':expected,'predicted':predicted,'latency_ms':latency,'tokens':tokens}

class BenchmarkTests(unittest.TestCase):
    def test_paired_baseline_score(self):
        records=[row('plain','c1',predicted='error'),row('aeon','c1'),row('aeon','c2','violated','violated'),row('plain','c2','violated','satisfied')]
        result=score_records(records)
        self.assertEqual(result['paired_case_count'],2)
        self.assertEqual(result['methods']['aeon']['accuracy'],1.0)
        self.assertEqual(result['methods']['plain']['explicit_errors'],1)
        self.assertEqual(result['methods']['plain']['accuracy'],0.0)
    def test_unpaired_cases_fail(self):
        with self.assertRaises(BenchmarkError):score_records([row('a','x'),row('b','y')])
    def test_expected_conflict_fails(self):
        with self.assertRaises(BenchmarkError):score_records([row('a','x'),row('b','x','violated')])
    def test_duplicate_case_fails(self):
        with self.assertRaises(BenchmarkError):score_records([row('a','x'),row('a','x')])
    def test_missing_metrics_fails(self):
        x=row('a','x');x.pop('tokens')
        with self.assertRaises(BenchmarkError):score_records([x])
    def test_float_latency_fails(self):
        with self.assertRaises(BenchmarkError):score_records([row('a','x',latency=0.1)])
    def test_empty_fails(self):
        with self.assertRaises(BenchmarkError):score_records([])
    def test_no_hidden_dropped_errors(self):
        out=score_records([row('a','1',predicted='error'),row('a','2',predicted='error')])
        self.assertEqual(out['methods']['a']['cases'],2)
        self.assertEqual(out['methods']['a']['incorrect_or_error'],2)

if __name__=='__main__': unittest.main()

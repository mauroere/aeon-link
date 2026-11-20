import copy
import unittest
from aeon_link.evidence_graph import PROFILE, validate_graph, analyze_graph, GraphError


def example():
    return {'profile': PROFILE, 'nodes': [
        {'id': 'ping', 'kind': 'evidence'},
        {'id': 'trace', 'kind': 'evidence'},
        {'id': 'c1', 'kind': 'claim', 'subject': 'link', 'predicate': 'reachable', 'value': True, 'context': 'primary'},
        {'id': 'c2', 'kind': 'claim', 'subject': 'link', 'predicate': 'reachable', 'value': False, 'context': 'primary'},
        {'id': 'c3', 'kind': 'claim', 'subject': 'route', 'predicate': 'healthy', 'value': True},
    ], 'edges': [
        {'from': 'ping', 'to': 'c1', 'type': 'supports'},
        {'from': 'trace', 'to': 'c1', 'type': 'refutes'},
        {'from': 'ping', 'to': 'c2', 'type': 'supports'},
        {'from': 'c1', 'to': 'c3', 'type': 'depends_on'},
    ]}


class GraphTests(unittest.TestCase):
    def test_no_implicit_trust(self):
        report = analyze_graph(example())
        self.assertEqual(report['claim_results']['c1']['status'], 'unresolved')
        self.assertEqual(report['claim_results']['c2']['status'], 'ungrounded')
    def test_support_link(self):
        report = analyze_graph(example(), trusted_evidence_ids=['ping'])
        self.assertEqual(report['claim_results']['c2']['status'], 'linked')
        self.assertEqual(report['claim_results']['c1']['status'], 'unresolved')
    def test_refutation(self):
        report = analyze_graph(example(), trusted_evidence_ids=['trace'])
        self.assertEqual(report['claim_results']['c1']['status'], 'contested')
    def test_conflicting_values_detected(self):
        self.assertEqual(analyze_graph(example())['potential_contradictions'], [['c1', 'c2']])
    def test_context_isolation(self):
        g = example(); g['nodes'][3]['context'] = 'backup'
        self.assertEqual(analyze_graph(g)['potential_contradictions'], [])
    def test_reject_cycle(self):
        g = example(); g['edges'].append({'from': 'c3', 'to': 'c1', 'type': 'depends_on'})
        with self.assertRaises(GraphError):
            validate_graph(g)
    def test_reject_untrusted_id(self):
        with self.assertRaises(GraphError):
            analyze_graph(example(), trusted_evidence_ids=['unknown'])
    def test_reject_duplicate_edge(self):
        g = example(); g['edges'].append(copy.deepcopy(g['edges'][0]))
        with self.assertRaises(GraphError): validate_graph(g)
    def test_reject_invalid_support_direction(self):
        g = example(); g['edges'][0]['from'] = 'c1'
        with self.assertRaises(GraphError): validate_graph(g)
    def test_reject_claim_self_attestation(self):
        g = example(); g['nodes'][0]['trusted'] = True
        with self.assertRaises(GraphError): validate_graph(g)

if __name__ == '__main__': unittest.main()

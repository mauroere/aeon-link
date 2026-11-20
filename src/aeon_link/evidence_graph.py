"""AEON-Link 0.4: deterministic evidence-relationship graph, not a truth engine.

Sources and evidence assertions are untrusted unless an external verifier provides
trusted evidence IDs. Graph relationships are claims about relationships, not
cryptographically or epistemologically proven conclusions.
"""
from __future__ import annotations

from .canonical import canonical_bytes, digest, CanonicalizationError

PROFILE = 'aeon.evidence.graph/0.1'
MAX_NODES = 128
MAX_EDGES = 256
KINDS = frozenset({'claim', 'evidence'})
RELATIONS = frozenset({'supports', 'refutes', 'depends_on'})


class GraphError(ValueError):
    pass


def validate_graph(graph: dict) -> dict:
    try:
        canonical_bytes(graph)
    except (CanonicalizationError, TypeError) as exc:
        raise GraphError(f'Unsupported graph encoding: {exc}') from exc
    if not isinstance(graph, dict) or set(graph) != {'profile', 'nodes', 'edges'} or graph['profile'] != PROFILE:
        raise GraphError('Unsupported graph profile or keys')
    nodes = graph['nodes']
    edges = graph['edges']
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES:
        raise GraphError('Node count exceeds allowed limits')
    if not isinstance(edges, list) or len(edges) > MAX_EDGES:
        raise GraphError('Edge count exceeds allowed limits')
    by_id = {}
    for node in nodes:
        if not isinstance(node, dict) or set(node) - {'id', 'kind', 'subject', 'predicate', 'value', 'context'}:
            raise GraphError('Invalid node keys')
        id_, kind = node.get('id'), node.get('kind')
        if not isinstance(id_, str) or not 1 <= len(id_) <= 128 or not isinstance(kind, str) or kind not in KINDS or id_ in by_id:
            raise GraphError('Malformed or duplicate node')
        if kind == 'claim':
            if not {'subject', 'predicate', 'value'}.issubset(node):
                raise GraphError('Claim must have a subject, predicate and value')
            if not isinstance(node['subject'], str) or not node['subject'] or not isinstance(node['predicate'], str) or not node['predicate']:
                raise GraphError('Invalid subject/predicate')
            if 'context' in node and not isinstance(node['context'], str):
                raise GraphError('Context must be a string')
        else:
            if set(node) != {'id', 'kind'}:
                raise GraphError('Evidence node cannot self-attest to trust')
        by_id[id_] = node
    refs = set()
    deps = {key: [] for key, node in by_id.items() if node['kind'] == 'claim'}
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {'from', 'to', 'type'}:
            raise GraphError('Malformed relation')
        f, t, rel = edge['from'], edge['to'], edge['type']
        if not isinstance(f, str) or not isinstance(t, str) or f not in by_id or t not in by_id or not isinstance(rel, str) or rel not in RELATIONS:
            raise GraphError('Invalid relation endpoint/type')
        if (f, t, rel) in refs:
            raise GraphError('Duplicate relation')
        refs.add((f, t, rel))
        if rel == 'depends_on':
            if by_id[f]['kind'] != 'claim' or by_id[t]['kind'] != 'claim':
                raise GraphError('Only claims can depend on claims')
            deps[f].append(t)
        else:
            if by_id[f]['kind'] != 'evidence' or by_id[t]['kind'] != 'claim':
                raise GraphError('Support/refutation edges must point from evidence to claims')
    seen, visiting = set(), set()
    def walk(n):
        if n in visiting:
            raise GraphError('Cyclic dependency')
        if n in seen:
            return
        visiting.add(n)
        for other in deps[n]:
            walk(other)
        visiting.remove(n)
        seen.add(n)
    for n in deps:
        walk(n)
    return graph


def analyze_graph(graph: dict, *, trusted_evidence_ids=()) -> dict:
    """Trusted IDs MUST come from an external verifier, never untrusted graph data."""
    validate_graph(graph)
    nodes = {n['id']: n for n in graph['nodes']}
    if not isinstance(trusted_evidence_ids, (list, tuple, set, frozenset)):
        raise GraphError('Trusted evidence IDs must be a collection')
    if any(not isinstance(i, str) for i in trusted_evidence_ids):
        raise GraphError('Evidence IDs must be strings')
    trusted = set(trusted_evidence_ids)
    if any(not isinstance(i, str) or i not in nodes or nodes[i]['kind'] != 'evidence' for i in trusted):
        raise GraphError('Unknown/untrusted evidence identity')
    incoming = {}
    dependencies = {}
    for e in graph['edges']:
        if e['type'] == 'depends_on':
            dependencies.setdefault(e['from'], []).append(e['to'])
        else:
            incoming.setdefault(e['to'], []).append(e)
    result = {}
    def check(cid):
        if cid in result:
            return result[cid]
        related = incoming.get(cid, [])
        supports = sorted(e['from'] for e in related if e['type'] == 'supports' and e['from'] in trusted)
        refutes = sorted(e['from'] for e in related if e['type'] == 'refutes' and e['from'] in trusted)
        missing = sorted(dep for dep in dependencies.get(cid, ()) if check(dep)['status'] != 'linked')
        if refutes:
            status = 'contested'
        elif missing:
            status = 'unresolved'
        elif supports:
            status = 'linked'
        else:
            status = 'ungrounded'
        result[cid] = {'status': status, 'verified_support_ids': supports,
                       'verified_refutation_ids': refutes, 'unresolved_dependencies': missing}
        return result[cid]
    for n in nodes.values():
        if n['kind'] == 'claim':
            check(n['id'])
    contradictions = []
    groups = {}
    for node in nodes.values():
        if node['kind'] != 'claim':
            continue
        key = (node['subject'], node['predicate'], node.get('context', ''))
        groups.setdefault(key, []).append(node)
    for group in groups.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if digest(a['value']) != digest(b['value']):
                    contradictions.append([a['id'], b['id']])
    return {'profile': PROFILE, 'claim_results': {k: result[k] for k in sorted(result)},
            'potential_contradictions': sorted(contradictions),
            'note': 'Trusted references are not proof that propositions are true.'}

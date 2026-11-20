"""Paired, auditable *experimental* LLM evaluation harness.

Identical cases, exact-model and fixed prompt versions; balanced trial order.
This does not compare ÆON-Link with A2A/MCP as wire protocols: they are
orthogonal. It compares two semantic payload presentations using one API.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import asdict
from .canonical import digest
from .providers import ask_model, ProviderError
from .semantics import PROFILE, evaluate_contract

METHODS = ('plain-json', 'aeon-semantic')

def benchmark_cases(seed: int = 917) -> tuple[dict, list[dict]]:
    contract = {'profile': PROFILE, 'allowed_actions': ['observe', 'read'], 'clauses': [
        {'id': 'dns', 'mode': 'require', 'path': '/dns/resolved', 'op': 'eq', 'value': True},
        {'id': 'locked', 'mode': 'forbid', 'path': '/permissions/write', 'op': 'eq', 'value': True},
        {'id': 'latency', 'mode': 'require', 'path': '/latency_ms', 'op': 'lte', 'value': 120},
    ]}
    rng = random.Random(seed)
    cases = []
    for i in range(36):
        state = {'dns': {'resolved': rng.choice([True, False])},
                 'permissions': {'write': rng.choice([False, True])},
                 'latency_ms': rng.choice([30, 120, 180])}
        if i % 7 == 0:
            state.pop('latency_ms')
        if i % 9 == 0:
            state['dns'].pop('resolved')
        action = rng.choice(['read', 'observe', 'execute'])
        expected = evaluate_contract(contract, state, action)['status']
        cases.append({'case_id': f'test_{i:03d}', 'state': state, 'action': action, 'expected': expected})
    return contract, cases


def prompt_for(method: str, contract: dict, case: dict) -> str:
    if method not in METHODS:
        raise ValueError('Unknown method')
    data = {'contract': contract, 'state': case['state'], 'action': case['action']}
    rules = ('Return ONLY one JSON object {"status":"satisfied|violated|incomplete"}. '
             'A require clause must be true; a forbid clause must be false. '
             'Missing properties in comparisons yield incomplete unless another rule is violated. '
             'Unknown action yields violated. Compare typed JSON values; never guess missing data.')
    if method == 'plain-json':
        return ('Evaluate this contract on this case. '+rules+'\n'+json.dumps(data,ensure_ascii=False,sort_keys=True))
    return ('AEON Semantic Contract profile '+PROFILE+'. Interpret the following machine-readable '+
            'rules and return an exact decision receipt status. '+rules+'\n'+json.dumps(data,ensure_ascii=False,sort_keys=True))


def extract_status(raw: str) -> str:
    try:
        parsed=json.loads(raw.strip())
    except (ValueError,TypeError):
        return 'error'
    if type(parsed) is not dict or set(parsed) != {'status'}:
        return 'error'
    return parsed['status'] if type(parsed['status']) is str and parsed['status'] in ('satisfied','violated','incomplete') else 'error'


def run_live(provider: str, model: str, *, seed: int = 917, limit: int = 36) -> dict:
    """MAKE PAID API CALLS only when the invoking operator explicitly calls this.

    No keys or provider raw text are persisted in the returned report.
    """
    if type(limit) is not int or not 1 <= limit <= 36:
        raise ValueError('Limit must be between 1 and 36')
    contract, cases = benchmark_cases(seed)
    observations = []
    for i,case in enumerate(cases[:limit]):
        for method in (METHODS if i % 2 == 0 else METHODS[::-1]):
            p = prompt_for(method,contract,case)
            try:
                reply = ask_model(provider,model,p)
                status = extract_status(reply.text)
                latency_ms = reply.latency_ms
                tokens = reply.input_tokens + reply.output_tokens if reply.input_tokens is not None and reply.output_tokens is not None else None
                error = status == 'error'
            except ProviderError:
                status,latency_ms,tokens,error = 'error',None,None,True
            observations.append({'provider':provider,'model':model,'case_id':case['case_id'],
                'method':method,'expected':case['expected'],'predicted':status,
                'latency_ms':latency_ms,'total_tokens':tokens,'error':error})
    return {'schema':'aeon.live.eval/0.1','dataset_digest':digest({'contract':contract,'cases':cases[:limit]}),
            'seed':seed,'num_cases':limit,'provider':provider,'model':model,
            'protocol_baseline':'none; payload only',
            'limitations':['No claims of A2A/MCP superiority','Automated labels only; no independent grading'],
            'records':observations,'analysis':score_live(observations)}


def score_live(records: list[dict]) -> dict:
    """Paired comparisons with *descriptive*, not statistical-superiority claim."""
    grouped = {}
    for r in records:
        key=(r['provider'],r['model'],r['case_id'])
        if r['method'] not in METHODS or r['predicted'] not in ('satisfied','violated','incomplete','error'):
            raise ValueError('Invalid results')
        if key not in grouped: grouped[key]={}
        if r['method'] in grouped[key]:raise ValueError('Duplicate row')
        grouped[key][r['method']]=r
    if not grouped or any(set(g)!=set(METHODS) or len({r['expected'] for r in g.values()})!=1 for g in grouped.values()):
        raise ValueError('Unpaired rows or inconsistent labels')
    total=len(grouped)
    correct = {m:sum(g[m]['predicted']==g[m]['expected'] for g in grouped.values()) for m in METHODS}
    aeon_only = sum(g['aeon-semantic']['predicted']==g['aeon-semantic']['expected'] and g['plain-json']['predicted']!=g['plain-json']['expected'] for g in grouped.values())
    plain_only = sum(g['plain-json']['predicted']==g['plain-json']['expected'] and g['aeon-semantic']['predicted']!=g['aeon-semantic']['expected'] for g in grouped.values())
    return {'paired_cases':total,'accuracies':{m:round(correct[m]/total,4) for m in METHODS},
            'discordant':{'aeon_only_correct':aeon_only,'plain_only_correct':plain_only},
            'accuracy_difference':round((correct['aeon-semantic']-correct['plain-json'])/total,4),
            'conclusion':'Observational paired sample; no generalizable superiority claim'}

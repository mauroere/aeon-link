"""Independent scoring of recorded agent decisions, without network/model calls.

This module deliberately never scores data not present in its input. It checks
that the same problems were evaluated by each method, and does not claim that
its confidence intervals establish protocol superiority.
"""
from __future__ import annotations
from collections import defaultdict
from math import sqrt
from .canonical import canonical_bytes, CanonicalizationError

STATUSES = frozenset({'satisfied','violated','incomplete'})
MAX_ROWS = 10000

class BenchmarkError(ValueError):
    pass


def _wilson(successes:int,n:int,z:float=1.96)->list[float]:
    if not n:
        return [0.0,0.0]
    p=successes/n
    denom=1+z*z/n
    center=(p+z*z/(2*n))/denom
    spread=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return [round(max(0,center-spread),4),round(min(1,center+spread),4)]


def score_records(records:list[dict])->dict:
    """Each row has: method, case_id, expected, predicted, latency_ms, tokens.

    A prediction equal to 'error' is counted as incorrect, not excluded.
    Tests do not infer model behavior or invent token/latency values.
    """
    try: canonical_bytes(records)
    except (CanonicalizationError,TypeError) as exc: raise BenchmarkError('Unsafe benchmark input') from exc
    if not isinstance(records,list) or not 1<=len(records)<=MAX_ROWS:
        raise BenchmarkError('Expected 1..10000 records')
    groups=defaultdict(dict)
    for row in records:
        if not isinstance(row,dict) or set(row)!={'method','case_id','expected','predicted','latency_ms','tokens'}:
            raise BenchmarkError('Invalid benchmark fields')
        method,cid=row['method'],row['case_id']
        if any(not isinstance(v,str) or not 1<=len(v)<=128 for v in (method,cid)):
            raise BenchmarkError('Invalid method/case ID')
        if not isinstance(row['expected'],str) or not isinstance(row['predicted'],str) or row['expected'] not in STATUSES or row['predicted'] not in STATUSES|{'error'}:
            raise BenchmarkError('Invalid benchmark labels')
        for k in ('latency_ms','tokens'):
            v=row[k]
            if type(v) is not int or v<0:
                raise BenchmarkError('Latency/token counts must be nonnegative integers')
        if cid in groups[method]:
            raise BenchmarkError('Duplicate case for one method')
        groups[method][cid]=row
    methods=sorted(groups)
    case_ids=set(groups[methods[0]])
    if any(set(groups[m])!=case_ids for m in methods):
        raise BenchmarkError('Unpaired evaluation cases across methods')
    for cid in case_ids:
        if len({groups[m][cid]['expected'] for m in methods})!=1:
            raise BenchmarkError('Disagreement about ground truth between methods')
    result={}
    for method in methods:
        rows=list(groups[method].values())
        total=len(rows)
        correct=sum(x['predicted']==x['expected'] for x in rows)
        errors=sum(x['predicted']=='error' for x in rows)
        result[method]={
            'cases':total,
            'correct':correct,
            'incorrect_or_error':total-correct,
            'explicit_errors':errors,
            'accuracy':round(correct/total,4),
            'accuracy_wilson_95':_wilson(correct,total),
            'mean_latency_ms':round(sum(x['latency_ms'] for x in rows)/total,2),
            'mean_tokens':round(sum(x['tokens'] for x in rows)/total,2),
        }
    return {'schema':'aeon.semantic.benchmark/0.1','paired_case_count':len(case_ids),
            'methods':result,'note':'Recorded-data benchmark only; not a causal superiority claim.'}

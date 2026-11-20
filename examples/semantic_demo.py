"""Self-contained semantic challenge demo; no API credentials, no LLM calls."""
import json
from aeon_link import (SEMANTIC_PROFILE, evaluate_contract, counterfactual_cases,
    create_challenge, respond_to_challenge, score_challenge)

contract = {'profile': SEMANTIC_PROFILE, 'allowed_actions': ['read', 'observe'], 'clauses': [
    {'id':'dns', 'mode':'require', 'path':'/dns/resolved', 'op':'eq','value':True},
    {'id':'write_block', 'mode':'forbid', 'path':'/permissions/write', 'op':'eq','value':True},
]}
baseline = {'dns':{'resolved':True},'permissions':{'write':False}}
probes = counterfactual_cases(contract, baseline, 'observe')
public, private_key = create_challenge(contract, probes)
answer = respond_to_challenge(contract,public)
result = score_challenge(private_key,answer)
print(json.dumps({'cases':len(probes),'benchmark':result,'note':'Reference solver, not a real LLM'},indent=2))

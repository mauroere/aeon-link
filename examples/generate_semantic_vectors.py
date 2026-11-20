"""Deterministic, independently checked Python -> JS semantic test vectors."""
import json
from pathlib import Path
from aeon_link.semantics import (PROFILE, contract_fingerprint, evaluate_contract)

contract = {'profile': PROFILE, 'allowed_actions': ['observe', 'read'], 'clauses': [
    {'id': 'dns', 'mode': 'require', 'op': 'eq', 'path': '/dns/resolved', 'value': True},
    {'id': 'no_changes', 'mode': 'forbid', 'op': 'eq', 'path': '/changes/config', 'value': True},
    {'id': 'packet_loss', 'mode': 'require', 'op': 'lte', 'path': '/metrics/loss', 'value': 1},
]}
base = {'dns': {'resolved': True}, 'changes': {'config': False}, 'metrics': {'loss': 0}}
cases = [
    {'id':'ok','action':'observe','state':base},
    {'id':'wrong_dns','action':'observe','state':{'dns':{'resolved':False},'changes':{'config':False},'metrics':{'loss':0}}},
    {'id':'bad_loss','action':'read','state':{'dns':{'resolved':True},'changes':{'config':False},'metrics':{'loss':2}}},
    {'id':'missing_loss','action':'observe','state':{'dns':{'resolved':True},'changes':{'config':False}}},
    {'id':'write','action':'write','state':base},
    {'id':'config_change','action':'observe','state':{'dns':{'resolved':True},'changes':{'config':True},'metrics':{'loss':0}}},
    {'id':'bool_is_not_int','action':'observe','state':{'dns':{'resolved':True},'changes':{'config':False},'metrics':{'loss':True}}},
]
result={'profile':PROFILE,'contract':contract,'contract_digest':contract_fingerprint(contract),
        'cases':[dict(c,expected=evaluate_contract(contract,c['state'],c['action'])) for c in cases]}
Path(__file__).resolve().parents[1].joinpath('fixtures','semantic-vectors.json').write_text(
    json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

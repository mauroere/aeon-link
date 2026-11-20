"""Explicit paid-network opt-in; API keys must be set outside the repository."""
import argparse
import json
from pathlib import Path
from aeon_link.live_eval import run_live, benchmark_cases, score_live

p=argparse.ArgumentParser(description='Paired live evaluation; model API calls may incur charges')
p.add_argument('--provider',choices=['openai','anthropic','gemini'],required=True)
p.add_argument('--model',required=True)
p.add_argument('--limit',type=int,default=12)
p.add_argument('--seed',type=int,default=917)
p.add_argument('--output',type=Path,default=Path('aeon-live-results.json'))
p.add_argument('--i-accept-api-costs',action='store_true')
a=p.parse_args()
if not a.i_accept_api_costs:
    p.error('Live calls are disabled unless --i-accept-api-costs is supplied')
report=run_live(a.provider,a.model,limit=a.limit,seed=a.seed)
a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(report['analysis'],indent=2))

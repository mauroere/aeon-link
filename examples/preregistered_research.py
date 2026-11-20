"""Create versioned corpus, score offline observations, or explicitly run paid pilot."""
import argparse
import json
from pathlib import Path
from aeon_link.research_eval import (make_cases,dataset_digest,score_records,run_live,VERSION)

p=argparse.ArgumentParser(description='ÆON-Link three-method paired semantic research')
p.add_argument('command',choices=('generate','score','live'))
p.add_argument('--seed',type=int,default=20261120)
p.add_argument('--split',choices=('pilot','evaluation'),default='pilot')
p.add_argument('--output',type=Path,default=Path('aeon-research.json'))
p.add_argument('--observations',type=Path)
p.add_argument('--provider',choices=('openai','anthropic','gemini'))
p.add_argument('--model')
p.add_argument('--limit',type=int,default=5)
p.add_argument('--i-accept-api-costs',action='store_true')
a=p.parse_args()
corpus=make_cases(seed=a.seed)
if a.command=='generate':
    result=corpus
elif a.command=='score':
    if not a.observations:p.error('--observations required')
    raw=json.loads(a.observations.read_text('utf-8'))
    rows=raw['observations'] if type(raw) is dict else raw
    result=score_records(corpus,rows,split=a.split)
else:
    if not a.i_accept_api_costs:p.error('Live calls require --i-accept-api-costs')
    if not a.provider or not a.model:p.error('Live calls require --provider and --model')
    result=run_live(corpus,a.provider,a.model,split=a.split,limit=a.limit,confirmed_cost=True)
a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'schema':VERSION,'digest':dataset_digest(corpus),'output':str(a.output),'command':a.command},indent=2))

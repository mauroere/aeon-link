"""Two commercial model relay; never executes the tested action."""
import argparse,json
from aeon_link.relay import relay_once

p=argparse.ArgumentParser(description='Explicitly paid, read-only LLM A->B semantic relay')
p.add_argument('--provider-a',required=True,choices=['openai','anthropic','gemini'])
p.add_argument('--model-a',required=True)
p.add_argument('--provider-b',required=True,choices=['openai','anthropic','gemini'])
p.add_argument('--model-b',required=True)
p.add_argument('--action',choices=['read','write','execute'],default='write')
p.add_argument('--i-accept-api-costs',action='store_true')
a=p.parse_args()
if not a.i_accept_api_costs:p.error('Two commercial API calls are disabled without --i-accept-api-costs')
result=relay_once(a.provider_a,a.model_a,a.provider_b,a.model_b,action=a.action)
print(json.dumps(result,indent=2,ensure_ascii=False))

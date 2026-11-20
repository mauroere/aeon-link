"""Illustrative, fabricated test records—not observations of any LLM/provider."""
import json
from aeon_link.benchmark import score_records

def record(method,case,expected,predicted,latency,tokens):
    return dict(method=method,case_id=case,expected=expected,predicted=predicted,
                latency_ms=latency,tokens=tokens)
records=[
    record('plain_json','demo1','satisfied','satisfied',120,190),
    record('plain_json','demo2','violated','satisfied',140,200),
    record('aeon_link','demo1','satisfied','satisfied',170,280),
    record('aeon_link','demo2','violated','violated',180,290),
]
print(json.dumps(score_records(records),indent=2))
print('ALL INPUT ROWS ARE SYNTHETIC. THESE ARE NOT MODEL BENCHMARK RESULTS.')

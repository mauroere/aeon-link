"""Produces deterministic Python-side envelope acceptance vectors for Node parity."""
import copy
import json
import random
import sys
from aeon_link import message, validate_envelope, ProtocolError
R=random.Random(3005)

def baseline():
    return message('task','alpha','beta',{
      'objective':{'id':'case','text':'Observe','success_criteria':['Report']},
      'constraints':{'read_only':True},'action':'observe',
      'claims':[{'id':'c','status':'hypothesis','text':'Possibly unreachable','evidence_ids':[]}],
      'evidence':[{'id':'e','source_uri':'urn:example:source','observed_at':'2026-11-20T14:00:00Z'}]})

def main():
    row=[]
    cases=[]
    x=baseline();cases.append(('baseline',x))
    for field in ('sender','recipient'):
        for length in (0,1,255,256,257,300):
            y=copy.deepcopy(x);y[field]='a'*length;cases.append((f'{field}_{length}',y))
    timestamps=['2026-11-20T14:00:00Z','2026-15-99T25:61:00Z','not a timestamp',
                '2026-11-20','2026-02-29T08:01:59Z','2028-02-29T08:01:59Z',
                '2026-01-01T00:00:00+99:99','2026-02-30T00:00:00Z']
    for t in timestamps:
        y=copy.deepcopy(x);y['body']['evidence'][0]['observed_at']=t;cases.append((f'date_{len(cases)}',y))
    for i in range(100):
        y=copy.deepcopy(x)
        field=R.choice(['sender','recipient','action','status','claim_id','evidence_id','sha','max_risk','read_only'])
        v=R.choice([None,True,False,1,0,'','x'*R.randrange(257,400),'weird',[],{},'é🚀'])
        if field in ('sender','recipient'):y[field]=v
        elif field=='action':y['body']['action']=v
        elif field=='status':y['body']['claims'][0]['status']=v
        elif field=='claim_id':y['body']['claims'][0]['id']=v
        elif field=='evidence_id':y['body']['evidence'][0]['id']=v
        elif field=='sha':y['body']['evidence'][0]['sha256']=v
        elif field=='max_risk':y['body']['constraints']['max_risk']=v
        else:y['body']['constraints']['read_only']=v
        cases.append((f'random_{i}',y))
    for name,obj in cases:
        try:validate_envelope(obj);expected=True
        except (ProtocolError,ValueError,TypeError):expected=False
        row.append({'case':name,'envelope':obj,'accepted':expected})
    json.dump(row,sys.stdout,ensure_ascii=True,separators=(',',':'))
if __name__=='__main__':main()

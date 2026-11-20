"""Deterministic Python decision receipts for independent Node verification."""
import json
import sys
from aeon_link.receipts import make_decision_receipt
from aeon_link.semantics import PROFILE

C={'profile':PROFILE,'allowed_actions':['read','observe'],'clauses':[
 {'id':'check','mode':'require','path':'/ok','op':'eq','value':True},
 {'id':'limit','mode':'require','path':'/level','op':'lte','value':10},
 {'id':'ban','mode':'forbid','path':'/blocked','op':'eq','value':True}]}
CASES=[({'ok':True,'level':2,'blocked':False},'read'),
       ({'ok':True,'level':12,'blocked':False},'read'),
       ({'ok':True,'level':2},'read'),
       ({'ok':True,'level':2,'blocked':False},'execute'),
       ({'ok':False,'level':2,'blocked':True},'observe'),
       ({'ok':True,'level':10,'blocked':False,'memo':'é 🚀'},'read'),
       ({'ok':True,'level':-1,'blocked':False},'read')]
json.dump([{'contract':C,'state':state,'action':action,
            'receipt':make_decision_receipt(C,state,action)} for state,action in CASES],
          sys.stdout,separators=(',',':'),ensure_ascii=True)

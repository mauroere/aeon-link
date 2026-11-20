"""ÆON-Link 0.2 minimal reference: semantics, negotiation, local authorization.
Experimental; does not connect LLMs or verify source truth.
"""
import json, hashlib, uuid
from dataclasses import dataclass

VERSION="0.2.0"
ONTOLOGY="urn:aeon-link:ontology:core:0.2.0"
FEATURES=frozenset({"claims.v1","evidence.refs.v1","objective.ack.v1"})

class ProtocolError(ValueError): pass

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def validate(msg):
    if not isinstance(msg,dict) or msg.get("protocol")!="aeon-link" or msg.get("version")!=VERSION or msg.get("ontology")!=ONTOLOGY:
        raise ProtocolError("Unsupported protocol/version/ontology")
    if msg.get("kind") not in ("hello","task","result"): raise ProtocolError("Invalid kind")
    if not all(isinstance(msg.get(k),str) and msg[k] for k in ("sender","recipient","message_id")): raise ProtocolError("Invalid identity")
    b=msg.get("body")
    if not isinstance(b,dict): raise ProtocolError("Invalid body")
    if msg["kind"]=="hello":
        if not all(isinstance(b.get(k),list) for k in ("versions","ontologies","features")): raise ProtocolError("Invalid hello")
    elif msg["kind"]=="task":
        if not isinstance(b.get("objective"),dict) or not isinstance(b.get("constraints"),dict): raise ProtocolError("Invalid objective")
        if b.get("action") not in ("observe","read","write","execute"): raise ProtocolError("Invalid action")
        ev=b.get("evidence",[]);claims=b.get("claims",[])
        if not isinstance(ev,list) or not isinstance(claims,list): raise ProtocolError("Invalid claims/evidence")
        ids=[e["id"] for e in ev]
        if len(ids)!=len(set(ids)): raise ProtocolError("Repeated evidence ID")
        for c in claims:
            if c.get("status") not in ("fact","hypothesis","unknown"): raise ProtocolError("Invalid epistemic status")
            if not set(c.get("evidence_ids",[])).issubset(set(ids)): raise ProtocolError("Missing evidence reference")
            if c["status"]=="fact" and not c.get("evidence_ids"): raise ProtocolError("FACT requires referenced evidence")
        if b["constraints"].get("read_only") and b["action"] in ("write","execute"): raise ProtocolError("Read-only policy violated")
    return msg

def message(kind,sender,recipient,body):
    return validate({"protocol":"aeon-link","version":VERSION,"ontology":ONTOLOGY,
                     "message_id":str(uuid.uuid4()),"kind":kind,
                     "sender":sender,"recipient":recipient,"body":body})

def hello(sender,recipient,features=FEATURES):
    return message("hello",sender,recipient,{"versions":[VERSION],"ontologies":[ONTOLOGY],"features":sorted(features)})

@dataclass(frozen=True)
class Agreement:
    version:str
    ontology:str
    features:frozenset

def negotiate(a,b,required_features=()):
    validate(a);validate(b)
    if a["kind"]!="hello" or b["kind"]!="hello" or a["sender"]!=b["recipient"] or b["sender"]!=a["recipient"]:
        raise ProtocolError("Incompatible participants")
    if VERSION not in set(a["body"]["versions"])&set(b["body"]["versions"]):raise ProtocolError("No common version")
    if ONTOLOGY not in set(a["body"]["ontologies"])&set(b["body"]["ontologies"]):raise ProtocolError("No common ontology")
    feats=frozenset(a["body"]["features"])&frozenset(b["body"]["features"])
    if not set(required_features).issubset(feats):raise ProtocolError("Missing features")
    return Agreement(VERSION,ONTOLOGY,feats)

@dataclass(frozen=True)
class LocalPolicy:
    verified_sender:str
    allowed_actions:frozenset

def authorize(task,policy):
    validate(task)
    if task["kind"]!="task" or task["sender"]!=policy.verified_sender or task["body"]["action"] not in policy.allowed_actions:
        raise ProtocolError("Host authorization denied")
    return True

def acknowledge(task,responder):
    validate(task)
    if task["kind"]!="task" or task["recipient"]!=responder: raise ProtocolError("Wrong recipient")
    b=task["body"]
    return message("result",responder,task["sender"],{
        "in_reply_to":task["message_id"],"objective_digest":digest(b["objective"]),
        "constraints_digest":digest(b["constraints"]),"status":"needs_clarification",
        "actions_executed":[]})

def verify_ack(task,result):
    validate(task);validate(result)
    b=result["body"]
    if result["kind"]!="result" or result["sender"]!=task["recipient"] or result["recipient"]!=task["sender"] or b.get("in_reply_to")!=task["message_id"] or b.get("objective_digest")!=digest(task["body"]["objective"]) or b.get("constraints_digest")!=digest(task["body"]["constraints"]):
        raise ProtocolError("Acknowledgment mismatch")
    return True

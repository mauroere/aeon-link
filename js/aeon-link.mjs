/** AEON-Link 0.2.0 minimal dependency-free Node.js reference (experimental).
 * Manual validation is an interoperable subset, NOT full JSON Schema validation.
 */
import { randomUUID } from 'node:crypto';

export const VERSION = '0.4.0';
export const ONTOLOGY = 'urn:aeon-link:ontology:core:0.4.0';
import {canonicalBytes, digest} from './canonical.mjs';
export {canonicalBytes, digest} from './canonical.mjs';
export const FEATURES = ['claims.v1', 'evidence.refs.v1', 'objective.ack.v1', 'semantic.contract.v1', 'evidence.graph.v1'];

export class ProtocolError extends Error {}

const isObject = x => !!x && typeof x === 'object' && !Array.isArray(x);
const requireKeys = (o, keys) => {
  if (!isObject(o)) throw new ProtocolError('Expected object');
  if (keys.some(k => !(k in o))) throw new ProtocolError('Missing required key');
};
const onlyKeys = (o, keys) => {
  if (Object.keys(o).some(k => !keys.includes(k))) throw new ProtocolError('Unexpected key');
};
const str = x => typeof x === 'string' && x.length > 0;
const lengthCP = s => [...s].length;
function validRfc3339(s) {
  if(typeof s !== 'string') return false;
  const m = /^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?([Zz]|[+-]\d{2}:\d{2})$/.exec(s);
  if(!m) return false;
  const [year,month,day,hour,minute,second]=m.slice(1,7).map(Number);
  if(month<1||month>12||hour>23||minute>59||second>59) return false;
  const leap=(year%4===0 && (year%100!==0 || year%400===0));
  const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
  if(day<1||day>days[month-1]) return false;
  if(m[7].length===6){const oh=Number(m[7].slice(1,3)),om=Number(m[7].slice(4));if(oh>23||om>59)return false;}
  return true;
}
const arr = x => Array.isArray(x);
const uniq = x => new Set(x).size === x.length;
const uuid = x => typeof x === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(x);
const hash = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
function assert(test, reason) { if (!test) throw new ProtocolError(reason); }

export function validateEnvelope(m) {
  requireKeys(m, ['protocol', 'version', 'ontology', 'message_id', 'kind', 'sender', 'recipient', 'body']);
  onlyKeys(m, ['protocol', 'version', 'ontology', 'message_id', 'kind', 'sender', 'recipient', 'body']);
  assert(m.protocol === 'aeon-link' && m.version === VERSION && m.ontology === ONTOLOGY, 'Unsupported protocol/version/ontology');
  assert(uuid(m.message_id) && str(m.sender) && lengthCP(m.sender)<=256 && str(m.recipient) && lengthCP(m.recipient)<=256, 'Invalid envelope identities');
  assert(['hello','task','result','error'].includes(m.kind), 'Invalid message kind');
  const b = m.body;
  if (m.kind === 'hello') {
    requireKeys(b, ['versions','ontologies','features']);
    onlyKeys(b, ['versions','ontologies','features']);
    for (const p of ['versions','ontologies','features']) assert(arr(b[p]) && b[p].every(str) && uniq(b[p]), `Invalid ${p}`);
    assert(b.versions.length > 0 && b.ontologies.length > 0, 'Empty supported profiles');
  }
  if (m.kind === 'task') {
    requireKeys(b, ['objective','constraints','action','claims','evidence']);
    onlyKeys(b, ['objective','constraints','action','claims','evidence']);
    requireKeys(b.objective, ['id','text','success_criteria']);
    onlyKeys(b.objective, ['id','text','success_criteria']);
    assert(str(b.objective.id) && str(b.objective.text) && arr(b.objective.success_criteria) && b.objective.success_criteria.length > 0 && b.objective.success_criteria.every(str), 'Bad objective');
    requireKeys(b.constraints, ['read_only']);
    onlyKeys(b.constraints, ['read_only','max_risk']);
    assert(typeof b.constraints.read_only === 'boolean', 'Invalid read_only');
    if ('max_risk' in b.constraints) assert(['low','medium','high'].includes(b.constraints.max_risk), 'Bad risk');
    assert(['observe','propose','write','execute'].includes(b.action), 'Bad action');
    assert(!(b.constraints.read_only && ['write','execute'].includes(b.action)), 'Read-only violation');
    assert(arr(b.evidence) && arr(b.claims), 'Missing evidence/claims');
    const evidenceIds = new Set();
    for (const e of b.evidence) {
      requireKeys(e,['id','source_uri']); onlyKeys(e,['id','source_uri','sha256','observed_at']);
      assert(str(e.id) && str(e.source_uri) && !evidenceIds.has(e.id), 'Invalid/duplicate evidence');
      if ('sha256' in e) assert(hash(e.sha256),'Bad evidence hash');
      if ('observed_at' in e) assert(validRfc3339(e.observed_at), 'Invalid RFC3339 timestamp');
      evidenceIds.add(e.id);
    }
    const claimIds = new Set();
    for (const c of b.claims) {
      requireKeys(c,['id','status','text','evidence_ids']); onlyKeys(c,['id','status','text','evidence_ids']);
      assert(str(c.id) && str(c.text) && !claimIds.has(c.id), 'Bad/duplicate claim');
      assert(['fact','hypothesis','unknown'].includes(c.status) && arr(c.evidence_ids) && c.evidence_ids.every(str) && uniq(c.evidence_ids), 'Bad claim type/evidence_ids');
      assert(c.status !== 'fact' || c.evidence_ids.length > 0, 'Fact requires referenced evidence');
      assert(c.evidence_ids.every(id => evidenceIds.has(id)), 'Dangling evidence');
      claimIds.add(c.id);
    }
  }
  if (m.kind === 'result') {
    requireKeys(b,['in_reply_to','objective_id','objective_digest','constraints_digest','status','understood_objective','findings','uncertainties','actions_executed']);
    onlyKeys(b,['in_reply_to','objective_id','objective_digest','constraints_digest','status','understood_objective','findings','uncertainties','actions_executed']);
    assert(uuid(b.in_reply_to) && str(b.objective_id) && hash(b.objective_digest) && hash(b.constraints_digest), 'Bad result references');
    assert(['completed','rejected','needs_clarification'].includes(b.status) && str(b.understood_objective), 'Bad result status/objective');
    for(const key of ['findings','uncertainties','actions_executed']) assert(arr(b[key]) && b[key].every(x => typeof x === 'string'),`Bad ${key}`);
  }
  if (m.kind === 'error') {
    requireKeys(b,['code','message']); onlyKeys(b,['code','message','in_reply_to']);
    assert(str(b.code) && str(b.message) && (!('in_reply_to' in b) || uuid(b.in_reply_to)), 'Bad error body');
  }
  try {canonicalBytes(m);} catch (err) {throw new ProtocolError('Invalid canonical JSON profile: ' + err.message);}
  return m;
}

export function message(kind, sender, recipient, body) {
  return validateEnvelope({ protocol:'aeon-link', version:VERSION, ontology:ONTOLOGY,
    message_id: randomUUID(), kind, sender, recipient, body:structuredClone(body) });
}
export const hello = (sender,recipient) => message('hello',sender,recipient,{
  versions:[VERSION], ontologies:[ONTOLOGY], features:[...FEATURES]
});
export function negotiate(a,b,required=[]) {
  validateEnvelope(a);validateEnvelope(b);
  assert(a.kind==='hello' && b.kind==='hello' && a.sender===b.recipient && b.sender===a.recipient,'Invalid handshake');
  assert(a.body.versions.includes(VERSION) && b.body.versions.includes(VERSION),'Version mismatch');
  assert(a.body.ontologies.includes(ONTOLOGY) && b.body.ontologies.includes(ONTOLOGY),'Ontology mismatch');
  const common = a.body.features.filter(f=>b.body.features.includes(f));
  assert(required.every(x=>common.includes(x)),'Required feature missing');
  return { version:VERSION, ontology:ONTOLOGY, features:common.sort() };
}
export function makeAckResult(task, responder) {
  validateEnvelope(task);
  assert(task.kind==='task' && task.recipient===responder, 'Wrong recipient/task');
  return message('result',responder,task.sender,{
    in_reply_to:task.message_id, objective_id:task.body.objective.id,
    objective_digest:digest(task.body.objective), constraints_digest:digest(task.body.constraints),
    status:'needs_clarification', understood_objective:task.body.objective.text,
    findings:[], uncertainties:['No external checks or model reasoning performed'],actions_executed:[]
  });
}
export function verifyAck(task,result) {
  validateEnvelope(task);validateEnvelope(result);
  const b=result.body;
  assert(task.kind==='task' && result.kind==='result','Wrong message pair');
  assert(task.sender===result.recipient && task.recipient===result.sender && b.in_reply_to===task.message_id,'Wrong participants/reply');
  assert(b.objective_id===task.body.objective.id && b.objective_digest===digest(task.body.objective) && b.constraints_digest===digest(task.body.constraints) && b.understood_objective===task.body.objective.text,'Ack mismatch');
  return true;
}

export function asA2aDataPart(envelope) {
  validateEnvelope(envelope);
  return { data: { aeon_link: envelope }, metadata: { aeon_link_version: VERSION } };
}
export function fromA2aDataPart(part) {
  if (!isObject(part?.data) || !isObject(part.data.aeon_link)) throw new ProtocolError('A2A data part missing aeon_link');
  return validateEnvelope(part.data.aeon_link);
}
export function asMcpToolResult(envelope) {
  validateEnvelope(envelope);
  return { structuredContent: { aeon_link: envelope }, isError: false };
}
export function fromMcpToolResult(result) {
  if (!isObject(result?.structuredContent) || !isObject(result.structuredContent.aeon_link)) throw new ProtocolError('MCP result missing aeon_link');
  return validateEnvelope(result.structuredContent.aeon_link);
}

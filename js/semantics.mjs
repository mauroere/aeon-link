/** ÆON-Link v0.4 deterministic semantic-contract profile (not natural-language proof).
 * Independent JS implementation of a bounded subset of predicate logic.
 */
import {canonicalBytes,digest} from './canonical.mjs';

export const PROFILE = 'aeon.semantic.contract/0.2';
export class ContractError extends Error {}
const OPS = new Set(['eq','ne','exists','gt','gte','lt','lte','in']);
const MODES = new Set(['require','forbid']);
const STATUSES = new Set(['satisfied','violated','incomplete']);
const MISSING = Symbol('missing');
const fail = msg => {throw new ContractError(msg)};
const isObj = x => x!==null && typeof x==='object' && !Array.isArray(x);
const sorted = x => [...x].sort();
function safe(x){ try {canonicalBytes(x)} catch(e){fail('Noncanonical contract/state: '+e.message)} }
function tokens(ptr){
  if(typeof ptr!=='string'||!ptr.startsWith('/')||ptr.length>256)fail('Invalid JSON Pointer');
  return ptr.slice(1).split('/').map(part=>{
    if(/~(?![01])/.test(part))fail('Malformed JSON Pointer escape');
    const token = part.replace(/~1/g,'/').replace(/~0/g,'~');
    if(['constructor','prototype','__proto__'].includes(token)||!(/^(?:[A-Za-z_][A-Za-z0-9_.-]*|0|[1-9][0-9]*)$/).test(token))fail('Unsupported path token');
    return token;
  });
}
export function normalizeContract(contract){
  safe(contract);
  if(!isObj(contract)||Object.keys(contract).sort().join(',')!=='allowed_actions,clauses,profile'||contract.profile!==PROFILE)fail('Invalid semantic contract');
  const {clauses,allowed_actions:actions}=contract;
  if(!Array.isArray(clauses)||clauses.length<1||clauses.length>64||!Array.isArray(actions)||actions.length<1||actions.length>32)fail('Invalid lengths');
  if(actions.some(a=>typeof a!=='string'||!a||a.length>128)||new Set(actions).size!==actions.length)fail('Invalid actions');
  const ids=new Set();
  for(const c of clauses){
    if(!isObj(c)||!['id','mode','path','op'].every(k=>Object.hasOwn(c,k))||Object.keys(c).some(k=>!['id','mode','path','op','value'].includes(k)))fail('Malformed clause');
    if(typeof c.id!=='string'||!c.id||c.id.length>128||ids.has(c.id))fail('Invalid clause ID');
    ids.add(c.id);
    if(!MODES.has(c.mode)||!OPS.has(c.op))fail('Invalid clause operation');
    tokens(c.path);
    if((c.op==='exists')===Object.hasOwn(c,'value'))fail('Predicate value mismatch');
    if(['gt','gte','lt','lte'].includes(c.op)&&(!Number.isSafeInteger(c.value)))fail('Comparison needs integer');
    if(c.op==='in'&&(!Array.isArray(c.value)||c.value.length===0||c.value.length>64))fail('Invalid membership list');
  }
  return {profile:PROFILE,allowed_actions:sorted(actions),clauses:[...clauses].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0)};
}
export const contractFingerprint = contract => digest(normalizeContract(contract));
function lookup(state,ptr){
  let val=state;
  for(const token of tokens(ptr)){
    if(isObj(val)){
      if(!Object.hasOwn(val,token))return MISSING;
      val=val[token];
    }else if(Array.isArray(val)){
      if(!/^(?:0|[1-9][0-9]*)$/.test(token)||!Object.hasOwn(val,token))return MISSING;
      val=val[Number(token)];
    }else return MISSING;
  }
  return val;
}
const same=(a,b)=>{
  if(typeof a!==typeof b || Array.isArray(a)!==Array.isArray(b) || isObj(a)!==isObj(b))return false;
  return canonicalBytes(a).equals(canonicalBytes(b));
};
function predicate(c,state){
  const actual=lookup(state,c.path);
  if(c.op==='exists')return actual!==MISSING;
  if(actual===MISSING)return null;
  const expected=c.value;
  switch(c.op){
    case 'eq':return same(actual,expected);
    case 'ne':return !same(actual,expected);
    case 'in':return expected.some(v=>same(actual,v));
    default:
      if(!Number.isSafeInteger(actual))return null;
      return ({gt:actual>expected,gte:actual>=expected,lt:actual<expected,lte:actual<=expected})[c.op];
  }
}
export function evaluateContract(contract,state,action){
  const c=normalizeContract(contract);
  if(!isObj(state)||typeof action!=='string')fail('Invalid state/action');
  safe(state);
  if(!c.allowed_actions.includes(action))return {status:'violated',violations:['action:unauthorized'],unknown:[]};
  const violations=[], unknown=[];
  for(const clause of c.clauses){
    const r=predicate(clause,state);
    if(r===null)unknown.push(clause.id);
    else if((clause.mode==='require'&&!r)||(clause.mode==='forbid'&&r))violations.push(clause.id);
  }
  return {status:violations.length?'violated':unknown.length?'incomplete':'satisfied',violations,unknown};
}
export function respondToChallenge(contract,publicChallenge){
  if(!isObj(publicChallenge)||Object.keys(publicChallenge).sort().join(',')!=='cases,contract_digest,nonce,profile'||publicChallenge.profile!==PROFILE||publicChallenge.contract_digest!==contractFingerprint(contract))fail('Invalid challenge binding');
  const {cases}=publicChallenge;
  if(!Array.isArray(cases)||cases.length<1||cases.length>64)fail('Invalid challenge cases');
  const seen=new Set();
  const answers=cases.map(c=>{
    if(!isObj(c)||Object.keys(c).sort().join(',')!=='action,id,state'||typeof c.id!=='string'||!c.id||seen.has(c.id))fail('Invalid case');
    seen.add(c.id);
    return {id:c.id,status:evaluateContract(contract,c.state,c.action).status};
  });
  return {nonce:publicChallenge.nonce,contract_digest:publicChallenge.contract_digest,answers};
}

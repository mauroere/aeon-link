/** Machine-checkable behavioral decision receipt. Not evidence of LLM reasoning. */
import {canonicalBytes,digest} from './canonical.mjs';
import {normalizeContract, contractFingerprint, evaluateContract} from './semantics.mjs';
const PROFILE='aeon.semantic.receipt/0.1';
const missing=Symbol('missing');
function pathTokens(ptr){return ptr.slice(1).split('/').map(t=>t.replace(/~1/g,'/').replace(/~0/g,'~'));}
function lookup(state,ptr){
 let val=state;
 for(const token of pathTokens(ptr)){
  if(val!==null&&typeof val==='object'&&Object.hasOwn(val,token))val=val[token];
  else return missing;
 }
 return val;
}
function same(a,b){
 if(typeof a!==typeof b||Array.isArray(a)!==Array.isArray(b))return false;
 return canonicalBytes(a).equals(canonicalBytes(b));
}
function predicate(c,state){
 const actual=lookup(state,c.path);
 if(c.op==='exists')return actual!==missing;
 if(actual===missing)return null;
 switch(c.op){
  case 'eq':return same(actual,c.value);
  case 'ne':return !same(actual,c.value);
  case 'in':return c.value.some(v=>same(actual,v));
  default:
   if(!Number.isSafeInteger(actual))return null;
   return ({gt:actual>c.value,gte:actual>=c.value,lt:actual<c.value,lte:actual<=c.value})[c.op];
 }
}
export function makeDecisionReceipt(contract,state,action){
 const norm=normalizeContract(contract);
 if(state===null||typeof state!=='object'||Array.isArray(state)||typeof action!=='string')throw Error('Invalid receipt inputs');
 canonicalBytes(state);
 const decision=evaluateContract(norm,state,action),trace=[];
 if(!norm.allowed_actions.includes(action))trace.push({id:'action:unauthorized',outcome:'fail'});
 else for(const c of norm.clauses){
  const result=predicate(c,state);
  const failed=(c.mode==='require'&&!result)||(c.mode==='forbid'&&result);
  trace.push({id:c.id,outcome:result===null?'unknown':failed?'fail':'pass'});
 }
 return {profile:PROFILE,contract_digest:contractFingerprint(norm),state_digest:digest(state),action,decision,trace};
}
export function verifyDecisionReceipt(contract,state,action,receipt){
 canonicalBytes(receipt);
 const a=canonicalBytes(receipt),b=canonicalBytes(makeDecisionReceipt(contract,state,action));
 if(!a.equals(b))throw Error('Decision receipt mismatch');
 return true;
}

/** AEON-Link v0.3 Node.js HMAC/canonical interoperability subset.
 * No transport, authorization authority, agent API or full JSON Schema validator.
 */
import {createHash,createHmac,timingSafeEqual} from 'node:crypto';
export class ProtocolError extends Error {}
const KEY=/^[A-Za-z_][A-Za-z0-9_.-]*$/;
const DOMAIN=Buffer.from('AEON-LINK-HMAC-SHA256-v1\0','utf8');
function fail(msg){throw new ProtocolError(msg);}
function encode(x,depth=0){
  if(depth>64)fail('Excessive JSON depth');
  if(x===null)return 'null';
  if(typeof x==='boolean')return x?'true':'false';
  if(typeof x==='number')return Number.isSafeInteger(x)?JSON.stringify(x):fail('Unsafe integer/float');
  if(typeof x==='string'){
    for(let i=0;i<x.length;i++){
      const c=x.charCodeAt(i);
      if(c>=0xd800&&c<=0xdbff){const next=x.charCodeAt(++i);if(!(next>=0xdc00&&next<=0xdfff))fail('Unpaired Unicode surrogate');}
      else if(c>=0xdc00&&c<=0xdfff)fail('Unpaired Unicode surrogate');
    }
    return JSON.stringify(x);
  }
  if(Array.isArray(x))return '['+x.map(v=>encode(v,depth+1)).join(',')+']';
  if(x&&typeof x==='object'){
    const keys=Object.keys(x).sort();
    if(keys.some(k=>!KEY.test(k)))fail('Expected ASCII identifier keys');
    return '{'+keys.map(k=>JSON.stringify(k)+':'+encode(x[k],depth+1)).join(',')+'}';
  }
  fail('Unsupported JSON value');
}
export function canonicalBytes(value){
  const b=Buffer.from(encode(value),'utf8');
  if(b.length>1048576)fail('Message exceeds 1 MiB');
  return b;
}
export const digest=x=>createHash('sha256').update(canonicalBytes(x)).digest('hex');
export function parseCanonical(buf){
  if(!Buffer.isBuffer(buf)||buf.length>1048576)fail('Invalid canonical bytes');
  let parsed;
  try{parsed=JSON.parse(buf.toString('utf8'));}catch{fail('Invalid JSON');}
  if(!canonicalBytes(parsed).equals(buf))fail('Noncanonical wire JSON or duplicate keys');
  return parsed;
}
function mac(envelope,meta,secret){
  return createHmac('sha256',secret).update(DOMAIN).update(canonicalBytes({envelope,meta})).digest('hex');
}
function assert(v,msg){if(!v)fail(msg);}
export function signEnvelope(envelope,{keyId,secret,issuedAt=Math.floor(Date.now()/1000),ttlSeconds=60}){
  assert(typeof keyId==='string'&&keyId.length>0&&Buffer.isBuffer(secret)&&secret.length>=32,'Invalid trusted key');
  assert(Number.isSafeInteger(issuedAt)&&Number.isSafeInteger(ttlSeconds)&&ttlSeconds>=1&&ttlSeconds<=300,'Invalid signed time');
  const meta={alg:'HS256',key_id:keyId,issued_at:issuedAt,expires_at:issuedAt+ttlSeconds};
  const signature=mac(envelope,meta,secret);
  return {envelope,meta,signature};
}
export function verifySigned(wrapper,trustedKeys,{now=Math.floor(Date.now()/1000)}={}){
  assert(wrapper&&typeof wrapper==='object'&&Object.keys(wrapper).sort().join(',')==='envelope,meta,signature','Invalid wrapper');
  const {envelope,meta,signature}=wrapper;
  assert(envelope?.protocol==='aeon-link'&&envelope?.version==='0.3.0'&&envelope?.ontology==='urn:aeon-link:ontology:core:0.3.0','Unsupported envelope');
  assert(meta&&Object.keys(meta).sort().join(',')==='alg,expires_at,issued_at,key_id'&&meta.alg==='HS256','Invalid metadata');
  const key=Object.hasOwn(trustedKeys,meta.key_id)?trustedKeys[meta.key_id]:undefined;
  assert(key&&typeof key.sender==='string'&&Buffer.isBuffer(key.secret)&&key.secret.length>=32,'Unknown trusted key');
  assert(Number.isSafeInteger(meta.issued_at)&&Number.isSafeInteger(meta.expires_at)&&meta.expires_at-meta.issued_at>=1&&meta.expires_at-meta.issued_at<=300,'Invalid lifetime');
  assert(Number.isSafeInteger(now)&&meta.issued_at<=now+30&&meta.expires_at>=now,'Expired/future message');
  assert(typeof signature==='string'&&/^[a-f0-9]{64}$/.test(signature),'Invalid signature');
  assert(timingSafeEqual(Buffer.from(signature,'hex'),Buffer.from(mac(envelope,meta,key.secret),'hex')),'Bad signature');
  assert(envelope.sender===key.sender,'Key identity mismatch');
  return {envelope,verifiedSender:key.sender,keyId:meta.key_id,expiresAt:meta.expires_at};
}

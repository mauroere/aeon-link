/** HMAC authentication over canonical AEON payloads using out-of-band shared keys.
 * Verify before authorization, using sender binding from a trusted local registry.
 */
import {createHmac, timingSafeEqual} from 'node:crypto';
import {canonicalBytes} from './canonical.mjs';
import {validateEnvelope, ProtocolError} from './aeon-link.mjs';
const DOMAIN = Buffer.from('AEON-LINK-HMAC-SHA256-v1\0','utf8');
const MAX_TTL = 300, CLOCK_SKEW = 30;
function assert(v,r) {if (!v) throw new ProtocolError(r);}
const own = (o,k)=>Object.prototype.hasOwnProperty.call(o,k);
function mac(envelope,meta,secret) {
  return createHmac('sha256', secret).update(DOMAIN).update(canonicalBytes({envelope,meta})).digest('hex');
}
export function signEnvelope(envelope,{keyId,secret,issuedAt=Math.floor(Date.now()/1000),ttlSeconds=60}) {
  validateEnvelope(envelope);
  assert(typeof keyId === 'string' && keyId.length > 0 && Buffer.isBuffer(secret) && secret.length >= 32, 'Invalid signing key');
  assert(Number.isSafeInteger(issuedAt) && Number.isSafeInteger(ttlSeconds) && ttlSeconds>=1 && ttlSeconds<=MAX_TTL, 'Invalid time window');
  const meta = {alg:'HS256',key_id:keyId,issued_at:issuedAt,expires_at:issuedAt+ttlSeconds};
  return {envelope,meta,signature:mac(envelope,meta,secret)};
}
export function verifySigned(signed,trustedKeys,{now=Math.floor(Date.now()/1000)}={}) {
  assert(signed && typeof signed === 'object' && !Array.isArray(signed) && Object.keys(signed).sort().join(',')==='envelope,meta,signature','Invalid signed wrapper');
  const {envelope,meta,signature}=signed;
  validateEnvelope(envelope);
  assert(meta && typeof meta==='object' && !Array.isArray(meta) && Object.keys(meta).sort().join(',')==='alg,expires_at,issued_at,key_id' && meta.alg==='HS256','Invalid auth metadata');
  const key = own(trustedKeys,meta.key_id) ? trustedKeys[meta.key_id] : undefined;
  assert(key && typeof key.sender==='string' && Buffer.isBuffer(key.secret) && key.secret.length>=32,'Unknown trusted key');
  assert(Number.isSafeInteger(meta.issued_at) && Number.isSafeInteger(meta.expires_at) && meta.expires_at-meta.issued_at>=1 && meta.expires_at-meta.issued_at<=MAX_TTL,'Invalid signed time window');
  assert(Number.isSafeInteger(now) && meta.issued_at<=now+CLOCK_SKEW && meta.expires_at>=now,'Expired or future message');
  assert(typeof signature==='string' && /^[a-f0-9]{64}$/.test(signature),'Bad signature');
  const expected=Buffer.from(mac(envelope,meta,key.secret),'hex'),actual=Buffer.from(signature,'hex');
  assert(timingSafeEqual(expected,actual),'Invalid message signature');
  assert(key.sender===envelope.sender,'Key identity does not match sender');
  return {envelope, verifiedSender:key.sender, keyId:meta.key_id, expiresAt:meta.expires_at};
}

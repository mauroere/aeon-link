/** Strict authenticated inbound boundary for AEON-Link 0.4 wire format.
 * SDK release 0.5. Requires host-supplied atomic, durable replay store.
 * No tool or model execution occurs here.
 */
import {parseCanonical} from './canonical.mjs';
import {verifySigned} from './auth.mjs';
import {validateEnvelope, ProtocolError} from './aeon-link.mjs';
const fail = msg => {throw new ProtocolError(msg);};
const isObj = x=>x!==null&&typeof x==='object'&&!Array.isArray(x);

/**
 * @param {Buffer} raw canonical UTF-8 signed wrapper
 * @param {object} cfg trustedKeys, localRecipient, policy, replayGuard, now
 * await replayGuard.checkAndRecord(verifiedSender, messageId, expiresAt, now)
 * must be atomic and durable across all processes executing side effects.
 */
export async function receiveSigned(raw,{trustedKeys,localRecipient,policy=null,replayGuard,now=Math.floor(Date.now()/1000)}) {
  if(!Buffer.isBuffer(raw))fail('Canonical Buffer required');
  if(typeof localRecipient!=='string'||localRecipient.length<1||localRecipient.length>256)fail('Explicit local recipient required');
  if(!Number.isSafeInteger(now)||Object.is(now,-0))fail('Invalid clock');
  if(!replayGuard||typeof replayGuard.checkAndRecord!=='function')fail('Host must provide durable replay store');
  const wrapper=parseCanonical(raw);
  const verified=verifySigned(wrapper,trustedKeys,{now});
  const envelope=validateEnvelope(verified.envelope);
  if(envelope.recipient!==localRecipient)fail('Message addressed to another recipient');
  if(envelope.kind==='task'){
    if(!isObj(policy)||typeof policy.verifiedSender!=='string'||!Array.isArray(policy.allowedActions)||!policy.allowedActions.every(x=>typeof x==='string'))fail('Host policy is required');
    if(policy.verifiedSender!==verified.verifiedSender)fail('Policy bound to wrong authenticated sender');
    if(!policy.allowedActions.includes(envelope.body.action))fail('Task action denied by local policy');
  }
  // A replay guard throws to reject duplicate or expired messages.
  await replayGuard.checkAndRecord(verified.verifiedSender,envelope.message_id,verified.expiresAt,now);
  return {envelope:structuredClone(envelope),verifiedSender:verified.verifiedSender,
          recipient:localRecipient,messageId:envelope.message_id,keyId:verified.keyId,
          expiresAt:verified.expiresAt,replayRecorded:true};
}

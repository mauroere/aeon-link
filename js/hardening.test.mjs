import test from 'node:test';
import assert from 'node:assert/strict';
import {hello, message, ProtocolError} from './aeon-link.mjs';
import {canonicalBytes,digest,parseCanonical,CanonicalizationError} from './canonical.mjs';
import {signEnvelope,verifySigned} from './auth.mjs';
const key = Buffer.from([...Array(32).keys()]);
const trusted = {'demo-key':{sender:'alpha',secret:key}};
const task = ()=>message('task','alpha','beta',{
  objective:{id:'o1',text:'Revisar conexión 🚀',success_criteria:['Sin pérdidas']},
  constraints:{read_only:true},action:'observe',claims:[],evidence:[]
});
test('UTF8 canonical stability',()=>assert.equal(canonicalBytes({z:'é 🚀',a:[1,true]}).toString(),'{'+'"a":[1,true],"z":"é 🚀"}'));
test('floating-point rejected',()=>assert.throws(()=>canonicalBytes({x:1.5}),CanonicalizationError));
test('unsafe int rejected',()=>assert.throws(()=>canonicalBytes({x:Number.MAX_SAFE_INTEGER+1}),CanonicalizationError));
test('unpaired surrogate rejected',()=>assert.throws(()=>canonicalBytes({x:'\ud800'}),CanonicalizationError));
test('non-ASCII keys rejected',()=>assert.throws(()=>canonicalBytes({'é':'value'}),CanonicalizationError));
test('duplicate key raw JSON rejected',()=>assert.throws(()=>parseCanonical(Buffer.from('{"a":1,"a":2}')),CanonicalizationError));
test('canonical raw roundtrip',()=>assert.deepEqual(parseCanonical(canonicalBytes({z:2,a:'ø'})),{z:2,a:'ø'}));
test('HMAC verifies valid message',()=>{
  const signed=signEnvelope(task(),{keyId:'demo-key',secret:key,issuedAt:1000});
  assert.equal(verifySigned(signed,trusted,{now:1010}).verifiedSender,'alpha');
});
test('HMAC rejects changed task',()=>{
  const signed=signEnvelope(task(),{keyId:'demo-key',secret:key,issuedAt:1000});
  signed.envelope.body.objective.text='tampered';
  assert.throws(()=>verifySigned(signed,trusted,{now:1010}),ProtocolError);
});
test('HMAC rejects changed expiry',()=>{
  const signed=signEnvelope(task(),{keyId:'demo-key',secret:key,issuedAt:1000});
  signed.meta.expires_at++;
  assert.throws(()=>verifySigned(signed,trusted,{now:1010}),ProtocolError);
});
test('HMAC rejects bound sender mismatch',()=>{
  const signed=signEnvelope(task(),{keyId:'demo-key',secret:key,issuedAt:1000});
  assert.throws(()=>verifySigned(signed,{'demo-key':{sender:'omega',secret:key}},{now:1010}),ProtocolError);
});
test('HMAC rejects expired message',()=>{
  const signed=signEnvelope(task(),{keyId:'demo-key',secret:key,issuedAt:1000});
  assert.throws(()=>verifySigned(signed,trusted,{now:1061}),ProtocolError);
});
test('HMAC rejects future message',()=>{
  const signed=signEnvelope(task(),{keyId:'demo-key',secret:key,issuedAt:1000});
  assert.throws(()=>verifySigned(signed,trusted,{now:969}),ProtocolError);
});

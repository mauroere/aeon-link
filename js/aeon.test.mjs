import test from 'node:test';
import assert from 'node:assert/strict';
import {canonicalBytes,digest,parseCanonical,signEnvelope,verifySigned,ProtocolError} from './aeon.mjs';
const secret=Buffer.from([...Array(32).keys()]);
const msg=()=>({protocol:'aeon-link',version:'0.3.0',ontology:'urn:aeon-link:ontology:core:0.3.0',
 message_id:'f25c4760-2b87-4f01-90f0-a55befca51f1',kind:'task',sender:'alpha',recipient:'beta',
 body:{objective:{id:'one',text:'Conexión 🚀'},constraints:{read_only:true},action:'observe',claims:[],evidence:[]}});
const signed=()=>signEnvelope(msg(),{keyId:'demo',secret,issuedAt:1700000000});
test('canonical UTF8 and ordering',()=>assert.equal(canonicalBytes({z:'é 🚀',a:[1,true]}).toString(),'{'+'"a":[1,true],"z":"é 🚀"}'));
test('unsafe numbers rejected',()=>assert.throws(()=>canonicalBytes({x:1.25}),ProtocolError));
test('unsafe Unicode rejected',()=>assert.throws(()=>canonicalBytes({x:'\ud800'}),ProtocolError));
test('noncanonical wire rejected',()=>assert.throws(()=>parseCanonical(Buffer.from('{"a":1,"a":2}')),ProtocolError));
test('signed valid identity',()=>assert.equal(verifySigned(signed(),{demo:{sender:'alpha',secret}},{now:1700000001}).verifiedSender,'alpha'));
test('tamper rejected',()=>{const s=signed();s.envelope.body.objective.text='changed';assert.throws(()=>verifySigned(s,{demo:{sender:'alpha',secret}},{now:1700000001}),ProtocolError)});
test('expiry rejected',()=>assert.throws(()=>verifySigned(signed(),{demo:{sender:'alpha',secret}},{now:1700000061}),ProtocolError));
test('key-bound identity',()=>assert.throws(()=>verifySigned(signed(),{demo:{sender:'other',secret}},{now:1700000001}),ProtocolError));

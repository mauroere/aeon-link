import test from 'node:test';
import assert from 'node:assert/strict';
import {canonicalBytes} from './canonical.mjs';
import {signEnvelope} from './auth.mjs';
import {receiveSigned} from './ingress.mjs';
import {message} from './aeon-link.mjs';

const key=Buffer.from([...Array(32).keys()]);
function fixture(recipient='beta'){
 const env=message('task','alpha',recipient,{objective:{id:'o1',text:'Observe',success_criteria:['Report']},constraints:{read_only:true},action:'observe',claims:[],evidence:[]});
 return canonicalBytes(signEnvelope(env,{keyId:'test-key',secret:key,issuedAt:1700000000}));
}
function cfg(){
 const seen=new Set();
 return {trustedKeys:{'test-key':{sender:'alpha',secret:key}},localRecipient:'beta',
         policy:{verifiedSender:'alpha',allowedActions:['observe']},now:1700000001,
         replayGuard:{checkAndRecord:(sender,id,expiry,now)=>{
            if(expiry<now)throw new Error('expired');
            const token=sender+'|'+id;if(seen.has(token))throw new Error('duplicate');seen.add(token);
         }}};
}
test('accept authentic authorized message',async()=>{
 const result=await receiveSigned(fixture(),cfg());assert.equal(result.verifiedSender,'alpha');
});
test('local replay rejection is pluggable',async()=>{
 const options=cfg(),wire=fixture();await receiveSigned(wire,options);
 await assert.rejects(()=>receiveSigned(wire,options),/duplicate/);
});
test('recipient mismatch rejects before replay record',async()=>{
 const options=cfg(),raw=fixture('gamma');
 await assert.rejects(()=>receiveSigned(raw,options),/another recipient/);
 options.localRecipient='gamma';assert.equal((await receiveSigned(raw,options)).recipient,'gamma');
});
test('no policy rejects task',async()=>await assert.rejects(()=>receiveSigned(fixture(),{...cfg(),policy:null}),/policy/));
test('unauthorized action denies',async()=>await assert.rejects(()=>receiveSigned(fixture(),{...cfg(),policy:{verifiedSender:'alpha',allowedActions:['execute']}}),/denied/));
test('tampering invalidates signature',async()=>{
 const obj=JSON.parse(fixture().toString());obj.envelope.body.objective.text='changed';
 await assert.rejects(()=>receiveSigned(canonicalBytes(obj),cfg()),/signature/);
});
test('must provide durable store',async()=>await assert.rejects(()=>receiveSigned(fixture(),{...cfg(),replayGuard:null}),/store/));
test('duplicate noncanonical JSON rejects',async()=>{
 const raw=fixture().toString().replace('"envelope":','"bogus":0,"envelope":');
 await assert.rejects(()=>receiveSigned(Buffer.from(raw),cfg()),/Invalid|Noncanonical/);
});
test('reject getter-based object as JSON',()=>{
 const x={};Object.defineProperty(x,'hidden',{enumerable:true,get:()=>42});
 assert.throws(()=>canonicalBytes(x),/Accessor/);
});
test('reject objects that only appear empty',()=>assert.throws(()=>canonicalBytes(new Date(0)),/plain/));
test('reject non-JSON sparse arrays',()=>assert.throws(()=>canonicalBytes([,1]),/Sparse/));
test('reject prototype pollution keys',()=>assert.throws(()=>canonicalBytes(JSON.parse('{"__proto__":0}')),/safe ASCII/));
test('reject negative zero',()=>assert.throws(()=>canonicalBytes({x:-0}),/safe JSON integer/));

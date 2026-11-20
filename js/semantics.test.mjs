import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalizeContract,contractFingerprint,evaluateContract,respondToChallenge,ContractError} from './semantics.mjs';
const fixture=JSON.parse(readFileSync(new URL('../fixtures/semantic-vectors.json',import.meta.url),'utf8'));
const c=fixture.contract;
test('Python -> Node contract SHA256 fingerprint',()=>assert.equal(contractFingerprint(c),fixture.contract_digest));
for(const entry of fixture.cases){
  test('Python -> Node semantic decision: '+entry.id,()=>assert.deepEqual(evaluateContract(c,entry.state,entry.action),entry.expected));
}
test('reordered contract has same fingerprint',()=>{
  assert.equal(contractFingerprint({...c,clauses:[...c.clauses].reverse(),allowed_actions:[...c.allowed_actions].reverse()}),fixture.contract_digest);
});
test('reject ambiguous bool/numeric equality',()=>{
  assert.equal(evaluateContract(c,{...fixture.cases[0].state,metrics:{loss:true}},'observe').status,'incomplete');
});
test('reject prototype traversal',()=>{
  const bad=JSON.parse(JSON.stringify(c));bad.clauses[0].path='/__proto__/poison';
  assert.throws(()=>normalizeContract(bad),ContractError);
});
test('reject unknown operator',()=>{
  const bad=JSON.parse(JSON.stringify(c));bad.clauses[0].op='exec';
  assert.throws(()=>normalizeContract(bad),ContractError);
});
test('reject duplicate clauses',()=>{
  const bad=JSON.parse(JSON.stringify(c));bad.clauses.push({...bad.clauses[0]});
  assert.throws(()=>normalizeContract(bad),ContractError);
});
test('respond to challenge without expected answers',()=>{
  const cases=fixture.cases.map(({id,state,action})=>({id,state,action}));
  const publicChallenge={profile:fixture.profile,nonce:'valid123',contract_digest:fixture.contract_digest,cases};
  const answer=respondToChallenge(c,publicChallenge);
  assert.deepEqual(answer.answers.map(x=>x.status),fixture.cases.map(x=>x.expected.status));
});
test('Unicode clause identifiers are rejected to avoid cross-runtime sorting divergence',()=>{
  const bad=JSON.parse(JSON.stringify(c));bad.clauses[0].id='🚀';
  assert.throws(()=>normalizeContract(bad),ContractError);
});
test('Unicode action identifiers are rejected',()=>{
  const bad=JSON.parse(JSON.stringify(c));bad.allowed_actions=['🌐'];
  assert.throws(()=>normalizeContract(bad),ContractError);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {makeDecisionReceipt,verifyDecisionReceipt} from './receipts.mjs';
const c={profile:'aeon.semantic.contract/0.2',allowed_actions:['read'],clauses:[
 {id:'a',mode:'require',path:'/authenticated',op:'eq',value:true},
 {id:'b',mode:'forbid',path:'/blocked',op:'eq',value:true}
]};
test('receipt satisfied',()=>{
 const s={authenticated:true,blocked:false};const r=makeDecisionReceipt(c,s,'read');
 assert.deepEqual(r.trace.map(x=>x.outcome),['pass','pass']);
 assert.equal(verifyDecisionReceipt(c,s,'read',r),true);
});
test('receipt incomplete',()=>assert.equal(makeDecisionReceipt(c,{authenticated:true},'read').decision.status,'incomplete'));
test('receipt unauthorized',()=>assert.equal(makeDecisionReceipt(c,{authenticated:true},'execute').trace[0].outcome,'fail'));
test('receipt tampering is rejected',()=>{
 const s={authenticated:true,blocked:false},r=makeDecisionReceipt(c,s,'read');r.trace[0].outcome='fail';
 assert.throws(()=>verifyDecisionReceipt(c,s,'read',r),/mismatch/);
});

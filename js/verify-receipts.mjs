import {readFileSync} from 'node:fs';
import {canonicalBytes} from './canonical.mjs';
import {makeDecisionReceipt,verifyDecisionReceipt} from './receipts.mjs';
const data=JSON.parse(readFileSync(process.argv[2],'utf8'));
let count=0;
for(const row of data){
 if(!canonicalBytes(makeDecisionReceipt(row.contract,row.state,row.action))
         .equals(canonicalBytes(row.receipt)))throw Error('Cross-language receipt mismatch '+count);
 verifyDecisionReceipt(row.contract,row.state,row.action,row.receipt);count++;
}
console.log('Cross-language semantic decision receipts:',count,'verified');

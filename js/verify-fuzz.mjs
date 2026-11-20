import {readFileSync} from 'node:fs';
import {canonicalBytes,digest} from './canonical.mjs';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8'));
for(const [index,v] of rows.entries()){
 if(digest(v.value)!==v.sha256 || canonicalBytes(v.value).toString('hex')!==v.canonical_hex)
   throw new Error('Canonical mismatch at row '+index);
}
console.log('Cross-language deterministic canonical fuzz:',rows.length,'verified');

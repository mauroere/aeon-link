import {readFileSync} from 'node:fs';
import {validateEnvelope} from './aeon-link.mjs';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8'));
const mismatches=[];
for(const {case:name,envelope,accepted} of rows){
 let result;
 try{validateEnvelope(envelope);result=true;}catch{result=false;}
 if(result!==accepted)mismatches.push({case:name,python:accepted,node:result});
}
console.log(JSON.stringify({total:rows.length,mismatches}));
if(mismatches.length)process.exitCode=1;

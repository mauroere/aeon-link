/** Example only, keys used here are public deterministic demo bytes, never production secrets. */
import {readFileSync} from 'node:fs';
import {message,digest} from './aeon-link.mjs';
import {verifySigned,signEnvelope} from './auth.mjs';
const input=JSON.parse(readFileSync(0,'utf8'));
const key=Buffer.from([...Array(32).keys()]);
const verified=verifySigned(input,{'demo-1':{sender:'agent-a',secret:key}},{now:1700000010});
const task=verified.envelope;
const response=message('result','agent-b','agent-a',{
  in_reply_to:task.message_id, objective_id:task.body.objective.id,
  objective_digest:digest(task.body.objective), constraints_digest:digest(task.body.constraints),
  status:'needs_clarification',understood_objective:task.body.objective.text,
  findings:[],uncertainties:['Simulated only; no model consulted'],actions_executed:[]
});
const signed=signEnvelope(response,{keyId:'demo-1',secret:key,issuedAt:1700000000,ttlSeconds:120});
process.stdout.write(JSON.stringify({signed,digest:digest(task.body.objective)}));

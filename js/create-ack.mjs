/** Offline Node responder. stdin = Python-origin AEON envelope, stdout = Node result. */
import { makeAckResult } from './aeon-link.mjs';
let input='';
for await(const chunk of process.stdin)input+=chunk;
const task=JSON.parse(input);
const result=makeAckResult(task,task.recipient);
process.stdout.write(JSON.stringify(result));

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { hello, negotiate, validateEnvelope, digest, makeAckResult, verifyAck, ProtocolError } from './aeon-link.mjs';

const fixture = JSON.parse(readFileSync(new URL('../fixtures/cross-language-vectors.json',import.meta.url)));

test('Python fixture is accepted in Node and digests agree', () => {
  validateEnvelope(fixture.envelope);
  assert.equal(digest(fixture.envelope.body.objective),fixture.objective_digest);
  assert.equal(digest(fixture.envelope.body.constraints),fixture.constraints_digest);
});
test('Node replies to a Python-generated task', () => {
  assert.equal(verifyAck(fixture.envelope,makeAckResult(fixture.envelope,'agent-beta')),true);
});
test('Negotiation produces a compatible agreement',()=>{
  assert.equal(negotiate(hello('a','b'),hello('b','a'),['claims.v1']).version,'0.4.0');
});
test('Unsupported ontology is rejected',()=>{
  const x=structuredClone(fixture.envelope);x.ontology='urn:wrong';
  assert.throws(()=>validateEnvelope(x),ProtocolError);
});
test('A fact without evidence is rejected',()=>{
  const x=structuredClone(fixture.envelope);x.body.claims[0].evidence_ids=[];
  assert.throws(()=>validateEnvelope(x),ProtocolError);
});
test('Read-only action cannot write',()=>{
  const x=structuredClone(fixture.envelope);x.body.action='write';
  assert.throws(()=>validateEnvelope(x),ProtocolError);
});

test('A2A data-part payload round trip',async()=>{
  const {asA2aDataPart,fromA2aDataPart}=await import('./aeon-link.mjs');
  assert.deepEqual(fromA2aDataPart(asA2aDataPart(fixture.envelope)),fixture.envelope);
});
test('MCP structured tool result round trip',async()=>{
  const {asMcpToolResult,fromMcpToolResult}=await import('./aeon-link.mjs');
  assert.deepEqual(fromMcpToolResult(asMcpToolResult(fixture.envelope)),fixture.envelope);
});

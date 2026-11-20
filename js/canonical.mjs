/** Restricted cross-runtime canonical JSON: safe integers, strings, ASCII keys.
 * Not RFC 8785/JCS. Rejects floats instead of accepting divergent encodings.
 */
import {createHash} from 'node:crypto';
const KEY = /^[A-Za-z_][A-Za-z0-9_.-]*$/;
const RESERVED = new Set(['__proto__','constructor','prototype']);
const MAX_BYTES = 1_048_576;
const isObj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const isPlain = x => Object.getPrototypeOf(x)===Object.prototype || Object.getPrototypeOf(x)===null;
export class CanonicalizationError extends Error {}
function fail(reason) {throw new CanonicalizationError(reason);}
function encode(x, depth = 0) {
  if (depth > 64) fail('Maximum JSON depth exceeded');
  if (x === null) return 'null';
  if (typeof x === 'boolean') return x ? 'true' : 'false';
  if (typeof x === 'number') {
    if (!Number.isSafeInteger(x) || Object.is(x, -0)) fail('Expected unambiguous safe JSON integer');
    return JSON.stringify(x);
  }
  if (typeof x === 'string') {
    for (let i = 0; i < x.length; ++i) {
      const c = x.charCodeAt(i);
      if (c >= 0xd800 && c <= 0xdbff) {
        const next = x.charCodeAt(i + 1);
        if (!(next >= 0xdc00 && next <= 0xdfff)) fail('Unpaired high surrogate');
        ++i;
      } else if (c >= 0xdc00 && c <= 0xdfff) fail('Unpaired low surrogate');
    }
    return JSON.stringify(x);
  }
  if (Array.isArray(x)) {
    for (let i=0;i<x.length;i++) if (!Object.hasOwn(x,i)) fail('Sparse array is not JSON');
    return '[' + x.map(v=>encode(v,depth+1)).join(',') + ']';
  }
  if (isObj(x)) {
    if (!isPlain(x)) fail('Only plain JSON objects are supported');
    const keys = Object.keys(x).sort();
    for (const k of keys) {
      if (!KEY.test(k) || RESERVED.has(k)) fail('Object keys must be safe ASCII identifiers');
      const d = Object.getOwnPropertyDescriptor(x,k);
      if (!d || !Object.hasOwn(d,'value')) fail('Accessor properties are not JSON');
    }
    return '{' + keys.map(k=>JSON.stringify(k)+':'+encode(x[k],depth+1)).join(',') + '}';
  }
  return fail('Invalid JSON value');
}
export function canonicalBytes(x) {
  const data = Buffer.from(encode(x), 'utf8');
  if (data.length > MAX_BYTES) fail('Canonical data exceeds 1 MiB');
  return data;
}
export const digest = x => createHash('sha256').update(canonicalBytes(x)).digest('hex');
export function parseCanonical(raw) {
  if (!Buffer.isBuffer(raw) || raw.length > MAX_BYTES) fail('Expected canonical bytes within 1 MiB');
  let parsed;
  try { parsed = JSON.parse(raw.toString('utf8')); } catch {return fail('Invalid JSON');}
  if (!canonicalBytes(parsed).equals(raw)) fail('Noncanonical wire bytes or duplicate keys');
  return parsed;
}

"""Check Node-generated result for Python-issued fixture task: python examples/check_node_ack.py FILE"""
import json
import sys
from pathlib import Path
from aeon_link import verify_ack

fixture = json.loads((Path(__file__).resolve().parent.parent / 'fixtures/cross-language-vectors.json').read_text(encoding='utf8'))
result = json.loads(Path(sys.argv[1]).read_text(encoding='utf8'))
assert verify_ack(fixture['envelope'], result)
print('CROSS-LANGUAGE PASS: Node-produced acknowledgment verified independently in Python')

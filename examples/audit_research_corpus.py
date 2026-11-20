"""Read-only reproducibility and leakage audit of the synthetic benchmark."""
import argparse
import json
from pathlib import Path

from aeon_link.research_eval import (
    make_cases, dataset_digest, assert_split_integrity, logical_signature, SPLITS,
)


def audit(corpus):
    integrity = assert_split_integrity(corpus)
    counts = {}
    for split in SPLITS:
        cases = corpus['splits'][split]
        counts[split] = {
            'rows': len(cases),
            'logical_groups': len({logical_signature(c) for c in cases}),
            'labels': {label: sum(c['expected'] == label for c in cases)
                       for label in ('satisfied', 'violated', 'incomplete')},
            'per_domain': {d: sum(c['domain'] == d for c in cases)
                           for d in sorted({c['domain'] for c in cases})},
        }
    return {
        'schema': 'aeon.research.integrity/0.1',
        'corpus_digest_sha256': dataset_digest(corpus),
        'integrity': integrity,
        'splits': counts,
        'limitations': [
            'Public deterministic synthetic corpus, NOT externally blinded',
            'Six domain templates; logical groups remain correlated within a domain',
            'Grouping ignores observation_id and untrusted comment text by design',
            'No commercial-model results or protocol superiority measured',
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    result = audit(make_cases())
    rendered = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.write_text(rendered, encoding='utf-8')
    else:
        print(rendered, end='')


if __name__ == '__main__':
    main()

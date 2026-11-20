"""Simple local CLI. Does not connect to external APIs."""
import argparse
import json
import sys
from .core import ProtocolError, validate_envelope


def main():
    p = argparse.ArgumentParser(description="Validate experimental AEON-Link 0.4.0 message envelopes")
    p.add_argument("file", help="JSON envelope file or '-' for standard input")
    args = p.parse_args()
    try:
        if args.file == "-":
            obj = json.load(sys.stdin)
        else:
            with open(args.file, "r", encoding="utf-8") as f:
                obj = json.load(f)
        validate_envelope(obj)
        print("VALID: AEON-Link v0.4.0 envelope. No evidence authenticity verified.")
    except (OSError, ValueError, ProtocolError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

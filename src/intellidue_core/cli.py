from __future__ import annotations
import argparse, json, sys
from .validators import validate_state, validate_release_lock, validate_zip
from .manifest import save_manifest

def main(argv=None):
    p=argparse.ArgumentParser(prog='intellidue')
    sub=p.add_subparsers(dest='cmd',required=True)
    for name in ('validate-state','validate-lock','validate-package'):
        q=sub.add_parser(name); q.add_argument('path')
    q=sub.add_parser('build-manifest'); q.add_argument('root'); q.add_argument('output')
    a=p.parse_args(argv)
    if a.cmd=='validate-state': errors=validate_state(a.path)
    elif a.cmd=='validate-lock': errors=validate_release_lock(a.path)
    elif a.cmd=='validate-package': errors=validate_zip(a.path)
    else:
        save_manifest(a.root,a.output); print(a.output); return 0
    print(json.dumps({'ok':not errors,'errors':errors},indent=2))
    return 0 if not errors else 1

if __name__=='__main__': raise SystemExit(main())

"""Command-line end-to-end synthetic demonstration."""
import argparse
import json
from .sim_runner import SCENARIOS, build, generate_and_store
from .historian import runs, get_run
from .analytics import summary, similar_runs
from .nebius import analyze


def main():
    p=argparse.ArgumentParser(description='DewaterIQ synthetic, isolated, advisory-only demo')
    sub=p.add_subparsers(dest='action',required=True)
    demo=sub.add_parser('demo',help='Build C, generate synthetic runs, and store SQLite historian')
    demo.add_argument('--scenario',choices=(*SCENARIOS,'all'),default='all')
    demo.add_argument('--samples',type=int,default=80)
    demo.add_argument('--seed',type=int,default=7)
    demo.add_argument('--centrifuge-id',default='CENT-SIM-01')
    sub.add_parser('runs',help='List runs in historian')
    rep=sub.add_parser('report',help='Summarize a stored run')
    rep.add_argument('run_id'); rep.add_argument('--use-nebius',action='store_true')
    args=p.parse_args()
    if args.action=='demo':
        build()
        for name in (SCENARIOS if args.scenario=='all' else (args.scenario,)):
            run_id,n=generate_and_store(name,args.samples,args.seed,centrifuge_id=args.centrifuge_id)
            print(f'Imported {run_id}: {n} synthetic samples')
    elif args.action=='runs': print(json.dumps(runs(),indent=2))
    elif args.action=='report':
        record=get_run(args.run_id)
        if not record: p.error('Unknown run_id')
        alternatives=[get_run(r['run_id']) for r in runs() if r['run_id']!=args.run_id]
        matches=similar_runs(record,alternatives)
        print(json.dumps({'summary':summary(record),'similar_runs':matches,
                          'advisory':analyze(record,matches,force_offline=not args.use_nebius)},indent=2))

if __name__=='__main__': main()

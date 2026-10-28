"""Only Panel2 redraw; never calls projection, reconstruction or evaluation."""
from render_cases import *
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--pair');args=ap.parse_args();done=load(R/'audit/panel2_changes.json')if(R/'audit/panel2_changes.json').exists()else[]
    for r in rows():
        if args.pair and args.pair!=r['pair_id']:continue
        if any(x['pair_id']==r['pair_id']for x in done):continue
        done.append(render_one(r));both('panel2_changes',done);print('PANEL2_ONLY',r['pair_id'],'outside_changed=0',flush=True)
if __name__=='__main__':main()

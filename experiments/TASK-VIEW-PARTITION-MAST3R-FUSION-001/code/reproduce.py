"""Cache-backed reproduction entry. Never implicitly runs neural inference."""
from common import *
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['verify','render-D','index']);a=p.parse_args()
    if a.action=='verify':
        from final_audit import main
        main()
    elif a.action=='render-D':
        from render_d import p8,p9,six_cross,layers,five_panels
        verify();p8();p9();six_cross();layers();five_panels()
    else:
        from report_d import main
        main()

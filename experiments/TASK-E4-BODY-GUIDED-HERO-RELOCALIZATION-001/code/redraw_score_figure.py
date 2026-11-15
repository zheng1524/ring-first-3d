"""Re-render the unchanged metric figure labels; no predictions/evaluation recomputed."""
from visualize import *
import textwrap
s=(R/'code/visualize.py').read_text();block=s[s.index(" met=load(R/'metrics/COMPARISON.json')"):s.index(' # Controls actual surfaces')];groups=['G03','G05','G01','G06'];exec(textwrap.dedent(block),globals())

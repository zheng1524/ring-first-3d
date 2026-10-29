"""Artifact/link/publication-boundary checks; no scientific algorithm calls."""
from common import *
from html.parser import HTMLParser
from urllib.parse import unquote,urlparse
import re
def main():
    rows=[]
    def check(name,ok):rows.append(dict(check=name,passed=bool(ok)));assert ok,name
    for p in (R/'code').glob('*.py'):ast.parse(p.read_text());check('Python syntax '+p.name,True)
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k not in ['href','src']or not v or urlparse(v).scheme or v.startswith('#'):continue
                check('HTML local link '+v,(R/'visualizations'/unquote(v.split('#')[0])).resolve().exists())
    Links().feed((R/'visualizations/index.html').read_text())
    for p in [R/'TECHNICAL_REPORT.md',R/'RESULT_INDEX.md']:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if not urlparse(link).scheme and not link.startswith('#'):check(p.name+' link '+link,(p.parent/unquote(link.split('#')[0])).exists())
    for stage in range(10):
        dirs=list((R/'figures').glob('P'+str(stage)+'_*'));files=[p for d in dirs for p in d.glob('*.png')];check('P'+str(stage)+' has 3–4 core real PNG',3<=len(files)<=4)
        for p in files:
            with Image.open(p)as im:im.verify()
            check(p.name+' valid PNG',True)
    check('Exactly one technical report in new task',len(list(R.rglob('TECHNICAL_REPORT.md')))==1)
    check('No full research assets in publication paths',not any(p.suffix.lower()in['.glb','.ply','.mp4','.pth','.ckpt','.npz']for folder in ['code','config','metrics','provenance','visualizations']for p in (R/folder).rglob('*')if p.is_file()))
    check('All local-only geometry files accounted',all(Path(f['path']).exists()and sha(f['path'])==f['sha256']for f in load(R/'provenance/OUTPUT_INDEX.json')['files']))
    subprocess.run(['git','-C',str(REPO),'diff','--check'],check=True);check('git diff --check',True)
    both('delivery_validation_checks',rows);print('DELIVERY CHECKS',len(rows),'PASS',flush=True)
if __name__=='__main__':main()

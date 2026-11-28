"""Protect complete local 2D process and upload compact fitted evidence separately."""
from common import *
import tarfile

def archive(name,paths,upload):
    paths=sorted(set(paths));destination=T/'evidence'/name;records=[dict(path=str(p.relative_to(T)),sha256=sha(p),bytes=p.stat().st_size) for p in paths]
    with tarfile.open(destination,'w:gz',compresslevel=6) as tf:
        for p in paths:tf.add(p,arcname=str(p.relative_to(T)),recursive=False)
    with tarfile.open(destination) as tf:
        members=tf.getmembers();assert len(members)==len(records)
        for m,r in zip(members,records):assert m.name==r['path'] and hashlib.sha256(tf.extractfile(m).read()).hexdigest()==r['sha256']
    if upload:assert destination.stat().st_size<90*1024**2,'Split evidence without discarding scientific outputs'
    return dict(archive=asset(destination),upload=upload,retain_dependency=True,files=records)

def main():
    core=[]
    for root in ['runs/results','runs/observations','runs/inputs','runs/registration','runs/control']:
        core += [p for p in (T/root).rglob('*') if p.is_file() and p.suffix in ['.npz','.json'] and p.name not in ['FIGURES.json','DISPLAY.json']]
    # Complete small process examples: official A/B, Ring failure pixel outlet,
    # and a true non-solvable pixel case. Full process is separately preserved.
    for case,frame in [('GP_IIa_14.0mm_closed_R5_single_refY_005','raw_000000'),('GP_Ip_10.3mm_closed_R5_single_refY_004','raw_000135'),('GP_Ip_4.0mm_closed_R5_single_refY_005','raw_000038')]:
        core += [p for p in (T/'runs/dxy'/case/frame).rglob('*') if p.is_file()]
    fitted=archive('CORE_RESULTS.tar.gz',core,True)
    all_dxy=[p for p in (T/'runs/dxy').rglob('*') if p.is_file()]
    full=archive('FULL_DXY_PROCESS_LOCAL.tar.gz',all_dxy,False)
    save(T/'evidence/ARCHIVE_MANIFEST.json',dict(core=fitted,full_DXY_local=full,scope='Full local actual process preserved; compact fits/examples uploaded; no upstream RGB/video/weights',extract='tar -xzf evidence/CORE_RESULTS.tar.gz -C .; local full process archive optional',gallery=str(T/'runs/results/index.html'),frame_gallery=str(T/'runs/review/index.html')))
    print('ARCHIVES',fitted['archive']['bytes'],full['archive']['bytes'],len(core),len(all_dxy),flush=True)
if __name__=='__main__':main()

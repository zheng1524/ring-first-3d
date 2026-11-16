"""Small actual-input regression figure; no scientific prediction or GT access."""
from _bootstrap import ROOT
import json
import os
from pathlib import Path
import numpy as np

task=ROOT/"experiments/TASK-RESEARCH-HARNESS-STORAGE-001"
os.environ.setdefault("MPLCONFIGDIR",str(task/"local_only/mpl"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ring_first_3d.rendering.pytorch3d_renderer import MetricRenderer


def main():
    f=json.loads((ROOT/"tools/research/frozen_fixture.json").read_text())
    result=json.loads((task/"SMOKE_AFTER.json").read_text())
    dxy=next(t for t in result["tests"]if t["name"]=="DXY_real_official")["details"]["result"]
    a=np.load(Path(f["real_case_root"])/"inputs"/f["case"]/(f["sample_view"]+".npz"))
    obj=MetricRenderer(f["real_case_root"],f["case"])
    alpha=obj.render(f["sample_view"])["alpha"].detach().cpu().numpy()
    fig,ax=plt.subplots(1,3,figsize=(13.5,3.6),layout="constrained")
    ax[0].imshow(a["RGB"]);ax[0].set_title("Frozen real RGB: G01 / 004 / ref08")
    ax[1].imshow(a["RGB"]);ax[1].contour(a["labels"]==1,levels=[.5],colors=["lime"],linewidths=.8)
    theta=np.linspace(0,2*np.pi,361);uv=np.c_[np.cos(theta),np.sin(theta)]@np.asarray(dxy["basis_px"]).T+np.asarray(dxy["center_px"])
    ax[1].plot(uv[:,0],uv[:,1],color="magenta",lw=1,label="DXY inferred candidate")
    ax[1].plot([],[],color="lime",label="Observed mask boundary")
    ax[1].legend(fontsize=7,loc="lower left");ax[1].set_title("V9.1 Q-conflict recovery; not strict stable")
    ax[2].imshow(alpha,vmin=0,vmax=1,cmap="magma");ax[2].set_title("Frozen metric Body + CAD: rendered alpha")
    for item in ax[:2]:item.set(xlim=(0,639),ylim=(359,0),xlabel="Native x [px]",ylabel="Native y [px]")
    ax[2].set(xlabel="Raster x [px]",ylabel="Raster y [px]")
    fig.suptitle("Engineering regression only | world geometry: mm | source: frozen 014 input pack | GT not read",fontsize=10)
    out=task/"figures";out.mkdir(exist_ok=True);fig.savefig(out/"REAL_SMOKE_EVIDENCE.png",dpi=120)
    print(out/"REAL_SMOKE_EVIDENCE.png")


if __name__=="__main__":main()

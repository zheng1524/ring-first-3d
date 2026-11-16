"""Run the exact historical trainer; only depth video weighting is adapted."""
from _bootstrap import ROOT
from pathlib import Path
import sys,os
legacy=ROOT/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/legacy015'
sys.path.insert(0,str(legacy))
import train_mesh
Base=train_mesh.MultiObjective
class BalancedDepthObjective(Base):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);by={}
  for cid in self.depth.obs:by.setdefault(self.c.views[cid]['meta']['video'],[]).append(cid)
  self.dw={cid:1/len(by)/len(ids)for ids in by.values()for cid in ids}
train_mesh.MultiObjective=BalancedDepthObjective
if __name__=='__main__':train_mesh.main()

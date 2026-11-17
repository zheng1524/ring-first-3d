"""One dimensionally controlled local direction; original physical guard unchanged."""
from strategy import local_directions
from free_model import *
def local_normalized(ch,before,grad):
 old=ch.vertices(before).detach()
 result=[]
 for key,d in local_directions(ch,before,grad):
  move=float((ch.vertices(before+d).detach()-old).norm(dim=1).max())
  if move>1e-15:result.append((key+'_TAU_NORMALIZED',d*(ch.tau/move)))
 return result

"""Independent Task B while G01 BA runs; frozen018 results only, no BA feedback."""
from visualize021 import *
def main():
 for g in ['G03','G05','G06']:
  while not(R/'runtime'/(g+'_QUANTITATIVE_COMPLETE.json')).exists()or not(R/'runtime'/(g+'_SOURCE_GEOMETRY_COMPLETE.json')).exists():time.sleep(5)
  if not(R/'runtime'/(g+'_FIGURES_COMPLETE.json')).exists():group_figures(g)
 print('INDEPENDENT_NON_G01_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':main()

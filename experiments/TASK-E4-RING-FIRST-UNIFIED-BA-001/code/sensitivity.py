"""One preregistered start perturbation. No held/body/HERO selection."""
from joint_ba import *
if __name__=='__main__':
 fit_guard();assert load(N/'STAGE_A_GATE.json')['PASS'];r=load(N/'results/G01/B2/FINAL.json');o=Joint('G01','B3',initial=r);o.H['005'][0]+=.03/.6;o.H['005'][4]+=np.deg2rad(.05)/S[4];o.run('SENSITIVITY/G01_B3_FIXED_PERTURBATION');freeze('provenance/SENSITIVITY_POSE_FROZEN.json',[N/'results/SENSITIVITY/G01_B3_FIXED_PERTURBATION/FINAL.json'],preregistered=True,selected_by_held=False)

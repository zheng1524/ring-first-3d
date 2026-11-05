from common import *
import platform,scipy,subprocess
def main():
    old=REPO/'experiments/E4-SDF-LOCALIZATION-BLENDER-001'
    sources=[dict(role='native CAD GT generation source',**asset(Path('/home/liu/polyp_research/experiments/geometric_validation_v1/assets/IIa6.5.blend')),optimizer_access=False,unit='source vertices meters; world vertices ×1000 then frozen rigid centering, no local edit'),dict(role='native target mesh',**asset(R/'audit_only/NATIVE_CAD_GT.npz'),optimizer_access=False,unit='mm'),dict(role='independent P0 field',**asset(R/'inputs/BASE_FIELD.npz'),optimizer_access=True,unit='mm SDF from Ring-only ellipsoid'),dict(role='independent P0 mesh',**asset(R/'inputs/BASE_SOURCE_MESH.npz'),optimizer_access=True,unit='mm, DMTet'),dict(role='Ring CAD',**asset(R/'inputs/RING_CAD.npz'),optimizer_access=True,unit='mm'),dict(role='frozen cameras',**asset(R/'inputs/CAMERAS.json'),optimizer_access=True,unit='c2w translation mm, K pixel-center and edge conventions explicit')]
    for p in sorted((R/'inputs').glob('*.png')):sources.append(dict(role='actual fixed-scene Blender emission label; not clinical RGB',**asset(p),optimizer_access=p.name.startswith('TARGET'),unit='native 640x360 pixel centers'))
    for name in ['RING_CAD.npz','CAMERAS.json']:assert sha(R/'inputs'/name)==sha(old/'inputs'/name)
    assert sha(R/'inputs/BASE_FIELD.npz')!=sha(old/'inputs/BASE_FIELD.npz')
    gate=load(R/'metrics/PROJECTION_GATE.json');assert gate['passed'];assert load(R/'metrics/FIREWALL.json')['passed']
    cams=load(R/'inputs/CAMERAS.json');FOV=[dict(view=c['id'],horizontal_FOV_deg=float(np.degrees(2*np.arctan(c['width']/(2*np.array(c['K_edge'])[0,0])))),role=c['role'])for c in cams]
    save('assets_index/INPUT_MANIFEST.json',dict(sources=sources,old_BASE_FIELD_prohibited=True,old_synthetic_Targets_not_native_N0=True,native_CAD_q_GT='DOES_NOT_EXIST',FOV=FOV,simulation_camera_qualification='known Blender control extrinsics, not clinical Camera Gate certification',GT_firewall=load(R/'metrics/FIREWALL.json'),software=dict(Python=platform.python_version(),NumPy=np.__version__,SciPy=scipy.__version__,Open3D=o3d.__version__),RA_file='not found in Downloads; task document explicitly sufficient'))
    text='# 来源与GT防火墙审计\n\n本轮为原生CAD N0，非前两轮人工法向/同核目标。仅Gate A；五视角来自一个静止Blender场景，不是五个不同原生病例。原生GT没有四参数q_GT。\n\n'
    text+='|角色|路径|SHA256|单位|优化器可读|\n|---|---|---|---|---|\n'
    for x in sources:text+=f"|{x['role']}|{x['path']}|{x['sha256']}|{x['unit']}|{x['optimizer_access']}|\n"
    text+='\nP0为新建独立低维椭球，由Ring内半径5mm的固定比例规则产生，非原生CAD底场，非某个真实病例的跨坐标P0。九参数定义冻结初始化，优化只更新局部四参数。h=.15mm、核半径1.8mm，无半径搜索；旧1.82mm来自旧控制对象尺寸，未用于N0。\n\n'
    text+=f"相机实际水平视场{FOV[0]['horizontal_FOV_deg']:.6f}°，与名义70°不符。用户已允许选择一致实现，因此保留冻结K/c2w字节，以实际K渲染全部目标和预测。K_edge主点减0.5得到整数像素中心K；c2w_blender=c2w_cv×diag(1,-1,-1,1)，所有几何mm。BASE/TARGET×5投影和Ring门禁均通过，源原始.blend不保存。\n\n"
    text+='防火墙实测拒绝本轮GT、旧GT、旧原生CAD生成BASE_FIELD及.blend，允许本轮独立P0、Ring、相机和二维标签。旧同核GT只在独立的A2诊断脚本中读取，不能在N0优化进程读取。留出目标只做逐轮评价，不进入损失或选模。\n\n开发期旧控制诊断曾出现一个root路径适配遗漏、读到本轮目标Mask；未运行优化，错误输出已封存runtime/PREFLIGHT_WRONG_MASK_ROUTING.*，修复后增加旧GT/FINAL原损失与已冻结历史值逐项一致断言，只有通过回归的诊断才进入最终结果。N0默认root及投影门禁不受此路由遗漏影响。\n'
    (R/'SOURCE_AND_FIREWALL_AUDIT.md').write_text(text)
    print('SOURCE_AUDIT_DONE',FOV,flush=True)
if __name__=='__main__':main()

"""Planning inventory only: existing real image/camera assets, no new inference."""
from common import *
from scipy.spatial.transform import Rotation
def main():
    p=protocol();gate={x['source']:x for x in load(R/'config/CAMERA_GATE_RESULTS.json')['sources']};out=[]
    for v in load(PART/'metrics/view_distribution.json'):
        scene=v.get('group','')+'_'+v.get('source_id','').split('video')[-1]
        if scene not in p['orders']or v.get('type')!='video':continue
        cases=[c for c in CC if CC[c]['scene_id']==scene and CC[c]['reference_index']==v['index']];cid=cases[0]if cases else None;T=np.array(v['c2w']);distances=[]
        for c in p['orders'][scene]:
            t=source(c)['T'];angle=float(np.degrees(Rotation.from_matrix(T[:3,:3]@t[:3,:3].T).magnitude()));distances.append((angle,float(np.linalg.norm(T[:3,3]-t[:3,3])),c))
        near=min(distances);quality=gate[cid]['qualification']if cid else'NOT_TESTED_WITH_CURRENT_GATE';in_fusion=cid in p['orders'][scene]if cid else False
        needed=[]
        if not cid:needed.extend(['current Camera Gate Ring/RGB tests','new original HERO (separate authorization required)','A2 cleanup and exact crop'])
        elif not in_fusion:needed.append('derived current-version cleanup and crop')
        if quality=='INSUFFICIENT_EVIDENCE':needed.append('additional real image correspondence evidence / unresolved qualification')
        if quality=='UNQUALIFIED_GEOMETRY':needed.append('not eligible; resolve actual Ring contradiction before any inclusion')
        if scene=='G01_004':needed.append('independent decoded raw-frame binding; cached image SHA remains exact identity')
        out.append(dict(scene=scene,view_id=v['id'],cached_frame=v['view_id'],raw_frame=CC[cid]['raw_frame']if cid else(int(v['view_id'].split('raw')[-1])if'raw'in v['view_id']else None),frame_binding=v['frame_binding'],RGB_path=v['RGB'],RGB_SHA256=sha(v['RGB']),Mask_path=v['Mask'],block=v['block'],nearest_experiment_source=near[2],relative_rotation_deg=near[0],camera_center_difference_mm=near[1],current_gate=quality,original_HERO_exists=bool(cid),source_id=cid,cleaned_for_this_task=in_fusion,already_fused=in_fusion,new_pose_proxy=near[0]>=2,near_duplicate_proxy=near[0]<2 and near[1]<1,side_information='unverified; pose diversity proxy only',required_computations=needed,enhanced_inference_run=False))
    table('metrics/VIEW_EXPANSION_CANDIDATES.csv',out);save('config/VIEW_EXPANSION_PLAN.json',dict(candidate_N=len(out),candidates=out,counts_by_scene={s:sum(r['scene']==s for r in out)for s in p['orders']},merged_across_groups=False,enhanced_inference_run=False))
    text='# 20–30视角增强采样准备（仅方案）\n\n现有两组共24份真实RGB/Mask/冻结相机候选资产：G01_004为16份，G06_004为8份。**24不是单组可立即融合视角数，也不允许跨物理组混合。** 本轮只完成G01八源/G06五源，增强推理=0。完整逐帧名单、SHA、分区、距本轮输入的姿态差、当前Camera Gate和所需计算见metrics/VIEW_EXPANSION_CANDIDATES.csv。\n\n'
    text+='G01目前11份原生HERO中growth_r01有明确Ring矛盾，不能纳入；其他未选择源仍需当前派生清理，不能用旧融合Mesh渲染深度冒充观测。5份只有RGB/Mask/冻结候选相机的缓存帧需要逐源Gate及新HERO授权。G06只有5份现存HERO，余3帧也需要相同流程。G01原始解码帧号映射存在历史差异；本轮不把缓存004_XX强行解释为raw frame，原图SHA是精确身份。\n\n'
    text+='若下一轮目标是**G01单组20–30个可用视角**，当前16缓存资产还不足；须先补齐真实视频解码身份，按现有block内空缺和新侧面选择额外4–14个真实帧，再执行同一Camera Gate及逐参考HERO。当前不能给这些未选帧伪造姿态差或合格身份。建议先逐一核验当前未用8帧，达到可用分母后提交新的源清单与计算预算，由研究者批准；这份清单不降低Camera Gate标准。\n\n'
    text+='准备顺序：身份/视频帧绑定→真实RGB Ring+匹配资格→按分区/姿态去重→单独授权缺失的HERO→固定A2清理/裁剪→按全保留点冻结域→正序/逆序完整预训练推理。新增侧面仅是预期信息，须以真实新输入支持验证，不以当前NeuralFusion外观选帧。\n\n'
    text+='|场景|缓存候选|当前原生HERO|本轮已清理融合|后续缺失HERO|\n|---|---:|---:|---:|---:|\n'
    for scene in p['orders']:
        aa=[r for r in out if r['scene']==scene];text+=f"|{scene}|{len(aa)}|{sum(r['original_HERO_exists']for r in aa)}|{sum(r['already_fused']for r in aa)}|{sum(not r['original_HERO_exists']for r in aa)}|\n"
    (R/'VIEW_EXPANSION_20_30_PLAN.md').write_text(text)
    print('PLAN_ONLY',len(out),'no enhanced forward')
if __name__=='__main__':main()

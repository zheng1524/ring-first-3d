from common import *
from scipy.spatial.transform import Rotation
def main():
 old=load(R/'config/EXISTING_VIEWS.json');cor=load(R/'config/VIDEO_CORRECTIONS.json');rows=[];r=np.load(R/'inputs/G01/RING.npz');rs=scene(r['V'],r['F'])
 for v in old:
  if v['case']!='G01':continue
  lab=np.array(Image.open(v['Mask_source']));K=np.array(v['K']);T=np.array(v['T']);D=np.array(cor.get(v['sid'],np.eye(4)));ct=contour(lab==2);xy=ct.astype(int);q=ct[cv2.dilate((lab==1).astype(np.uint8),np.ones((5,5),np.uint8))[xy[:,1],xy[:,0]]==0]
  for tag,pose in [('B0',T),('B1',D@T)]:
   z=cast(rs,K,pose,360,640);cp=contour(np.isfinite(z));error=cKDTree(cp).query(q)[0]if len(cp)and len(q)else[];rows.append(dict(view=v['id'],sid=v['sid'],arm=tag,observed_qualified_boundary_N=len(q),Ring_raw_pixel_error=stats(error),CAD_Ring_IoU=float(((lab==2)&np.isfinite(z)).sum()/max(1,((lab==2)|(np.isfinite(z)&(lab!=1))).sum()))))
 table('metrics/POSE_RING_NATIVE_AUDIT.csv',rows);save('metrics/POSE_RING_NATIVE_AUDIT.json',rows)
 refs={}
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];v=next(x for x in old if x['case']==n and x['original013']);refs[n]=dict(reference_video=v['video'],rule='frozen 013 original-HERO coordinate frame; G01 explicitly004; no GT',identity=np.eye(4))
 save('config/REFERENCE_VIDEOS.json',refs)
 cross=load(R/'metrics/pose/G01_004_TO_005.json');neg=load(R/'metrics/pose/G01_004_TRUE_RAW_TIME_SPLIT_NEGATIVE.json');b=cross['selected_FIT_only'];nn=neg['selected_FIT_only'];rv=np.array(b['x']);nv=np.array(nn['x']);text=f'''# 视频级位姿修正：部分证据，未认证

G01参考004固定Identity；005一个共享SE3候选，旋转向量(deg)={np.degrees(rv[:3]).tolist()}，平移(mm)={rv[3:].tolist()}，无尺度。原相机只读，派生T单独存储。目标仅实际背景SIFT三角化点、Ring CAD及先验，未读HERO息肉几何或GT，Mesh冻结。

原始背景留出MAE {cross['original_held_BG_px']['MAE']:.3f} px → {b['held_background_px']['MAE']:.3f} px，中位 {b['held_background_px']['median']:.3f} px，p95 {b['held_background_px']['p95']:.3f} px。FIT背景{cross['fit_BG_N']}，留出{cross['held_BG_N']}，空间格{cross['image_cells']}；近最优多初值参数差{cross['near_optimum_parameter_spread']:.6f}。相对改善和多初值稳定并不证明绝对正确；仍有大残差、错误匹配/背景非刚性/原相机误差的混合可能。反向005→004的FIT对应仅18点，不足以支持独立修正；反向原始投影证据保留。

真正按原始时间分半的004负对照：留出MAE {neg['original_held_BG_px']['MAE']:.3f}→{nn['held_background_px']['MAE']:.3f} px，仍产生{np.linalg.norm(nv[3:]):.3f} mm、{np.degrees(np.linalg.norm(nv[:3])):.3f}°修正。不是零漂移PASS，说明背景/相机/三角化噪声可被6DoF部分吸收。早先缺失时间戳的档案排序对照文件保留，但不作为时间负对照证据。

B1作为明确标识的研究候选用于派生005相机；不能称正式相机修复。B2需要充分独立证据，当前NOT_EVALUABLE，不执行交替拟合。Ring原生像素误差见metrics/POSE_RING_NATIVE_AUDIT.csv；旧求解日志的归一Ring残差不是原生像素误差，不混用。004→005、005→004原始背景匹配逐点保留在metrics/pose，后续同共享Mesh检查稳定性，不能期待005新增明显面积。

其他组现有参考视频固定；第二视频没有历史公制pose时，以真实背景RGB地标PnP派生新pose，记录其来源，不伪称视频级修正了不存在的原始轨迹。G08-video006背景PnP无解，所有40候选保留为缺相机，不能任意指定Ring对称轴yaw拼入统一Mesh。
''';(R/'POSE_CORRECTION_REPORT.md').write_text(text)
if __name__=='__main__':main()

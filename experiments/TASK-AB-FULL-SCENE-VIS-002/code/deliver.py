"""Public four PNGs, full local gallery and one report; no geometry changes."""
from common import *
import html
from PIL import ImageDraw,ImageFont
TASK='TASK-AB-FULL-SCENE-VIS-002';FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def composite(paths,dest,width=2400,title=''):
    ims=[]
    for p in paths:
        im=Image.open(p).convert('RGB');im=im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS);ims.append(im)
    out=Image.new('RGB',(width,sum(im.height for im in ims)+90),'white');dr=ImageDraw.Draw(out);dr.text((18,15),title,font=ImageFont.truetype(FONT,27),fill='black');y=90
    for im in ims:out.paste(im,(0,y));y+=im.height
    out.save(R/dest)
def table(headers,rows):
    def f(x):return'NaN'if x is None else f'{x:.2f}'if isinstance(x,float)else str(x).replace('|','/')
    return'\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(f(x)for x in r)+' |'for r in rows])
def main():
    rows=load(R/'metrics/results.json');assert len(rows)==11;get=lambda pid:next(r for r in rows if r['pair_id']==pid);figs=R/'figures';figs.mkdir(exist_ok=True)
    cross1='G01_004_ref08__to__video005_v005_00516';cross2='G01_005_raw00459__to__video004_004_10';photo='G01_005_raw00459__to__photo_003_LG490_candidate';groupids=['G06_004_ref04__to__key01_raw00229','G08_005_ref04__to__key00_raw00120','G07_004_ref04__to__key00_raw00066']
    composite([R/get(x)['figures']['Five_Panels.png']for x in [cross1,cross2]],'figures/Fig1_G01_crossvideo_full_scenes.png',2400,'G01 双向跨视频完整场景｜22.60° / 23.25°｜CANDIDATE_ONLY，未融合')
    composite([R/get(photo)['figures']['Five_Panels.png']],'figures/Fig2_photo003_large_angle_candidate.png',2880,'video005→photo003｜39.29° CANDIDATE_ONLY｜真实孔洞、错位与背景断裂保留')
    composite([R/get(x)['figures']['Five_Panels.png']for x in groupids],'figures/Fig3_multigroup_full_scene_diagnostics.png',2400,'G06 / G08 / G07 完整场景｜NORMAL / LIMITED目标未筛查 / UNQUALIFIED压力测试')
    old=next(x for x in load(AUDIT/'metrics/a_to_b_results.json')if x['pair_id']==cross1);composite([AUDIT/old['figure'],R/get(cross1)['figures']['Five_Panels.png']],'figures/Fig4_old_new_same_pair.png',2880,'同一A/B与冻结H｜上：旧Polyp-only；下：完整点云场景；原Polyp数值完全一致')
    public=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(figs.glob('Fig*.png'))];assert len(public)==4;save('metrics/PUBLIC_FIGURES.json',public)
    # Angle audit compares trajectory maxima to actual frozen P0-source availability.
    prior=load(AUDIT/'metrics/view_coverage_summary.json');angles=[]
    for g,v in [('G01','004'),('G01','005'),('G06','004'),('G08','005'),('G07','004')]:
        vv=next(x for x in prior if x['source']==g+'_video'+v);rr=[p for p in load(R/'metrics/pair_selection.json')if case(p['A'])['group']==g and case(p['A'])['video']==v and'CANDIDATE'not in p['pose_status']];angles.append(dict(group=g,video=v,all_frozen_camera_trajectory_max_angle_deg=vv['within_source_max_optical_angle_deg'],maximum_selected_available_P0_angle_deg=max(x['optical_axis_angle_deg']for x in rr),quality=vv['quality'],limitation='Camera-trajectory endpoint need not have P0; target quality retained, no P0 recomputation'))
    both('large_angle_summary',angles)
    summary=table(['组/来源A→B','角度°','姿态状态','原Polyp三角面覆盖 / MAE','新P点覆盖 / MAE','新BG点覆盖 / MAE','源BG点数'],[[r['pair_id'],r['angle_deg'],r['pose_status'],f"{r['legacy_Polyp_only']['target_coverage']:.1%} / {r['legacy_Polyp_only']['RGB_MAE_0_255']:.2f}",f"{r['new_point_scene']['Polyp_target_coverage']:.1%} / {r['new_point_scene']['Polyp_RGB_MAE']:.2f}",f"{r['new_point_scene']['Background_target_coverage']:.1%} / {r['new_point_scene']['Background_RGB_MAE']:.2f}",r['source_BG_N']]for r in rows])
    angle_table=table(['组/视频','轨迹最大°','本轮已有P0可用最大°','相机条件'],[[x['group']+'/'+x['video'],x['all_frozen_camera_trajectory_max_angle_deg'],x['maximum_selected_available_P0_angle_deg'],x['quality']]for x in angles])
    folder=R/'visualizations';folder.mkdir(exist_ok=True);href=lambda p:html.escape(os.path.relpath(p,folder),quote=True);htmlparts=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>'+TASK+'</title><style>body{max-width:1700px;margin:auto;padding:24px;font:16px sans-serif}img{width:100%;height:auto}article{border-top:2px solid #ccc;margin:30px 0}a{color:#12579c}</style><h1>'+TASK+'</h1><p>Polyp + 黑色实体CAD Ring + 实际Background XYZ。背景DISPLAY_ONLY；跨源CANDIDATE；无新重建或精度改善声明。</p>']
    for label,p in [('技术报告',R/'TECHNICAL_REPORT.md'),('完整结果索引',R/'RESULT_INDEX.md'),('原Polyp指标',R/'metrics/legacy_polyp_metrics.csv'),('新点云场景独立指标',R/'metrics/scene_point_metrics.csv'),('大角度及限制',R/'metrics/large_angle_summary.csv')]:htmlparts.append(f'<p><a href="{href(p)}">{label}</a></p>')
    htmlparts.append('<p>按物理组： '+' | '.join(f'<a href="#'+g+'">'+g+'</a>'for g in ['G01','G06','G08','G07'])+'</p>')
    for g in ['G01','G06','G08','G07']:
        htmlparts.append(f'<h2 id="{g}">{g}</h2>')
        for r in sorted((x for x in rows if x['group']==g),key=lambda x:-x['angle_deg']):
            p=R/r['figures']['Five_Panels.png'];htmlparts.append(f'<article><h3>{html.escape(r["pair_id"])} — {r["angle_deg"]:.2f}° / {r["baseline_mm"]:.2f} mm</h3><p>{html.escape(r["pose_status"])}；BG DISPLAY_ONLY。<a href="{href(R/r["figures"]["Real_B_vs_Full_AtoB_Scene.png"])}">高分辨率B与完整场景</a> | <a href="{href(R/r["figures"]["Actual_XYZ_side_views.png"])}">实际XYZ侧/斜视与相机关系</a> | <a href="{href(Path(r["source_geometry_path"]))}">实际分层XYZ/UV（本地）</a></p><a href="{href(p)}"><img src="{href(p)}" loading="lazy"></a></article>')
    for p in public:htmlparts.append(f'<article><h2>{html.escape(p["path"])}</h2><a href="{href(R/p["path"])}"><img src="{href(R/p["path"])}" loading="lazy"></a></article>')
    htmlparts.append('</html>');(folder/'index.html').write_text('\n'.join(htmlparts))
    source_renderers=[REPO/'visualization'/n for n in ['real_p0_renderer.py','same_camera_scene.py','pointcloud_audit_renderer.py']]+[HIST/'code/scene004.py',AUDIT/'code/reprojection.py'];save('provenance/RENDERER_VERSIONS.json',stamp(source_renderers,upstream_modules_modified=False,legacy_kernels_extracted_by_AST=True))
    report=f'''# {TASK}

用户任务标题：TASK-VIEW-OBSERVABILITY-AB-SCENE-VIS-002。状态 **REPORTED / VISUALIZATION RESTORED — 科学一致性未认证**。2026-10-28（Asia/Shanghai）。

## 中文摘要

本轮复用已有真实场景渲染器和冻结背景XYZ，恢复了四个物理组、11组A→B的息肉、实体参考环与局部背景展示。第2面板统一灰色离散点，第4面板仅采用源A的RGB，黑色CAD按实际几何和预测深度遮挡；原Polyp-only三角面指标完整保留，新增点云/背景指标使用独立分母。大角度样例包括同视频24.03°、14.52°以及跨视频22.60°/23.25°和照片候选39.29°。场景展示工程恢复成功，但大角度预测仍有孔洞、错位和背景断裂，G07继续是不合格相机压力测试。全部P0、背景点坐标、相机、HERO、融合与测量代码保持不变，未读取GT，未宣称重建精度改善。

## 入口与来源

本地根目录：`{R}`。 [HTML图库]({folder}/index.html) · [全部案例图]({R}/figures/cases/) · [完整索引](RESULT_INDEX.md)。分支`exp/{TASK}`，起始HEAD `432747735aad5df46df32a93f78b3c819c7797ed`，真实独立worktree `{REPO}`；旧任务及其未公开数据仍在原路径，只读。首阶段源码/选帧冻结提交`0d4285c`。

已读取AGENTS、COLLAB_STANDARD、README、BASELINE状态和FINAL_AUDIT历史副本。正式baseline仍未认证；用户本轮明确授权仅展示封装，不将治理状态改为科学验收。

历史完整场景位于 `{HIST}/local_scenes/G01_004_same_camera_ref03/`，包含Local_3D_Scene.png、Real_vs_3D.png、Background_FULL_DISPLAY_ONLY.npz和Point_layers_and_source_ids.npz，均已实际找到。历史背景与当前ref03冻结缓存的XYZ及RGB **逐值相同**。上一轮退化源于仅传P0/开放面、遗漏背景输入、CAD只做遮挡；历史模块仍完整，不是重新设计渲染风格。

## 封装与物理坐标

`real_p0_renderer.py`提供原点绘制、冻结K/c2w和像素中心缩放；`SameCameraScene.draw()`对Polyp/Background使用同一个点artist、源RGB、远近排序及CAD逐射线遮挡；`ring_image()`使用原OBJ三角面命中、法向黑色着色与alpha1。`pointcloud_audit_renderer`提供侧视真实XYZ方法。版本和SHA见[RENDERER_VERSIONS](provenance/RENDERER_VERSIONS.json)。这些正式可视化模块原样未改。

所有点保存A原始毫米坐标与源UV。背景直接读旧NPZ display_mask：源基底代理附近较大椭圆（scale2，短长轴比.75）、12px接触带及旧源空间远端限制；无新世界Z截断、无B指导裁切、无坐标移动。完整原背景缓存保持不变，派生选择可反查缓存原索引。标签 **BACKGROUND_FROM_FROZEN_DEPTH — DISPLAY_ONLY** 不表示背景独立可靠。

跨视频/照片显示采用`c2w_B_in_A = inv(H_A_to_B) @ c2w_B`。源A Polyp、Background、Ring都保留原坐标；不把CAD独立吸附到B，也不改变半径、法向或尺度。相同投影等价于整场景应用既有H；候选H没有优化。其CAD遮挡与原Polyp-only内核的目标局部CAD口径有差异，因此新旧指标严格分列。

Panel2没有源RGB着色；统一灰`.58`，点大小`.08`和关闭抗锯齿沿用已有稀疏审计设置，使点间距可观察。Panel4保持历史scene004 RGB点大小`.8`与不透明绘制。首张灰点`.8`样图因点过密不利检查，原样保留在本地first_display_sample，仅调整显示配置；XYZ/ROI/相机/评价规则完全没变。1280×720只进行像素中心保持的K缩放，不重估相机。所有无支持区域明确留空，无平滑、补面、额外点或纹理平面。

## 配对、大角度与限制

11配对在本轮场景误差前按冻结相机、可读RGB/Mask、Ring/Polyp可见和既有质量固定。[完整选帧清单](metrics/pair_selection.csv)及[冻结参数](provenance/PAIRS_FROZEN.json)保留所有矩阵与理由。没有按本轮误差或渲染美观择优。

{angle_table}

轨迹最大角度两端不必有独立P0，故不重建新源面来凑角度。G06除14.29°已筛查目标外，保留16.94°未筛查目标。G08 12.79°目标仅MODEL_PREDICTED，标记FROZEN_LOCAL_TARGET_UNSCREENED，不能称可靠大角度。G07 2.87°是其当前源P0最大可用，整个相机不合格，仅UNQUALIFIED_CAMERA_STRESS；较好RGB分数不改变身份。保留0.65°小角度对照。

跨视频22.60°、23.25°和照片39.29°均明确CANDIDATE_ONLY；没有获得可靠跨视频注册或照片光学模式标定。这些基线/角度仅为候选条件量，照片目标曾参与历史候选位姿拟合，本轮图像不是新的独立相机认证。004原视频raw帧号历史存在近似绑定，引用固定缓存key+RGB SHA，不猜测新raw编号。

## 五面板与数值隔离

布局改为上两行2×2完整视场，第5面板四项横向展开：50%叠加、支持/未覆盖/外逸、分层有效差异、实际XYZ侧视。另11张3200×1070的Real_B_vs_Full_AtoB_Scene.png及11张三方向/相机关系侧视图供放大；主图2880×2484。灰点面板和RGB面板都包含全部保留P0、源背景及实体CAD；未知区域和错误深度不隐藏。

**原Polyp-only指标**：对四个已有配对复用旧NPZ，逐字段核验与上一轮相等；其他7配对从旧reprojection.py精确AST调用相同三角面投影/评价内核，源A顶点RGB、原面、全B Polyp Mask分母及.05mm目标局部CAD容差保持不变。BG没有进入这个预测或分母。[原口径表](metrics/legacy_polyp_metrics.csv)。

**新场景点云诊断**：640×360整数像素中心最近点z-buffer、源CAD .002mm遮挡，颜色为命中原点的A源RGB，Polyp与BG分别统计。BG目标ROI规则预先固定：B Polyp Mask图像下方20%像素中位UV，半长轴2×max(Polyp半宽,Ring半宽)，短轴.75倍，仅B label0且在椭圆为背景分母。B RGB/Mask只在A预测写盘后读取作评价，不生成颜色、不决定A点保留。BG ROI只是局部图像支持，不是独立三维组织对应GT。

新P/BG的分母、未覆盖、ROI外预测、BG投到B Polyp及P投到B BG均分开保存；不删除外逸点来压误差。图中红色表示评价ROI外或类别不符，不是真实错误标签。点中心数值支持与`.8`显示标记占像素范围不同，不能把显示面积当点覆盖。新旧MAE不得直接作“性能提升”比较：采样、可见性和支持集不同。

{summary}

全部RGB MAE单位为0–255；新P/BG只有各自有效共同支持区计算。未覆盖不计误差但单独报告；完整分母见两份CSV。没有报告清理成功率、三维精度或物理测量改善。

## 真实诊断与验收结论

**展示封装工程验收：已恢复，11/11配对、4/4物理组都有Polyp+实际背景XYZ+黑色实体CAD完整五面板；最终人工视觉验收待PM与研究者完成。** 第2面板实际中性灰，背景/息肉同绘制方法；第4只用源A RGB，Ring具有真实厚度与深度遮挡。

科学/几何一致性没有因此通过：G01 24.03°的新点云P覆盖40.6%、BG42.2%；39.29°照片候选P36.0%、BG41.3%，明显孔洞、重复/错位和局部背景断裂保留。004→005新点P75.7%、BG70.4%，反向59.4%/63.4%；候选变换仍未认证。G06筛查14.29°场景相对一致（P92.2%、BG78.1%，对应MAE约9.00/10.04），但不能当绝对精度证明。G08背景缺口与目标相机限制、G07不合格相机均保留。

source背景与Polyp的真实预测间隙在侧视清楚可见；没有强行连接。Ring边缘在正侧视可呈细横向截面，这是该实体几何的真实侧向投影，主相机图与斜视同时提供完整圆环。

![双向跨视频完整局部场景](figures/Fig1_G01_crossvideo_full_scenes.png)

![39.29度照片候选及真实失败](figures/Fig2_photo003_large_angle_candidate.png)

![G06 G08 G07统一场景诊断](figures/Fig3_multigroup_full_scene_diagnostics.png)

![同配对旧新版，旧数值未变](figures/Fig4_old_new_same_pair.png)

## 科研边界审计

| 审计项目 | 本轮结果 |
| --- | --- |
| 目标组数 | 4独立物理组，11配对；G01两视频不计两病例 |
| 本算法独立成功 | 仅展示工程11/11；本轮不生成测量预测，无正式几何成功认证 |
| 本算法失败 | 大角度和跨源孔洞/错位保留；G07压力测试；物理指标评价NOT_APPLICABLE |
| 历史测量值回退 | 0；只保留同一路线旧Polyp投影对照，不读取其他测量值 |
| 失败组及原因 | G01跨视角支持/注册候选，G08未筛查目标与背景缺口，G07相机不合格；每组完整图与侧视可查 |
| 最终统计样本 | 11展示配对、4物理组，非独立病例测量准确率；P/BG/旧口径各有分母 |
| 是否使用GT选择算法 | 否，GT_NONE；读取防火墙禁止GT/Oracle几何；无新算法/姿态优化 |

本轮正式renderer、P0、HERO、Ring-First、清理、融合、Dxy、高度和GT评价方法均未修改。完整NPZ/大图本地保存，GitHub仅公开源码、参数、表、4精选PNG与报告。完成后停止，等待人工审查。
'''
    (R/'TECHNICAL_REPORT.md').write_text(report)
    result=f'''# {TASK} 结果索引

本地绝对目录：`{R}`

[直接打开HTML图库]({folder}/index.html) · [完整案例文件夹]({R}/figures/cases/) · [本地报告]({R}/TECHNICAL_REPORT.md) · [复现](REPRODUCE.md)。图库按G01/G06/G08/G07和角度排序，包含11张五面板、11张高分辨率Real_B_vs_Full_AtoB_Scene.png、11张侧/斜视和A/B相机关系图；所有大图LOCAL_ONLY。

公开核心图：

1. [双向跨视频22.60°/23.25°完整场景](figures/Fig1_G01_crossvideo_full_scenes.png)
2. [photo003 39.29°候选与失败](figures/Fig2_photo003_large_angle_candidate.png)
3. [G06/G08/G07三组统一诊断](figures/Fig3_multigroup_full_scene_diagnostics.png)
4. [同配对旧/新版完整对照](figures/Fig4_old_new_same_pair.png)

[旧Polyp-only指标](metrics/legacy_polyp_metrics.csv) · [新点云场景独立指标](metrics/scene_point_metrics.csv) · [逐项结果及大图路径](metrics/results.json) · [大角度限制](metrics/large_angle_summary.csv) · [实际源帧/坐标](metrics/source_coordinate_inventory.csv) · [冻结选帧](metrics/pair_selection.csv) · [渲染器版本SHA](provenance/RENDERER_VERSIONS.json) · [本地资产SHA](metrics/LOCAL_ASSET_INDEX.csv)。

公开目录：https://github.com/zheng1524/ring-first-3d/tree/exp/{TASK}/experiments/{TASK} 。背景是冻结预测XYZ、DISPLAY_ONLY，跨源关系仍CANDIDATE；不是融合或重建性能改善。
''';(R/'RESULT_INDEX.md').write_text(result)
    (R/'REPRODUCE.md').write_text(f'''# 复现

环境：既有Python3.12、Open3D0.19旧vendor、Matplotlib及原项目renderer，不安装环境或运行模型。原输入和所有参数SHA见provenance。当前目录只作已交付验证，不覆盖重放。

```bash
cd {REPO}
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/{TASK}/code/validate.py
```

重新生成请将本任务源码/配置放在新空实验目录：prepare.py（冻结11配对与输入）→test_small.py→render_cases.py→deliver.py→validate.py。所有R由脚本位置派生；没有GT、HERO或完整重建入口。正式renderer和旧缓存均只读。最终显示配置已包含灰点.08/关闭抗锯齿，RGB点.8；redraw_geometry.py仅为首次展示审查后的灰点显示修订，不改变任何数值预测/支持。

本轮实际还先单独渲染22.60°样图检查，保留初始样图后完成批量；其余阶段与上面一致。没有声称做了第二次完整重放。旧四配对预测直接复用并逐字段等同，其余7使用同一原内核。
''')
    files=[p for base in ['figures','local_results']for p in (R/base).rglob('*')if p.is_file()];both('LOCAL_ASSET_INDEX',[dict(path=str(p),relative_path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,publication='PUBLIC_CORE'if p.parent==R/'figures'else'LOCAL_ONLY')for p in sorted(files)])
    print('DELIVERY_GENERATED',len(rows),'cases /4 groups /4 core PNG',[(p['path'],p['bytes'])for p in public])
if __name__=='__main__':main()

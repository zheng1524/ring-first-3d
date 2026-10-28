"""Preserve public Fig2 outside Panel2; compact comparison and local gallery."""
from common import *
import html
from PIL import ImageDraw,ImageFont
TASK='TASK-AB-SCENE-PANEL2-DEPTH-COLOR-003'
def main():
    changes=load(R/'audit/panel2_changes.json');assert len(changes)==11;pid='G01_005_raw00459__to__photo_003_LG490_candidate';r=next(x for x in changes if x['pair_id']==pid);oldcase=np.asarray(Image.open(r['old_figure']).convert('RGB'));newcase=np.asarray(Image.open(R/r['new_figure']).convert('RGB'));oldcore=np.asarray(Image.open(PREV/'figures/Fig2_photo003_large_angle_candidate.png').convert('RGB'));assert np.array_equal(oldcore[90:],oldcase);newcore=oldcore.copy();x0,y0,x1,y1=r['allowed_panel2_rectangle_xyxy'];newcore[y0+90:y1+90,x0:x1]=newcase[y0:y1,x0:x1];mask=np.ones(oldcore.shape[:2],bool);mask[y0+90:y1+90,x0:x1]=False;assert np.array_equal(newcore[mask],oldcore[mask]);dest=R/'figures/Fig2_photo003_large_angle_candidate_depth_color.png';Image.fromarray(newcore).save(dest)
    save('audit/CORE_FIG2_PIXEL_AUDIT.json',dict(original=str(PREV/'figures/Fig2_photo003_large_angle_candidate.png'),new=str(dest),allowed_rect=[x0,y0+90,x1,y1+90],changed_pixels_outside_Panel2=0,original_header_and_all_other_panels_pixel_identical=True))
    a=Image.fromarray(oldcase[y0:y1,x0:x1]);b=Image.fromarray(newcase[y0:y1,x0:x1]);gap=16;out=Image.new('RGB',(a.width+b.width+gap,a.height+80),'white');dr=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',21);dr.text((12,8),'修改前：同相机统一灰色点云',font=font,fill='black');dr.text((a.width+gap+12,8),'修改后：粉红/蓝绿，共享A轴向Z深浅',font=font,fill='black');dr.text((12,40),'Panel 2 对照；XYZ/点大小/相机/CAD不变，完整五面板其他区域0像素变化。',font=font,fill='black');out.paste(a,(0,80));out.paste(b,(a.width+gap,80));out.save(R/'figures/Fig2_Panel2_before_after.png')
    g6=next(x for x in changes if x['pair_id']=='G06_004_ref04__to__key01_raw00229');Image.open(R/g6['new_figure']).save(R/'figures/Fig3_G06_panel2_depth_color.png');pub=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted((R/'figures').glob('*.png'))];assert len(pub)==3;save('audit/PUBLIC_FIGURES.json',pub)
    gallery=R/'visualizations';gallery.mkdir(exist_ok=True);href=lambda p:html.escape(os.path.relpath(p,gallery),quote=True);parts=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>'+TASK+'</title><style>body{max-width:1600px;margin:auto;padding:24px;font:16px sans-serif}img{width:100%;height:auto}article{border-top:1px solid #ccc;margin-top:28px}a{color:#1763a3}</style><h1>Panel 2：粉红/蓝绿 + 相机轴向Z</h1><p>仅颜色和必要图例变更。近亮、远暗，两层共用每个A场景Z范围；黑色CAD不变。其余面板逐像素保持原图。无重建/配准/深度预测或评价重跑。</p>']
    for label,p in [('技术报告',R/'TECHNICAL_REPORT.md'),('结果索引',R/'RESULT_INDEX.md'),('逐图像素检查',R/'audit/panel2_changes.csv')]:parts.append(f'<p><a href="{href(p)}">{label}</a></p>')
    for r0 in pub:parts.append(f'<article><h2>{html.escape(r0["path"])}</h2><a href="{href(R/r0["path"])}"><img loading="lazy" src="{href(R/r0["path"])}"></a></article>')
    for c in changes:
        z=c['depth'];parts.append(f'<article><h2>{html.escape(c["pair_id"])}</h2><p>{c["angle_deg"]:.2f}° | {html.escape(c["pose_status"])}；A轴向Z {z["min_Z_mm"]:.4f}–{z["max_Z_mm"]:.4f} mm；P/BG点数 {z["Polyp_N"]}/{z["Background_N"]}；其他区域变化0像素。<a href="{href(Path(c["old_figure"]))}">原图</a> | <a href="{href(R/c["new_geometry"])}">新版实际几何绘制</a></p><a href="{href(R/c["new_figure"])}"><img loading="lazy" src="{href(R/c["new_figure"])}"></a></article>')
    parts.append('</html>');(gallery/'index.html').write_text('\n'.join(parts))
    rows_=['| 配对 | A轴向Z范围 mm | P / BG点数 | Panel2外变化像素 |','| --- | --- | --- | --- |']
    for c in changes:
        z=c['depth'];rows_.append(f'| {c["pair_id"]} | {z["min_Z_mm"]:.4f}–{z["max_Z_mm"]:.4f} | {z["Polyp_N"]} / {z["Background_N"]} | 0 |')
    table='\n'.join(rows_)
    report=f'''# {TASK}

状态：REPORTED / PANEL2_ONLY；等待人工验收。2026-10-28（Asia/Shanghai）。

本轮仅将已认可五面板中的第2面板由灰色点云改为粉红Polyp与蓝绿Background，并用两色系内的明暗表达已有预测XYZ在冻结A相机下的轴向深度。先完成39.29° photo003，再对全部11配对复用。两类点共享同一A场景全部有效XYZ的Z最小/最大值，同一个A在不同B配对中使用相同颜色；未按图层独立归一化、未删极值、未重新估计深度。黑色实体CAD、点坐标、点数、点大小、遮挡与相机均不变。原图保留，新图逐像素复制其余区域，11/11张Panel2及必要图例之外变化均为0。全部历史评价文件只核对哈希，没有重新运行评价。候选姿态、背景DISPLAY_ONLY和相机压力测试身份原样保留，不产生新的科研精度结论。

本地目录：`{R}`。 [HTML图库]({gallery}/index.html) · [全部新版]({R}/figures/cases/) · [结果索引](RESULT_INDEX.md)。独立分支`exp/{TASK}`，起始提交`d969bd064e980ab0ca6af3b4d0e6f2e5a1bb1818`。旧任务脚本、官方renderer及旧图片均未改。

## 颜色与深度

读取已有source_layers NPZ，不重新生成点或背景。`Z=((XYZ-C_A) @ R_A)[:,2]`，单位mm。每个源A的Polyp和Background全部有限正Z共同构成范围；`t=(Z-Zmin)/(Zmax-Zmin)`，近端HLS明度0.82、远端0.27，饱和度0.70；Polyp色相340°，Background170°。两层共享t与明度公式。没有百分位裁剪，没有改变任何深度数值。此Z是冻结重建的相机轴向深度，不是独立GT或新深度预测。

photo003案例共享范围35.6454–54.0253mm，Polyp12775点、Background37751点。物理毫米比例尺仍是原Ring平面参考尺度。

{table}

## 严格不变范围

复用原SameCameraScene.draw、real_p0_renderer投影、点排序和CAD射线遮挡；Panel2点大小仍.08、alpha1、关闭抗锯齿，K缩放、c2w和Ring不变。先用原灰色图复绘Panel2位置，控制图与旧PNG逐像素一致；再仅替换该精确矩形，图例位于原Panel2下方白色间隙，不移动轴框、不覆盖Ring。

新版Fig2由旧公开Fig2直接复制，仅替换同一Panel2区域，原90px标题栏、Panel1/3/4/5及数值注释逐像素不变。黑色可见CAD像素另逐点检查保持相同。单独前后对照图仅并排显示Panel2，完整原图仍可在图库打开。

历史指标、预测缓存、背景ROI与源几何共128个输入文件在开始时冻结SHA；结束时再次核验。没有调用旧point_projection、scene_metrics、legacy.evaluate或任何重建/配准/测量流程。新audit目录仅存像素与显示审计，不是新的科研评价指标。

![新版Fig2](figures/Fig2_photo003_large_angle_candidate_depth_color.png)

![Panel2修改前后](figures/Fig2_Panel2_before_after.png)

![G06同规则示例](figures/Fig3_G06_panel2_depth_color.png)

源相机密集采样处仍可能形成连续色块外观，实际绘制的是同一批离散XYZ，没有补面/平滑。旧跨源候选与背景几何缺陷保留；本轮不评判或修正它们。

## 修改文件与复现

所有代码均新增于本任务目录：`code/scene_renderer.py`仅做共享Z配色并复用原点/CAD接口；`code/render_cases.py`定位原Panel2与必要图例、复制其他像素；`code/redraw_geometry.py`只迭代已有11配对。`prepare.py`、`test_small.py`、`validate.py`、`deliver.py`为冻结/核查/交付辅助。旧scene_renderer.py/render_cases.py/redraw_geometry.py文件字节不变。

```bash
cd {REPO}
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/{TASK}/code/validate.py
```

新空输出目录重放顺序：prepare.py → redraw_geometry.py --pair G01_005_raw00459__to__photo_003_LG490_candidate → test_small.py → redraw_geometry.py → deliver.py → validate.py。不得在已冻结旧任务目录覆盖生成。没有完整重建或评价入口。

验收依据为11/11外部像素差0、Ring保持、颜色深度单调与共享范围、所有冻结输入哈希不变；完整审计见`audit/VALIDATION.json`与`audit/panel2_changes.csv`。本轮不产生测量结果、不使用GT、不修改正式Dxy。完成后停止。
''';(R/'TECHNICAL_REPORT.md').write_text(report)
    (R/'RESULT_INDEX.md').write_text(f'''# {TASK} 结果索引

本地可视化文件夹：`{gallery}`

[打开HTML]({gallery}/index.html) · [11个新版五面板]({R}/figures/cases/) · [技术报告](TECHNICAL_REPORT.md) · [逐图像素审计](audit/panel2_changes.csv) · [冻结输入SHA](provenance/INPUTS_FROZEN.json)。

- [新版Fig2](figures/Fig2_photo003_large_angle_candidate_depth_color.png)
- [修改前后对照](figures/Fig2_Panel2_before_after.png)
- [G06新版示例](figures/Fig3_G06_panel2_depth_color.png)

每个案例的旧图绝对路径、新图路径、深度范围、点数和不变像素检查见audit/panel2_changes.json。全部旧图/评价数据保留于原任务`{PREV}`，本轮不复制或重写历史指标。

GitHub分支：https://github.com/zheng1524/ring-first-3d/tree/exp/{TASK} 。完整11张图保留本地，公开三张核心PNG。
''')
    files=sorted(p for base in ['figures','local_results']for p in (R/base).rglob('*')if p.is_file());both('LOCAL_ASSET_INDEX',[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,publication='PUBLIC_CORE'if p.parent==R/'figures'else'LOCAL_ONLY')for p in files]);print('DELIVERED',len(changes),'cases,3 public PNG')
if __name__=='__main__':main()

# TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001

![2D to real 3D vertex evidence](visualization/figures/Fig1_2D_TO_3D.png)

A3: original013 + frozen004/005 + explicit normal contour constraints, no HERO depth. A2 frozen historical baseline. A2D removes depth but keeps historical direct contour loss, isolating the new correspondence mechanism. No camera optimization. All trained arms use original train_mesh optimizer/FreeVertices/RingAware/guard/budget and final accepted Mesh.

GT uses best_rigid015 scale1 SE3 on frozen evaluation copies only; source-world Body is unchanged and is used by HERO.

H1=A2+ellipse; H2=A3+ellipse; H3=A2+actual Mesh boundary; H4=A3+actual Mesh boundary. Same sources, transforms budget and 0.5mm Body tolerance. Actual triangles remain rigid; cameras and Body fixed. Boundary transfer is only a candidate constraint; not a physical surface replacement.

**本轮判定：显式二维对应相对公平无深度对照仅有小幅形状收益，未稳定超越完整A2；004与005的二维解释没有同步改善。真实Mesh对应改善了相对椭圆中介的HERO留出投影，但H4未全面优于H3，新主体的收益未稳定传导为曲面统一定位收益。真实HERO绝对三维位置仍不可评价。**

## 三个科学问题的回答

1. **显式二维对应相对历史直接轮廓损失的增益：**公平的无深度 A2D→A3 对照中，Chamfer 6/10 组改善，平均变化 -0.001373 mm；条件占据 IoU 8/10 组提高。严格 IoU 共同有效 3 组，其中 3 组提高。A2D 与 A3 唯一区别为轮廓对应损失；保留全部正负结果，不把 A2→A3 的全部变化归功于新增机制。

相对冻结 A2，A3 的 Chamfer 6/10 组改善，平均变化 0.001107 mm；严格 IoU 共同有效 3 组，其中 2 组提高。数值输出 10/11；G08缺004，仍为不可评价。

2. **共享主体对004/005二维观测的解释：**
   - FIT 004：A3−A2 平均 Mask IoU -0.003145，4/10 组提高。
   - FIT 005：A3−A2 平均 Mask IoU +0.001879，5/10 组提高。
   - HOLDOUT 004：A3−A2 平均 Mask IoU -0.004663，3/10 组提高。
   - HOLDOUT 005：A3−A2 平均 Mask IoU +0.001581，4/10 组提高。

3. **真实Mesh轮廓是否更好组织HERO：**
   - H4 对 H1 的跨视频 MAE：2/3 组下降；逐组幅度和 P95 保留在全组表。
   - H4 对 H1 的同视频 MAE：2/4 组下降；逐组幅度和 P95 保留在全组表。
   - H4 对 H2 的跨视频 MAE：2/3 组下降；逐组幅度和 P95 保留在全组表。
   - H4 对 H2 的同视频 MAE：2/4 组下降；逐组幅度和 P95 保留在全组表。
   - H4 对 H3 的跨视频 MAE：1/3 组下降；逐组幅度和 P95 保留在全组表。
   - H4 对 H3 的同视频 MAE：0/4 组下降；逐组幅度和 P95 保留在全组表。

**留出视角同时核验：**
H4 对 H1：HOLDOUT Mask IoU 4/4组提高，组均值变化 +0.032175。
H4 对 H2：HOLDOUT Mask IoU 4/4组提高，组均值变化 +0.043195。
H4 对 H3：HOLDOUT Mask IoU 2/4组提高，组均值变化 +0.008585。
H4 对 M0：HOLDOUT Mask IoU 2/4组提高，组均值变化 -0.007434。
H4 对 ICP：HOLDOUT Mask IoU 3/4组提高，组均值变化 +0.040972。

H4并非全面最优：对H3同视频MAE 0/4组改善，跨视频仅1/3改善；但对同Body的椭圆H2，真实Mesh适配器在G03/G05降低跨视频MAE，并在4/4组改善留出投影。新增Body与新增对应的效果必须分开解释。ICP在G03的跨视频一致性可更低，但其留出投影更差；低曲面间距不等于绝对定位正确。


真实 HERO 有数值的多曲面组 4/11，其余目标保留不可评价状态和原库存；有效跨视频样本量另计。最近表面一致性改善不能证明真实三维位置准确。严格实体IoU与双视频HERO共同可评价样本极少，Figure4不作相关性或因果显著性声明。

## 执行与机制核验

157项回归通过，保留原35项。13阶段门禁完成。独立中央有限差分核验真实已保存显式对应的36个顶点坐标；误差、完整Face/边/插值和每视角梯度证据见evidence与visualization/intermediate。视角贡献用前一梯度与实际共享位移的负内积（descent work）描述，不能将它解读成共享非线性优化中唯一可识别的因果位移分解。

每个E步同时重建全部FIT对应；M步用冻结对应的当前投影更新同一Body，下一步前及最终均重建。原Adam候选、回缩、几何检查、停止预算不变；同attempt权重下接受，ramp随attempt变化，不宣称跨attempt总损失单调。所有早/中/最终完整Mesh及全部拒绝保留。

A3仅使用原2D Polyp/Ring、轮廓项和原形状先验，训练子进程禁止读取HERO深度；没有D2Depth实例。HERO阶段只移动完整局部Mesh，固定相机与Body。H3/H4不读取DXY椭圆参数；H1/H2沿用冻结椭圆适配器。没有新增视角或形态补丁。

GT只用于冻结预测后的尺度固定best_rigid015评价副本；实际对齐矩阵/NPZ/GLB均保存。A2原始世界Mesh与旧结果未修改；本轮所有臂用新的共同占据域重评A2，原数值另存ORIGINAL_A2_EVALUATION.json。Strict IoU不可评价时不升级conditional值。

[全组主体指标](visualization/BODY_SHAPE_METRICS.csv) · [全组HERO指标](visualization/HERO_ALL11_METRICS.csv) · [版本来源](VERSION_SOURCES.csv) · [实际HERO变换](visualization/HERO_TRANSFORMS_AND_MOTION.json) · [失败台账](visualization/FAILURE_LEDGER.json)

## 重复运行的数值稳定性限制

为修复图片导出而以完全相同科学代码/参数/种子重跑Smoke，输出并非逐位一致。已保留两次全部预测，不按GT挑选版本；采用门禁通过的新运行。A3最大顶点坐标分量差：G01约0.0000071mm，G05约0.000000036mm，G11约0.001885mm；G11 A2D约0.024621mm。固定种子不等于历史GPU渲染/线搜索链的逐位可重复性；本轮未定位唯一原因，也未改变冻结计算规则。小于数值波动量级的收益不解释为稳定方法增益，未据此事后筛选病例。完整实测见evidence/SCIENTIFIC_REEXECUTION_IDENTITY.json。

## 可执行方法与固定单位契约

每个真实可见边样本 P=(1−t)V[a]+tV[b]；采用固定原生像素 K 和 OpenCV c2w 相机投影。候选法向残差 r=n·(π(P)−q)/20，使用单位阈值Huber，两个方向各求均值后等权。误差阈值预先固定为40原生像素、切向8像素、互相一致半径4像素、法向绝对余弦≥cos45°。目标Ring边界膨胀3像素视为不确定。继承历史ContourDistance的可见边、Body/CAD射线遮挡与Ring不确定性判定。离散选择全部detach，只有实际3D边点投影携带梯度。

A3与A2D的全视角目标均为原RingAware投影损失 + 原ramp×(0.05 foreground + 0.05 background + 0.01 contour) + 原RelativePrior；A3 contour为显式法向Huber，A2D contour为原ContourDistance。没有HERO深度项，没有新增相机或二维形变变量。视频/方向/视角权重来自原multiview.weights。每候选仍由原train_mesh的全FIT目标和GeometryGuard检查；候选步长/8级回缩/重启/80提案/40接受/30连续拒绝全部不改。

H3/H4把真实Mask轮廓与当前反向变换到原观测坐标中的可见Body边界建立法向候选；以邻近有效边界位移的反距离插值定义像素区域候选，随后射线必须命中实际Body三角面，保存Face和重心。该像素区域转移只提出三维约束，不对训练图像或主体投影做自由变形。没有可用边界、射线失败、Ring接触、低置信或距离越界均保留拒绝/NaN。映射每个外层循环重建；其余共享视频SE3、受限帧残余、重叠项、鲁棒优化和0.5mm Body容差全部复用原registration.optimize代码。

## 原始记录与交付路径

所有科学NPZ与PNG坐标均为毫米。最终GLB按格式惯例导出为米（源顶点乘0.001，仅文件单位换算），物理大小不变，完整命名三角面节点保留；单位记录见visualization/GLB_EXPORT_UNITS.json。
原始Runner尝试、失败索引和训练OPT_START快照保持不可修改。历史训练日志中执行当时的.pending临时绝对路径会随原子提交重命名；它们是原始事件记录，不作为审阅入口。请使用RUN_MANIFEST的相对产物路径与本轮visualization/index.html；交付核验逐一检查这些路径实际存在。实际训练目录的52个015文件及逐臂OPT_START哈希均与905e2a9原提交核验，Objective适配器和执行源码另由本轮冻结身份覆盖。

[HERO因子分解](visualization/HERO_FACTORIAL_DIFFERENCES.csv) · [椭圆与实际Mesh映射诊断](visualization/MAPPING_DIAGNOSTICS.csv) · [几何前后诊断](visualization/GEOMETRY_BEFORE_AFTER.json) · [真实三角面切面身份](visualization/EXACT_MESH_SECTION_AUDIT.json)

H3/H4的有效射线候选置信度为 exp(−接受边界对应的平均像素距离/40) × 平均法向绝对余弦，无有效边界或可见Face则为0；这是一项固定启发式权重，不是概率融合模型。H1/H2保留原椭圆映射置信度及原DXY质量因子。因此H3/H4评价的是完整对应适配器，不能将差异唯一归因于几何映射而排除权重变化；本轮未额外改变优化器或开展DXY研究。
## Frozen aggregate results

```json
{
  "task_id": "TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001",
  "target_groups": 11,
  "A3_numeric": 10,
  "body": {
    "A2": {
      "common_numeric_groups": 10,
      "strict_common_groups": 3,
      "strict_IoU_better": 2,
      "conditional_IoU_better": 7,
      "Chamfer_better": 6,
      "mean_Chamfer_delta_mm": 0.0011073607216873032,
      "mean_conditional_IoU_delta": 0.01463758326951462,
      "strict_reference_mean": 0.7677543371659784,
      "strict_A3_mean": 0.7701861210166432,
      "FIT_004_IoU_delta": {
        "N": 10,
        "mean": -0.003145352659202916,
        "better": 4
      },
      "FIT_005_IoU_delta": {
        "N": 10,
        "mean": 0.0018793401725269332,
        "better": 5
      },
      "HOLDOUT_004_IoU_delta": {
        "N": 10,
        "mean": -0.004663296941942041,
        "better": 3
      },
      "HOLDOUT_005_IoU_delta": {
        "N": 10,
        "mean": 0.0015809421148238634,
        "better": 4
      }
    },
    "A2D": {
      "common_numeric_groups": 10,
      "strict_common_groups": 3,
      "strict_IoU_better": 3,
      "conditional_IoU_better": 8,
      "Chamfer_better": 6,
      "mean_Chamfer_delta_mm": -0.0013731548934840187,
      "mean_conditional_IoU_delta": 0.009634209649359881,
      "strict_reference_mean": 0.7684506948855429,
      "strict_A3_mean": 0.7701861210166432,
      "FIT_004_IoU_delta": {
        "N": 10,
        "mean": -0.002076836558862538,
        "better": 6
      },
      "FIT_005_IoU_delta": {
        "N": 10,
        "mean": 0.0005955960141804828,
        "better": 6
      },
      "HOLDOUT_004_IoU_delta": {
        "N": 10,
        "mean": -0.003584558154002959,
        "better": 5
      },
      "HOLDOUT_005_IoU_delta": {
        "N": 10,
        "mean": -0.0011990687775644492,
        "better": 6
      }
    }
  },
  "HERO_numeric": 4,
  "HERO": {
    "H1": {
      "within_video": {
        "common_groups": 4,
        "H4_better": 2,
        "rows": [
          {
            "case": "G01",
            "reference_MAE_mm": 0.5598268950734121,
            "H4_MAE_mm": 0.5611366560375365,
            "delta_H4_minus_reference_mm": 0.0013097609641243846
          },
          {
            "case": "G03",
            "reference_MAE_mm": 1.6993383316290358,
            "H4_MAE_mm": 1.6872832420617956,
            "delta_H4_minus_reference_mm": -0.012055089567240218
          },
          {
            "case": "G05",
            "reference_MAE_mm": 0.23937737653510802,
            "H4_MAE_mm": 0.23644352798168997,
            "delta_H4_minus_reference_mm": -0.0029338485534180503
          },
          {
            "case": "G06",
            "reference_MAE_mm": 0.15110641957556034,
            "H4_MAE_mm": 0.15144224340853957,
            "delta_H4_minus_reference_mm": 0.00033582383297922624
          }
        ]
      },
      "cross_video": {
        "common_groups": 3,
        "H4_better": 2,
        "rows": [
          {
            "case": "G01",
            "reference_MAE_mm": 0.4801983580363313,
            "H4_MAE_mm": 0.482770194138172,
            "delta_H4_minus_reference_mm": 0.0025718361018406966
          },
          {
            "case": "G03",
            "reference_MAE_mm": 1.9535005091116247,
            "H4_MAE_mm": 1.8923189691261992,
            "delta_H4_minus_reference_mm": -0.061181539985425415
          },
          {
            "case": "G05",
            "reference_MAE_mm": 0.27534388562819556,
            "H4_MAE_mm": 0.27103547090747415,
            "delta_H4_minus_reference_mm": -0.00430841472072141
          }
        ]
      }
    },
    "H2": {
      "within_video": {
        "common_groups": 4,
        "H4_better": 2,
        "rows": [
          {
            "case": "G01",
            "reference_MAE_mm": 0.5606498355917128,
            "H4_MAE_mm": 0.5611366560375365,
            "delta_H4_minus_reference_mm": 0.0004868204458237102
          },
          {
            "case": "G03",
            "reference_MAE_mm": 1.6954426917206744,
            "H4_MAE_mm": 1.6872832420617956,
            "delta_H4_minus_reference_mm": -0.008159449658878826
          },
          {
            "case": "G05",
            "reference_MAE_mm": 0.23975815695629799,
            "H4_MAE_mm": 0.23644352798168997,
            "delta_H4_minus_reference_mm": -0.0033146289746080193
          },
          {
            "case": "G06",
            "reference_MAE_mm": 0.15050337469491284,
            "H4_MAE_mm": 0.15144224340853957,
            "delta_H4_minus_reference_mm": 0.0009388687136267226
          }
        ]
      },
      "cross_video": {
        "common_groups": 3,
        "H4_better": 2,
        "rows": [
          {
            "case": "G01",
            "reference_MAE_mm": 0.48184117421035316,
            "H4_MAE_mm": 0.482770194138172,
            "delta_H4_minus_reference_mm": 0.0009290199278188527
          },
          {
            "case": "G03",
            "reference_MAE_mm": 1.9282559133024406,
            "H4_MAE_mm": 1.8923189691261992,
            "delta_H4_minus_reference_mm": -0.03593694417624138
          },
          {
            "case": "G05",
            "reference_MAE_mm": 0.27526761568204466,
            "H4_MAE_mm": 0.27103547090747415,
            "delta_H4_minus_reference_mm": -0.004232144774570512
          }
        ]
      }
    },
    "H3": {
      "within_video": {
        "common_groups": 4,
        "H4_better": 0,
        "rows": [
          {
            "case": "G01",
            "reference_MAE_mm": 0.5557247868037675,
            "H4_MAE_mm": 0.5611366560375365,
            "delta_H4_minus_reference_mm": 0.005411869233769018
          },
          {
            "case": "G03",
            "reference_MAE_mm": 1.6811672525697134,
            "H4_MAE_mm": 1.6872832420617956,
            "delta_H4_minus_reference_mm": 0.006115989492082141
          },
          {
            "case": "G05",
            "reference_MAE_mm": 0.23635003538892913,
            "H4_MAE_mm": 0.23644352798168997,
            "delta_H4_minus_reference_mm": 9.349259276084099e-05
          },
          {
            "case": "G06",
            "reference_MAE_mm": 0.15065183837476245,
            "H4_MAE_mm": 0.15144224340853957,
            "delta_H4_minus_reference_mm": 0.000790405033777114
          }
        ]
      },
      "cross_video": {
        "common_groups": 3,
        "H4_better": 1,
        "rows": [
          {
            "case": "G01",
            "reference_MAE_mm": 0.48446103594929685,
            "H4_MAE_mm": 0.482770194138172,
            "delta_H4_minus_reference_mm": -0.0016908418111248325
          },
          {
            "case": "G03",
            "reference_MAE_mm": 1.8887024512570434,
            "H4_MAE_mm": 1.8923189691261992,
            "delta_H4_minus_reference_mm": 0.003616517869155844
          },
          {
            "case": "G05",
            "reference_MAE_mm": 0.27036217506318316,
            "H4_MAE_mm": 0.27103547090747415,
            "delta_H4_minus_reference_mm": 0.0006732958442909887
          }
        ]
      }
    }
  },
  "real_absolute_3D_accuracy": "NOT_EVALUABLE",
  "GT_used_for_selection": false,
  "scientific_acceptance": "AWAITING_HUMAN_REVIEW"
}
```

A2 Mesh bytes are unchanged. All arms are re-evaluated in this task using one common Sobol domain per case, so its newly reported occupancy estimate can differ slightly from the prior report; the original report metrics remain in evidence/ORIGINAL_A2_EVALUATION.json. Strict and conditional occupancy are never interchanged. Per-view gradient/actual shared displacement evidence reports descent-work attribution, not a uniquely identifiable causal decomposition of the shared vertex update. No per-view meshes or image transforms are optimized.

## All-case comparisons

[
  {
    "case": "G01",
    "reference": "A2",
    "conditional_IoU_delta": 0.013227135155740699,
    "Chamfer_delta_mm": -0.030824355484823318,
    "strict_IoU_delta": 0.013227135155740699,
    "FIT_004_IoU_delta": -0.01753657504306194,
    "FIT_005_IoU_delta": -0.009218557488806622,
    "HOLDOUT_004_IoU_delta": -0.0205014548273198,
    "HOLDOUT_005_IoU_delta": -0.011274628736527958
  },
  {
    "case": "G01",
    "reference": "A2D",
    "conditional_IoU_delta": 0.0008190464085302551,
    "Chamfer_delta_mm": -0.0038644231184208344,
    "strict_IoU_delta": 0.0008190464085302551,
    "FIT_004_IoU_delta": 0.0010619218963088262,
    "FIT_005_IoU_delta": 0.0009299288986504006,
    "HOLDOUT_004_IoU_delta": 0.00034264038237785677,
    "HOLDOUT_005_IoU_delta": 0.0013639897956974067
  },
  {
    "case": "G02",
    "reference": "A2",
    "conditional_IoU_delta": 0.023578371191223968,
    "Chamfer_delta_mm": -0.012280825944905871,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": -0.0033192563103231487,
    "FIT_005_IoU_delta": -0.0038998065144060234,
    "HOLDOUT_004_IoU_delta": -0.005655898825574157,
    "HOLDOUT_005_IoU_delta": 0.002008396206120533
  },
  {
    "case": "G02",
    "reference": "A2D",
    "conditional_IoU_delta": 0.023472521695083848,
    "Chamfer_delta_mm": -0.010950250797219896,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": -0.00401789199899294,
    "FIT_005_IoU_delta": -0.003762778457682636,
    "HOLDOUT_004_IoU_delta": -0.005467554862972568,
    "HOLDOUT_005_IoU_delta": 0.002423903111509862
  },
  {
    "case": "G03",
    "reference": "A2",
    "conditional_IoU_delta": -0.023908824998387423,
    "Chamfer_delta_mm": 0.029946880938179543,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": -0.0025643403132318277,
    "FIT_005_IoU_delta": 0.021065234860864646,
    "HOLDOUT_004_IoU_delta": -9.71370989861775e-05,
    "HOLDOUT_005_IoU_delta": 0.02085594954884995
  },
  {
    "case": "G03",
    "reference": "A2D",
    "conditional_IoU_delta": -0.0025962869025065727,
    "Chamfer_delta_mm": 0.003466830960547229,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": 0.0030870402105839245,
    "FIT_005_IoU_delta": 0.0006792253137222204,
    "HOLDOUT_004_IoU_delta": 0.0021185852920755366,
    "HOLDOUT_005_IoU_delta": 0.0009040974382855671
  },
  {
    "case": "G07",
    "reference": "A2",
    "conditional_IoU_delta": 0.00012411310841276002,
    "Chamfer_delta_mm": -5.712597839213629e-08,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": -1.8070000591507984e-05,
    "FIT_005_IoU_delta": -1.0125556905715705e-05,
    "HOLDOUT_004_IoU_delta": -2.5728436484850903e-05,
    "HOLDOUT_005_IoU_delta": -2.73283777874056e-05
  },
  {
    "case": "G07",
    "reference": "A2D",
    "conditional_IoU_delta": 0.0,
    "Chamfer_delta_mm": 1.0691302835263983e-06,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": 0.0,
    "FIT_005_IoU_delta": 0.0,
    "HOLDOUT_004_IoU_delta": 2.7450657443139903e-05,
    "HOLDOUT_005_IoU_delta": 0.0
  },
  {
    "case": "G04",
    "reference": "A2",
    "conditional_IoU_delta": -0.034925527038626836,
    "Chamfer_delta_mm": 0.01269464989831856,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": -0.025733144844416245,
    "FIT_005_IoU_delta": -0.001573419132237741,
    "HOLDOUT_004_IoU_delta": -0.029184571059789,
    "HOLDOUT_005_IoU_delta": -0.019968024607130874
  },
  {
    "case": "G04",
    "reference": "A2D",
    "conditional_IoU_delta": 0.056697530301051735,
    "Chamfer_delta_mm": 0.0011843523567695025,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": -0.026041484804601556,
    "FIT_005_IoU_delta": 0.003228484717662572,
    "HOLDOUT_004_IoU_delta": -0.032157187071319426,
    "HOLDOUT_005_IoU_delta": -0.023553844715311523
  },
  {
    "case": "G05",
    "reference": "A2",
    "conditional_IoU_delta": 0.0007851892647813274,
    "Chamfer_delta_mm": -4.178030633217311e-05,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": 3.3712340638203386e-05,
    "FIT_005_IoU_delta": 2.3699545574684677e-05,
    "HOLDOUT_004_IoU_delta": 2.9358605264317994e-05,
    "HOLDOUT_005_IoU_delta": -3.357147017601925e-05
  },
  {
    "case": "G05",
    "reference": "A2D",
    "conditional_IoU_delta": 0.0007023156263190611,
    "Chamfer_delta_mm": -0.00036977002714355667,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": 7.079737683213239e-06,
    "FIT_005_IoU_delta": -4.282184029369418e-06,
    "HOLDOUT_004_IoU_delta": 3.376402472721196e-05,
    "HOLDOUT_005_IoU_delta": 0.0
  },
  {
    "case": "G06",
    "reference": "A2",
    "conditional_IoU_delta": 0.018867822859330086,
    "Chamfer_delta_mm": -0.003533283749387661,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": 0.004300218649157417,
    "FIT_005_IoU_delta": 0.00511782138049699,
    "HOLDOUT_004_IoU_delta": 0.00286445904714272,
    "HOLDOUT_005_IoU_delta": 0.01791775350378677
  },
  {
    "case": "G06",
    "reference": "A2D",
    "conditional_IoU_delta": 0.0005191667565717095,
    "Chamfer_delta_mm": -0.0015733078987262838,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": -0.004286747198584018,
    "FIT_005_IoU_delta": 0.0015968142960272047,
    "HOLDOUT_004_IoU_delta": -0.005920959468736942,
    "HOLDOUT_005_IoU_delta": 0.006547948510868262
  },
  {
    "case": "G09",
    "reference": "A2",
    "conditional_IoU_delta": 0.15455933675641775,
    "Chamfer_delta_mm": 0.004188004801811002,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": 0.012975601768288936,
    "FIT_005_IoU_delta": 0.007215556520892008,
    "HOLDOUT_004_IoU_delta": 0.013878655156174702,
    "HOLDOUT_005_IoU_delta": 0.009035846435462402
  },
  {
    "case": "G09",
    "reference": "A2D",
    "conditional_IoU_delta": 0.012340570623777802,
    "Chamfer_delta_mm": 0.004303677246816157,
    "strict_IoU_delta": null,
    "FIT_004_IoU_delta": 0.009172640275100452,
    "FIT_005_IoU_delta": 0.002236848526049884,
    "HOLDOUT_004_IoU_delta": 0.005463482216839233,
    "HOLDOUT_005_IoU_delta": 0.0016719167463798978
  },
  {
    "case": "G10",
    "reference": "A2",
    "conditional_IoU_delta": -0.028072096316139827,
    "Chamfer_delta_mm": 0.034305184277662354,
    "strict_IoU_delta": -0.028072096316139827,
    "FIT_004_IoU_delta": 0.0012509810897503026,
    "FIT_005_IoU_delta": 0.0015462038451743432,
    "HOLDOUT_004_IoU_delta": -0.00395487161374608,
    "HOLDOUT_005_IoU_delta": -0.0015359351052259829
  },
  {
    "case": "G10",
    "reference": "A2D",
    "conditional_IoU_delta": 0.002156997222913848,
    "Chamfer_delta_mm": -0.0027760638476506394,
    "strict_IoU_delta": 0.002156997222913848,
    "FIT_004_IoU_delta": 4.668528001161576e-05,
    "FIT_005_IoU_delta": -0.00034265602967908926,
    "HOLDOUT_004_IoU_delta": -7.75429490118551e-06,
    "HOLDOUT_005_IoU_delta": 0.0016615238173208757
  },
  {
    "case": "G11",
    "reference": "A2",
    "conditional_IoU_delta": 0.022140312712393695,
    "Chamfer_delta_mm": -0.02338081008767101,
    "strict_IoU_delta": 0.022140312712393695,
    "FIT_004_IoU_delta": -0.0008426539282393453,
    "FIT_005_IoU_delta": -0.0014732057353772365,
    "HOLDOUT_004_IoU_delta": -0.003985780366102087,
    "HOLDOUT_005_IoU_delta": -0.0011690362491327821
  },
  {
    "case": "G11",
    "reference": "A2D",
    "conditional_IoU_delta": 0.0022302347618571305,
    "Chamfer_delta_mm": -0.003153662940095392,
    "strict_IoU_delta": 0.0022302347618571305,
    "FIT_004_IoU_delta": 0.00020239101386509972,
    "FIT_005_IoU_delta": 0.0013943750610836414,
    "HOLDOUT_004_IoU_delta": -0.0002780484155624485,
    "HOLDOUT_005_IoU_delta": -0.003010222480394842
  }
]

## Body/HERO relationship

[
  {
    "case": "G01",
    "family": "cross_video",
    "delta_strict_IoU": 0.013227135155740699,
    "delta_conditional_IoU": 0.013227135155740699,
    "HERO_MAE_reduction_mm": -0.0025718361018406966,
    "strict_missing": false
  },
  {
    "case": "G01",
    "family": "within_video",
    "delta_strict_IoU": 0.013227135155740699,
    "delta_conditional_IoU": 0.013227135155740699,
    "HERO_MAE_reduction_mm": -0.0013097609641243846,
    "strict_missing": false
  },
  {
    "case": "G03",
    "family": "cross_video",
    "delta_strict_IoU": null,
    "delta_conditional_IoU": -0.023908824998387423,
    "HERO_MAE_reduction_mm": 0.061181539985425415,
    "strict_missing": true
  },
  {
    "case": "G03",
    "family": "within_video",
    "delta_strict_IoU": null,
    "delta_conditional_IoU": -0.023908824998387423,
    "HERO_MAE_reduction_mm": 0.012055089567240218,
    "strict_missing": true
  },
  {
    "case": "G05",
    "family": "cross_video",
    "delta_strict_IoU": null,
    "delta_conditional_IoU": 0.0007851892647813274,
    "HERO_MAE_reduction_mm": 0.00430841472072141,
    "strict_missing": true
  },
  {
    "case": "G05",
    "family": "within_video",
    "delta_strict_IoU": null,
    "delta_conditional_IoU": 0.0007851892647813274,
    "HERO_MAE_reduction_mm": 0.0029338485534180503,
    "strict_missing": true
  },
  {
    "case": "G06",
    "family": "within_video",
    "delta_strict_IoU": null,
    "delta_conditional_IoU": 0.018867822859330086,
    "HERO_MAE_reduction_mm": -0.00033582383297922624,
    "strict_missing": true
  }
]

## Audit

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 11 physical groups |
| 本算法独立成功 | A3 numerical 10/11; numeric output is not accuracy |
| 本算法失败 | A3无数值 1/11：G08；HERO接口不可评价 7/11：G02, G07, G04, G08, G09, G10, G11；数值但未收敛和恶化另列台账 |
| 历史测量值回退 | 0; A0/A2 explicit reference arms only |
| 失败组及具体原因 | [ledger](visualization/FAILURE_LEDGER.json); G08 missing004; HERO missing native source binding retained |
| 最终统计样本 | 主体共同数值 10/11，严格IoU共同有效 3/11；真实HERO 4/11，其中双视频 3/11；GT绝对定位不可评价 |
| 是否使用 GT 选择算法 | No; last accepted Mesh and frozen source code; no GT/HOLDOUT tuning |

## Artifacts

[Body metrics](visualization/BODY_SHAPE_METRICS.csv) · [all11 HERO](visualization/HERO_ALL11_METRICS.csv) · [GT SE3](visualization/GT_RIGID_TRANSFORMS.json) · [2D→3D links](visualization/BODY_UPDATE_LINKS.json)

![Fig1_2D_TO_3D](visualization/figures/Fig1_2D_TO_3D.png)

![Fig2_ALL_BODY_GT](visualization/figures/Fig2_ALL_BODY_GT.png)

![Fig4_BODY_HERO_RELATION](visualization/figures/Fig4_BODY_HERO_RELATION.png)

![G01_Fig1_2D_TO_3D](visualization/figures/G01_Fig1_2D_TO_3D.png)

![G01_Fig3_HERO_SECTIONS](visualization/figures/G01_Fig3_HERO_SECTIONS.png)

![G02_Fig1_2D_TO_3D](visualization/figures/G02_Fig1_2D_TO_3D.png)

![G03_Fig1_2D_TO_3D](visualization/figures/G03_Fig1_2D_TO_3D.png)

![G03_Fig3_HERO_SECTIONS](visualization/figures/G03_Fig3_HERO_SECTIONS.png)

![G04_Fig1_2D_TO_3D](visualization/figures/G04_Fig1_2D_TO_3D.png)

![G05_Fig1_2D_TO_3D](visualization/figures/G05_Fig1_2D_TO_3D.png)

![G05_Fig3_HERO_SECTIONS](visualization/figures/G05_Fig3_HERO_SECTIONS.png)

![G06_Fig1_2D_TO_3D](visualization/figures/G06_Fig1_2D_TO_3D.png)

![G06_Fig3_HERO_SECTIONS](visualization/figures/G06_Fig3_HERO_SECTIONS.png)

![G07_Fig1_2D_TO_3D](visualization/figures/G07_Fig1_2D_TO_3D.png)

![G09_Fig1_2D_TO_3D](visualization/figures/G09_Fig1_2D_TO_3D.png)

![G10_Fig1_2D_TO_3D](visualization/figures/G10_Fig1_2D_TO_3D.png)

![G11_Fig1_2D_TO_3D](visualization/figures/G11_Fig1_2D_TO_3D.png)


## G02/G03实际Mesh专项审阅

G02 的 A3 相对 A2 的条件占据 IoU由 0.521792 提高至 0.545370，Chamfer由 0.364178 降至 0.351897 mm，但实际对齐图仍为缺失半体，未恢复完整头部；不能将数值小幅提高认作错误初始化已修复。G02 GT有自交，严格实体IoU仍不可评价。

G03 的预测头部在真正SE(3)评价副本中与GT头部空间重合，长柄仍缺失。A2→A3的Chamfer 1.273195→1.303142 mm 恶化，而P95 9.086725→8.267317 mm下降；不能仅挑一个改善指标宣布恢复。当前固定初值、可见性、基底保护和预算的各自因果贡献未被分离；没有特殊形态补丁或GT选checkpoint。

![Actual aligned Ip failure evidence](visualization/figures/Fig2_G02_G03_IP_DETAIL.png)

## 形状与定位改善不同向的实际案例

| 病例 | A2→A3 GT Chamfer mm | H1→H4 跨视频曲面MAE mm | 解读 |
| --- | --- | --- | --- |
| G01 | 0.379809→0.348984 | 0.480198→0.482770 | 主体形状改善，但曲面一致性恶化 |
| G03 | 1.273195→1.303142 | 1.953501→1.892319 | 主体形状恶化，但曲面更集中；不能推断真实定位更准确 |

H4相对原始M0的HOLDOUT组均IoU下降0.007434，只有2/4组提高；这与H4相对椭圆H1/H2的4/4组留出改善必须同时报告。

GLB中的Body使用正式渲染表面F，全部该表面三角形均保留；NPZ同时保留F_solid及inferred_base_faces用于闭合诊断。推断封底不称为真实观测，也不能使严格IoU自动有效；HERO所有原始三角形始终完整保留。

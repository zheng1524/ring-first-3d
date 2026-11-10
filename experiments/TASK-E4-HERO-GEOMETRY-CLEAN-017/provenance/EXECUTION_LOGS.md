# Actual CPU execution logs

## runtime_ANALYSIS.log

```text
/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/code/analyze017.py:91: RuntimeWarning: invalid value encountered in subtract
  a=cast(old,uv,s['Kn'],s['T'])['t_hit'].numpy();b=cast(new,uv,s['Kn'],s['T'])['t_hit'].numpy()if new else np.full(len(uv),np.inf);cad=cast(ring,uv,s['Kn'],s['T'])['t_hit'].numpy();valid=np.isfinite(a)&(a<cad-.002);ret=valid&np.isfinite(b)&(b<cad-.002);same=ret&(abs(a-b)<.01)
G01_004_ref03 ARCHIVE_RAW faces 46805 reject 0 area 0.0 visible 1.0 sec 5.7
G01_004_ref03 NATIVE_GRID faces 46577 reject 0 area 0.0 visible 1.0 sec 5.4
G01_004_ref08 ARCHIVE_RAW faces 26621 reject 0 area 0.0 visible 1.0 sec 3.2
G01_004_ref08 NATIVE_GRID faces 26642 reject 0 area 0.0 visible 1.0 sec 3.1
G01_004_ref13 ARCHIVE_RAW faces 24453 reject 0 area 0.0 visible 1.0 sec 3.0
G01_004_ref13 NATIVE_GRID faces 24680 reject 0 area 0.0 visible 1.0 sec 2.9
G06_004_ref04 ARCHIVE_RAW faces 17829 reject 0 area 0.0 visible 1.0 sec 2.2
G06_004_ref04 NATIVE_GRID faces 17493 reject 0 area 0.0 visible 1.0 sec 2.1
G01_004_new_r00 ARCHIVE_RAW faces 44465 reject 0 area 0.0 visible 1.0 sec 5.3
G01_004_new_r00 NATIVE_GRID faces 44787 reject 0 area 0.0 visible 1.0 sec 5.1
G06_004_new_r00 ARCHIVE_RAW faces 15851 reject 0 area 0.0 visible 1.0 sec 1.9
G06_004_new_r00 NATIVE_GRID faces 15484 reject 0 area 0.0 visible 1.0 sec 1.8
G06_004_growth_r06 ARCHIVE_RAW faces 25240 reject 0 area 0.0 visible 1.0 sec 3.1
G06_004_growth_r06 NATIVE_GRID faces 24522 reject 0 area 0.0 visible 1.0 sec 2.9
G06_004_growth_r01 ARCHIVE_RAW faces 16408 reject 0 area 0.0 visible 1.0 sec 2.0
G06_004_growth_r01 NATIVE_GRID faces 16024 reject 0 area 0.0 visible 1.0 sec 1.9
G06_004_growth_r03 ARCHIVE_RAW faces 16550 reject 0 area 0.0 visible 1.0 sec 2.0
G06_004_growth_r03 NATIVE_GRID faces 16154 reject 0 area 0.0 visible 1.0 sec 1.9
G01_004_growth_r04 ARCHIVE_RAW faces 40950 reject 0 area 0.0 visible 1.0 sec 4.9
G01_004_growth_r04 NATIVE_GRID faces 40761 reject 0 area 0.0 visible 1.0 sec 4.7
G01_004_growth_r10 ARCHIVE_RAW faces 27723 reject 0 area 0.0 visible 1.0 sec 3.3
G01_004_growth_r10 NATIVE_GRID faces 27618 reject 0 area 0.0 visible 1.0 sec 3.2
G01_004_growth_r07 ARCHIVE_RAW faces 25876 reject 0 area 0.0 visible 1.0 sec 3.1
G01_004_growth_r07 NATIVE_GRID faces 26284 reject 0 area 0.0 visible 1.0 sec 3.0
G01_004_growth_r14 ARCHIVE_RAW faces 23283 reject 0 area 0.0 visible 1.0 sec 2.8
G01_004_growth_r14 NATIVE_GRID faces 23551 reject 0 area 0.0 visible 1.0 sec 2.8
G01_004_growth_r12 ARCHIVE_RAW faces 26183 reject 0 area 0.0 visible 1.0 sec 3.1
G01_004_growth_r12 NATIVE_GRID faces 26544 reject 0 area 0.0 visible 1.0 sec 3.1
G01_004_growth_r06 ARCHIVE_RAW faces 30756 reject 0 area 0.0 visible 1.0 sec 3.6
G01_004_growth_r06 NATIVE_GRID faces 30833 reject 0 area 0.0 visible 1.0 sec 3.6
G01_004_growth_r01 ARCHIVE_RAW faces 47862 reject 0 area 0.0 visible 1.0 sec 5.8
G01_004_growth_r01 NATIVE_GRID faces 48166 reject 0 area 0.0 visible 1.0 sec 5.7
G03_key04_raw00554 ARCHIVE_RAW faces 51525 reject 0 area 0.0 visible 1.0 sec 6.1
G03_key04_raw00554 NATIVE_GRID faces 51657 reject 0 area 0.0 visible 1.0 sec 5.9
G05_key04_raw00542 ARCHIVE_RAW faces 61796 reject 0 area 0.0 visible 1.0 sec 7.3
G05_key04_raw00542 NATIVE_GRID faces 60758 reject 0 area 0.0 visible 1.0 sec 7.0
```

## runtime_FINAL.log

```text
/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/code/analyze017.py:91: RuntimeWarning: invalid value encountered in subtract
  a=cast(old,uv,s['Kn'],s['T'])['t_hit'].numpy();b=cast(new,uv,s['Kn'],s['T'])['t_hit'].numpy()if new else np.full(len(uv),np.inf);cad=cast(ring,uv,s['Kn'],s['T'])['t_hit'].numpy();valid=np.isfinite(a)&(a<cad-.002);ret=valid&np.isfinite(b)&(b<cad-.002);same=ret&(abs(a-b)<.01)
FINAL G01_004_ref03 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_ref03 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_ref08 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_ref08 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_ref13 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_ref13 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G06_004_ref04 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G06_004_ref04 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_new_r00 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_new_r00 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G06_004_new_r00 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G06_004_new_r00 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G06_004_growth_r06 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G06_004_growth_r06 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G06_004_growth_r01 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G06_004_growth_r01 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G06_004_growth_r03 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G06_004_growth_r03 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r04 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r04 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r10 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r10 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r07 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r07 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r14 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r14 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r12 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r12 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r06 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r06 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r01 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G01_004_growth_r01 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G03_key04_raw00554 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G03_key04_raw00554 NATIVE_GRID removed 0 area 0.0 visible 1.0
FINAL G05_key04_raw00542 ARCHIVE_RAW removed 0 area 0.0 visible 1.0
FINAL G05_key04_raw00542 NATIVE_GRID removed 0 area 0.0 visible 1.0
```

## runtime_DIAGNOSTICS.log

```text
READ_ONLY_ATTRIBUTION_COMPLETE 24522 patches 8 group/representation rows
```

## runtime_VALIDATION_FINAL.log

```text
DELIVERY_VALIDATION_COMPLETE_NO_CLEANING_PASS
```

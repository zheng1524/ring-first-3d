# 原始SIFT退化失败日志（逐字保留）

```text
Traceback (most recent call last):
  File "/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-POLYP-REGISTRATION-019/code/features019.py", line 77, in <module>
    if __name__=='__main__':main()
                            ^^^^^^
  File "/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-POLYP-REGISTRATION-019/code/features019.py", line 76, in main
    lm=landmarks(refs,'CROSS_004');cross(refs,targets,lm,'CROSS');neg=load(R/'config/NEGATIVE_SPLIT.json');lm=landmarks(neg['reference_fit'],'NEGATIVE_004');cross(neg['reference_fit'],neg['target_fit'],lm,'NEGATIVE');save('provenance/FEATURE_FIT_FREEZE.json',dict(epoch=time.time(),all_image_ids=allids,HOLDOUT_images_used=False,GT=False,source=asset(Path(__file__)),landmarks=[asset(p)for p in(R/'landmarks').glob('*')]))
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-POLYP-REGISTRATION-019/code/features019.py", line 61, in cross
    a=VIEWS[aid];m=matches(a,b);ii=np.flatnonzero(m['RGB_RANSAC']);ii=ii[np.linspace(0,len(ii)-1,min(128,len(ii))).astype(int)]if len(ii)else ii
                   ^^^^^^^^^^^^
  File "/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-POLYP-REGISTRATION-019/code/features019.py", line 22, in matches
    F,flag=cv2.findFundamentalMat(u,w,cv2.USAC_MAGSAC,1.5,.999,10000)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
cv2.error: OpenCV(4.11.0) /io/opencv/modules/calib3d/src/usac/estimator.cpp:353: error: (-215:Assertion failed) !model.empty() in function 'setModelParameters'

```

原features.log仍保留本地，不覆盖。

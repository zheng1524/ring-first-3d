# 系统结构

统一代码包src/ring_first_3d继续承载契约、视角、初始化、Renderer、对应、配准和评价。mainline/lineage是版本隔离的既有算法源码闭包；native是经来源核验的Ring-First/HERO适配器；frozen_registry供原AST API读取原SHA定义。

mainline提供运行入口、配置、来源/依赖锁、精选结果和离线可视化。外部原始数据、官方代码、checkpoint与既有venv不混入算法包。.runtime是复制且核验过的本机编译库，LOCAL_ONLY。

工程状态PASS；科学状态ACTIVE_RESEARCH_MAINLINE。Graph节点及样条状态是历史checkpoint重放，不是新的训练结果。

# 可选默认档案：JEOL CRYO ARM 300 与铜网

档案版本：2026-10-20。设备与采集来源为此前维护者核实的实验记录；本版本根据维护者当日明确要求，将这些非身份参数作为可提示的默认选项收录。它不是官方设备校准证书，也不是新批次采集证明。

适用范围：用户明确选择沿用本档案的常规 TEM 冷冻电镜采集及结构存档准备。它整理了维护者已使用的设备、载网和历史采集设置，**不代表所有同型号设备、本次采集观测或通用 OneDep 默认值**。当前日志、设备/网格变更和用户更正优先；真实样品、作业、会话与私人资料不在本文件中。

## 启动时先收集，再提供默认选项

先查当前任务已提供的资料；没有才用一次简短提示收集：

> 请提供本批实际采集的 log、shottest、SerialEM `.mdoc` 或 Record 设置，并说明显微镜/探测器及铜网/支持膜参数。已有资料我会直接读取。暂时没有时，可选择本档案的 JEOL CRYO ARM 300 + K3、Quantifoil 铜网配置；也可明确采用下面列出的历史采集候选，我会标为“用户采用的默认值，本批尚未验证”。

- 已给出本批资料或明确设备/网格信息，不重复索取；先解析文件，只补问缺失项。
- 用户明确本次采用本档案后，在其授权范围内复用所选项目，不逐字段重复确认。记录采用日期、范围和 `user-adopted default; not batch-verified`，不能改写成 log 观测或实测值。
- 将“设备/载网配置”与“历史采集候选”分开呈现。仅确认同一设备不自动证明本批放大、剂量、帧数、采样或离焦相同。
- 缺 log 不阻塞已有证据支持的其他准备、文件检查和可独立填写项。未知可选项保留为空；必填缺项再集中补问，不编造参数。
- 测试记录可形成候选；提交前优先核对实际采集记录、数据匹配和覆盖。shottest 格式先读实际内容，不预设标准结构。

## 1. 可选设备与载网配置

用户采用后可作为本次候选预填；菜单名称仍与当前页面核对。

| 项目 | 可选值 | 说明 |
|---|---|---|
| 显微镜 | `JEOL CRYO ARM 300` | 原版型号，不自动改称后续型号 |
| 加速电压 | `300 kV` | 配置基准；遇本批矛盾以实际记录更新 |
| 球差系数 Cs | `2.7 mm` | 不是 nm，也不证明装有球差校正器 |
| 电子枪 | cold field emission gun；表单 `FIELD EMISSION GUN` | 物理配置与上位词表分开 |
| 能量过滤器 | `In-column Omega Filter` | 硬件名称；本次 slit 状态及宽度仍需证据 |
| 探测器 | `GATAN K3 (6k x 4k)` | 不因 Omega 滤镜改选其他相机组合型号 |
| 样品台 / 冷却剂 | `JEOL` / `NITROGEN` | holder 冷却；不等同制样快速冷冻剂 |
| 采集软件 | `SerialEM` | 版本未知，不能填当前安装版本代替当时运行版本 |
| 常规 TEM 照明 / 成像 | `FLOOD BEAM` / `BRIGHT FIELD` | 仅用于常规 TEM 全场明场；STEM/衍射等另核对 |
| Grid company/model | `Quantifoil R1.2/1.3` | 品牌与孔型 |
| Grid metal / mesh | `COPPER` / `200` | 铜网、200 mesh；不据孔型推断其他材质 |
| Support film / topology | `CARBON` / `HOLEY ARRAY` | 多孔碳支持膜 |
| Grid pretreatment | `GLOW DISCHARGE` | 辉光放电；时间、气氛、压力未知 |

设备型号、相机或模式改变时停止套用相关配置。膜厚、辉光时间/气氛/压力、能量狭缝、aperture、实际温度、对中方式、校准放大/离焦等不由本档案提供默认。

## 2. 可选择采用的历史采集候选

下列为维护者历史设置，不是当前批次的测量结果。用户选择采用时可预填并保持默认状态标记；有本批日志或实际文件后再核实。

| 项目 | 历史候选 | 证据边界 / 使用要求 |
|---|---|---|
| Nominal magnification | `50000` | 名义放大，不是 calibrated magnification |
| Total dose per movie | 约 `35 e-/A^2` | 每部完整电影累计剂量，不是 dose rate，不除以帧数 |
| Frames per movie | `57` | 不能由此推算曝光秒数或帧周期 |
| K3 mode | electron-counting super-resolution | 仅适用于采用此采集模式的数据 |
| Raw movie dimensions | `11520 x 8184` | width x height；stack 形状需检查轴序 |
| Raw sampling | `0.466 A/pixel` | 原始超分辨电影采样，不是最终地图值 |
| Motion-correction Fourier crop | `0.5` | 使用线性尺寸因子 0.5 的软件语义时才沿用 |
| Processed micrograph dimensions | `5760 x 4092` | 上述原始尺寸及裁切条件对应的输出 |
| Processed micrograph sampling | `0.932 A/pixel` | 与原始采样和 crop 的关系核算；最终地图仍独立查头 |
| Nominal defocus candidate | 欠焦幅度 `400–2600 nm` | 历史仅部分实际保存电影记录覆盖，不证明新批次或历史全批范围 |

离焦历史说明：记录软件的目标为 `-0.4` 至 `-2.6 um`，其中脚本声明至 `-2.5 um`，部分实际保存电影使用 `-2.6 um`。原符号、脚本声明、实际范围和覆盖分别保留。只有确认当前 OneDep 符号定义后，才把欠焦目标映射到其 nm 字段；这不是 CTF 搜索范围，也不是 calibrated defocus。

## 3. 始终按本批取证，不提供默认的项目

- **曝光时间和帧周期未知**：不能由 57 帧、文件时间差、采集耗时或历史经验推算。
- Movie/image 数、grid 实际采集数量、采集/处理软件运行版本不得继承；载网规格相同不证明 grid 数量相同。
- 最终主图选择、地图/half/mask 的网格与像素、origin、Contour level、展示图关联逐文件核对，不把 `0.932` 微图采样自动写入所有地图。
- 起始/筛选/最终片段数、分类数、分辨率/FSC、独立分半证据、点群、twist、rise、模型版本和地图-模型对应均取当前支路。
- 序列、D/L、端基、修饰、浓度、pH、组装/退火、blot、制样温湿度和冷冻剂不因采用本档案而继承。
- 作者、来源字段、公开安排和正式提交授权不属于设备 profile。默认仍为 no_submit，不自动登录、上传、接受报告/条款或正式提交。

## 4. 审核表中的状态写法

| 字段 | 值 | 状态 | 来源 |
|---|---|---|---|
| 用户选择的设备/载网项 | 本档案相应值 | 用户采用的默认值；本批未验证 | 本档案版本 + 本次采用记录 |
| 用户选择的历史采集候选 | 本档案相应值 | 历史候选预填；本批未验证 | 本档案 + 本次选择范围 |
| 本批实际记录 | 实际观测值 | 本批观测；注明完整/部分覆盖 | 文件/字段/位置与数据匹配 |
| 无明确证据项目 | 空 | unknown | 缺项原因 |

出现默认与实际记录冲突时并列说明并更新受影响字段，不能悄悄覆盖历史事实。若默认值已输入网页，保存后仍需重新载入核对，并在报告中保留其“默认、未验证”状态。

## 参考

本档案从已有工作记录提炼，不复制未公开 Methods 或真实提交材料；以下链接保留作必要时复核的来源入口，本轮未重新核实网页政策。

- [JEOL 原版 CRYO ARM 产品资料](https://www.jeol.com/products/scientific/tem/JEM-Z300FSC.php)
- [Quantifoil circular holes](https://www.quantifoil.com/products/quantifoil/quantifoil-circular-holes)
- [SerialEM metadata 格式](https://bio3d.colorado.edu/SerialEM/stableHlp/html/about_formats.htm)
- [OneDep detector 词表](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_image_recording.film_or_detector_model.html)
- [Nominal defocus min](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_imaging.nominal_defocus_min.html)、[Nominal defocus max](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_imaging.nominal_defocus_max.html)
- 通用核对：[采集参数指南](acquisition-metadata.md)、[OneDep 字段指南](onedep-field-guide.md)

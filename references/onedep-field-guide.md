# OneDep 多肽地图与模型逐页指南

本公开指南描述通用填写与核对方法，不含真实提交记录或作者资料。菜单名称来自既有字段核对资料；本轮整理没有重新核实网站政策，当前页面词表、帮助与官方要求优先。采集证据见 [采集参数指南](acquisition-metadata.md)，缺资料时可提示用户采用 [JEOL 与铜网默认选项](jeol-cryoarm300-default-profile.md)，审核输出见 [新条目模板](../assets/new-deposition-template.md)。

## 1. 身份、范围与操作终点

- 先区分样品、采集批次、重构 class/最终作业/迭代、模型版本。共享原始数据不代表不同 class 可以共用最终半图、FSC、分辨率或模型。
- 只有地图可准备 EMDB；有对应的最终原子模型可准备联合提交，或在实际 EMDB 编号取得后再交 PDB 并关联。`D_...` 是会话号，不是 `EMD-...` 存档编号。
- 默认模式为 **no_submit**：仅在本次用户已授权填写时，核对并保存表单、生成审核表。不得自动登录、接受报告或条款、正式 Submit/Deposit/Finish/Release、发送 Communication。上传具体文件及坐标转换另需属于当前授权范围。
- CryoSPARC 核对保持只读，不修改、克隆、启动或删除作业。没有浏览器工具时输出待粘贴内容，不能声称已填写或保存。
- 任务开始先使用本批已有资料，缺少时索取 log/mdoc/shottest、显微镜和载网/支持膜参数，并提示内置默认选项供用户采用。测试记录和默认值用于有状态的候选预填；正式采集记录与重构数据的匹配、覆盖范围及冲突必须记录。

## 2. File upload

以下类型名称用于识别用途；以当前菜单实际选项为准。

| 文件 | 常见类型 | 核对点 |
|---|---|---|
| 采用的最终三维密度 | `EM map (MRC/CCP4 format)` | 一条目选定主图；依据最终分析、展示或模型拟合使用的地图和处理记录，不凭 `_sharp`/`_sym` 后缀确定 |
| 独立 half A/B | `EM half map (MRC/CCP4 format)` | 同一最终重构的两个 half；核对网格、轴序、采样、origin、坐标框架和实际分组/独立精修证据 |
| 展示图片 | `Entry image for public display` | 应对应主图及推荐阈值，显示完整结构；尺寸、背景要求按当前页面，不固定旧案例像素数 |
| FSC XML | `FSC file (XML format)` | 确定 unmasked/masked/corrected 类型、对应 mask 和迭代；频率单位为逆埃时分辨率是 `1/frequency` |
| 相关后处理版本 | `Additional EM map (MRC/CCP4 format)` | 描述 sharpened/unsharpened、额外对称化等真实处理；无须上传软件生成的所有中间文件 |
| FSC/后处理 mask | `EM mask (MRC/CCP4 format)` | 与实际曲线匹配；自动收紧后 mask 与旧静态 mask 不可仅凭同目录互换 |
| 最终原子坐标 | 当前 PDBx/mmCIF 坐标类别 | 仅用于合适的坐标提交路线；EMDB-only 页面不混入未准备的模型 |

`Pixel spacing` 优先取当前 MRC header，与实际 crop/resampling 记录核对。保存三轴观测；非各向同性时核实页面输入方式。原始电影采样、运动校正后采样和地图采样分别记录。MRC 头检查只能证明头部观测，不能证明完整密度数组无损或半图独立。

`Contour level` 是密度数值尺度上的推荐显示阈值，不是分辨率、FSC 或默认 sigma。ChimeraX 的 Level、step、颜色和视角变化通常只改显示；没有改变数组、采样、坐标框架或文件时，不必因此重传 MRC。显示 `step` 不是物理采样倍数。每张图按其数值尺度选择阈值，不把主图阈值复制给半图。未滤波半图噪声较大，不能仅凭外观判定损坏；结合低通显示、两半一致性、FSC 和来源检查，不为美化而改写提交半图。

Short description 使用简短 ASCII 英文，写实际对象、class、处理状态、软件/作业/迭代。以下占位符须替换：

```text
Primary map of <sample>, <class>: <final processing state>. <software/job/iteration>.
Unsharpened reconstruction of <sample>, <class>. <software/job/iteration>.
Half map A from independently refined half-set A for <sample>, <class>; paired with half map B from the same reconstruction.
Mask used for <exact FSC curve type> from <job/iteration>.
```

网页重命名后缀本身不能证明内容改变或上传失败；记录完整网页文件名与本地对应关系，不靠后缀删除、重传或认定主图。出现读取错误时记录实际信息，先检查具体文件及允许的恢复方法，不自动重新上传全部数据。

传输或服务器处理尚在进行时不刷新、离开上传页、取消、删除或重复上传。区分网络传输与服务器处理；不从文件大小、勾选状态或等待时长推断完成。只有配套文件成功、类型和唯一主图明确、必填像素与阈值齐全、可见错误解决后，才执行已授权的普通保存/Continue。

## 3. Admin：标题、作者、引用和公开安排

| 字段 | 填写原则 |
|---|---|
| Obsoleting released entries | 不替换已有公开条目时选 `No`；给已有地图关联模型不等于废弃旧条目。替换未公开会话按当前官方流程处理 |
| Entry title | 简述结构、样品和区分类别的特征；不是仅贴序列，也不必须等于论文标题 |
| Classification | 按实际结构/功能及当前词表选择；线性序列不自动代表 fibril 或 helical reconstruction |
| Keywords | 按页面限制填写；既有页面为不超过四个、逗号分隔。只写有证据的结构/功能术语 |
| Authors | 分别确认提交作者、论文作者、顺序、PI、通讯作者。姓与名缩写按本人确认，不从中文名机械拆分 |
| Primary citation | 未发表仍可能要求预期论文标题与作者；未分配 DOI/PMID 时留空。复制上一页后仍需核对 |
| Release status | 每条目由用户确认；关联地图/模型需协调公开安排，不从旧项目继承 |

受 ASCII 限制的字段用 `alpha-sheet`、普通连字符和 `A`/`Angstrom`；只有研究确实支持该结构时才填相应关键词。私人联系方式不放入公开 skill 或便携包；仅在当前授权与名单确认后使用本地私有记录。

## 4. Macromolecules：实体、手性、端基与来源

- 这里登记单个化学实体；同序列的多个装配拷贝不逐一新建不同序列。不同序列、共价修饰或化学实体应分别描述。
- 真实逐位 D/L 构型、N/C 端基和修饰须由样品证据确认。单独一字母序列不能表达 D/L 或封端；非标准残基用当前接受的编码，并附明文手性说明。端基不是额外氨基酸。
- 不因出现 D 残基就猜页面不存在的分子类别，也不因 L 残基占多数就忽略 D 位点。分类存在歧义时查当前帮助。
- 实际化学合成的肽在 molecule obtained 字段选择与 `Chemically synthesized` 对应的当前选项；不虚构表达宿主或天然组织。
- 无天然物种的人工设计实体，如分类服务允许使用 `synthetic construct`/taxonomy `32630`，应核对其解析结果与字段语义。该 taxonomy 不是某条肽的序列 accession，也不代表来源为天然提取。
- EC、mutation、strain 等没有事实时留空。GenBank/UniProt 仅填真实对应 accession 和区间；不为短肽偶然 BLAST 匹配制造天然序列关系。
- 用户确认模型来自真实样品后，仍需验证模型化学命名、连接、手性与端基；从旧坐标读出的序列不自动成为实验样品事实。

## 5. Overall sample description：整体装配体与 Source

Name/Details 描述实际成像对象，例如多拷贝自组装的管段，而不是只重复单肽名称。Type 与 chimeric polymer 按实际组成和当前词表选择；混合 D/L 不自动等于嵌合聚合物。未知聚集数的 assembly 总质量允许时留空；单肽 MW 不能冒充整个装配体 MW，也不能未测量却标记 experimentally measured。

**Source 没有面向所有提交者的固定默认。**分别核对 molecule obtained 和整体 sample obtained 的字段语义、实际来源及当前页面。不要把分子页选择机械复制到整体样品页。

用户可以在私有 local profile 中明确授权某组页面填写约定，包括适用样品范围、来源、日期和字段对应；只有本次符合该范围且无冲突时才复用。个人约定不能升级为通用政策，不能把化学合成样品描述为天然提取物。控件禁用或语义不明时保留实际观测并查帮助，不绕过正常控件修改后台字段。Strain、organ、tissue、organelle 等无事实的项目保持空白。

## 6. Specimen preparation

逐批确认合成来源/纯度、母液与上网浓度、组装/退火时间与温度、pH/缓冲成分、grid、支持膜、辉光放电、blot 和冷冻条件。

| 字段 | 单位与边界 |
|---|---|
| Concentration | `mg/mL = mM * MW(g/mol) / 1000`；新序列、端基或质量口径改变须重算；母液不同于上网液 |
| Buffer/pH | 无已知缓冲盐或调 pH 试剂时不补配方；明确哪些成分未知 |
| Chamber temperature | 按字段单位，摄氏转 K 加 273.15；换算小数位不代表测量精度 |
| Blot time/force | 秒及仪器设置值；未知实际力时不把 blot force 设置赋 N 单位 |
| Grid/film | 品牌、孔型、mesh、金属、支持膜材料/厚度分别核实，孔型不能推出金属 |
| Glow discharge | 时间、气氛、压力按实际记录；仅有“glow discharged”不补常用数值 |
| Cryogen | 制样快速冷冻剂与显微镜 holder 冷却剂属于不同阶段 |
| Stained/embedded/shadowed | 仅按实际工艺填，无相关处理证据时不随意勾选 |

载网等可按用户采纳的内置 profile 预填并记录“采纳默认，未本批核实”。profile 未提供的未知可选项留空并解释；必填缺项需证据或补问，不能靠经验填数。

## 7. Microscopy 与 Image recording

设备档案仅在同一设备/模式且无矛盾时复用；批次值来自实际采集。详见 [采集参数指南](acquisition-metadata.md)。

- 模型、gun、filter、holder、冷却剂与照明/成像模式分别记录；配有某硬件不证明本次使用。TEM 明场与 STEM/衍射须按实际区分。
- 电压 `kV`、Cs `mm`；Cs 数值不证明使用球差校正器。放大为 nominal 还是 calibrated 要区分，无校准来源不编值。
- Defocus 保留原符号、单位和定义，检查当前字段正负约定后转换；目标离焦、实测离焦、CTF 搜索范围互不替代。
- Image recording 关联当前显微镜记录；探测器名按实际硬件/词表，不能因为有滤镜就换成另一探测器组合型号。
- Width/Height 是原始保存电影尺寸，不填运动校正裁切后的尺寸；计数/超分辨模式应说明。`Sampling interval (um)` 若帮助定义为扫描仪步长，不填样品平面 `A/pixel`。
- Dose 是完整电影累计 `e-/A^2`，不是 dose rate，也不除以帧数；Exposure time 由明确秒数字段取得，不能由帧数或文件时间差反推。
- Image 数是实际电影/微图数，不乘帧数；grid 数是实际采集载网数。部分日志去重计数不能冒充完整数据集。

## 8. Reconstruction：追溯最终支路

| 字段 | 依据 |
|---|---|
| Detector association | 本条重构实际使用的 recording，不固定数字 ID |
| Initial selected/extracted/final segments | 各阶段独立记录；最终数不能冒充起始数，多个 class 不混加 |
| Selection/software | 实际追踪、提取、分类步骤与当时运行版本；当前服务器版本不代表历史版本 |
| CTF correction | 按实际重构算法和当前词表；CTF estimation 不是 standalone corrected-image 处理 |
| Startup model | 最终 job 的直接参考及来源；自有实验图、计算模型、既有存档图/坐标分别说明，不因最后有模型就选 PDB ENTRY |
| Angles/algorithm | 角度分配与密度重构类别分开；最大似然 alignment 和 Fourier-space reconstruction 可同时成立 |
| Classification | 输入数、2D/3D、输出类数和实际选中类数分开；页面整数限制不支持时不任意取整 |
| Resolution/FSC | 与最终图、曲线类型及 mask 对应；保留软件 reported 值与独立核算值。常用 FSC 0.143 首次下降穿越按实际准则，不挑后续交叉点报更佳值 |
| Half-map generation | 文件成对不证明 gold-standard 独立；核对实际分组/精修。丝状重叠片段应检查是否按 parent filament 分半及交叉相关 |
| Helical parameters | 最终点群、带符号 twist、rise(A) 分别记录；C1 可同时施加螺旋对称。初始/最终参数与额外实空间处理分开 |

Mask、auto-tightening、FSC 和上传版本须一致。日志里的内部 symmetry order 不自动等于 Cn 或 protofilament 数。线性序列也不自动授权选择 HELICAL；依据实际形态及作业路线。

## 9. 保存、报告与正式提交边界

1. 用页内会话号、Requested ID(s)、样品/class 和关联记录确认目标，不靠旧标签标题。一次处理一个 deposition；发现目标变化立即停止写入，记录可能受影响字段。
2. 按当前工具文档使用可见表单和受控词表；不调用猜测的后台接口。填写后触发正常 input/change/blur 并等待保存完成。工具返回成功不等于服务器已持久保存。
3. 传输/处理结束且普通保存完成后，重新载入并完整读回字段、textarea、关联与错误。不能只读可见前几行、导航勾或旧 DOM。适配失败时按工具文档修复事件触发，不把历史 locator 或脚本当永久 API。
4. 输出实际保存值、完整英文文本、中文解释、单位/换算、来源/覆盖、留空原因和截图。区分建议值、已填写未确认保存、已保存、待用户处理。浏览器不可用时明确未验证。
5. 验证报告先核对生成时间、版本、目标会话、主图和警告。`Not provided` 可能是旧快照或真缺项，需读回当前表单再判断。初步报告、绿色勾和上传完成都不等于正式提交或科学验证通过。
6. 默认交用户审核，保持 **no_submit**。接受报告、条款、正式提交、公开、联系第三方须分别有当前授权，不由 skill 安装授予。实际完成以确认页、存档编号和状态为证。

## 10. PDBx/mmCIF 与地图关联

- 同一个化学实体的多个链实例应可唯一寻址；不为每个相同拷贝创建不同序列。检查 auth/label 身份、残基/原子身份、连接、装配与坐标框架。
- 传统 PDB 字段容量有限，大型多链结构宜准备 PDBx/mmCIF。hybrid-36 编号须正确解析，不能仅凭非十进制 serial 判坏。
- 仅修改扩展名或格式不代表化学与身份问题修复。只有用户授权转换时才在副本操作，保持坐标、手性、端基、原子身份与连接，重新读回并验证计数和差异。
- B 因子全零、含氢或 metadata 缺失是待核实特征，不单独证明无精修；不擅自改 B、删氢、最小化或重建。
- 核对模型确实对应所关联最终主图；不同 class 不能共用同一最终模型身份。保存真实精修软件/版本/参数、几何与模型-地图验证，再按实际 EMD 编号关联并协调公开。

## 官方参考与维护

链接从私有工作版的既有参考清单保留，供溯源与必要时复核；本轮没有重新核实网页政策。语义变化或关键未知时查当前官方资料。

- [wwPDB deposition FAQ](https://www.wwpdb.org/deposition/faq)、[PDBx/mmCIF 准备](https://www.wwpdb.org/deposition/preparing-pdbx-mmcif-files)
- [Detector 词表](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_image_recording.film_or_detector_model.html)、[Image 数定义](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_image_recording.num_real_images.html)、[Scanner sampling interval](https://pdbml.wwpdb.org/dictionaries/mmcif_pdbx_v5_next.dic/Items/_emd_image_digitization.sampling_interval.html)
- [Minimum nominal defocus](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_imaging.nominal_defocus_min.html)、[Maximum nominal defocus](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_imaging.nominal_defocus_max.html)
- [Final particle 数](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_3d_reconstruction.num_particles.html)、[Initial selection 数](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_particle_selection.num_particles_selected.html)、[Class 平均数](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_final_classification.avg_num_images_per_class.html)
- [Startup model type](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_start_model.type.html)、[Angular rotation](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_helical_entity.angular_rotation_per_subunit.html)、[Axial symmetry](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_helical_entity.axial_symmetry.html)
- [Overall assembly source 词表](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_em_entity_assembly.source.html)
- [CryoSPARC Helical Refinement](https://guide.cryosparc.com/processing-data/all-job-types-in-cryosparc/helical-reconstruction-beta/job-helical-refinement-beta)、[Helical symmetry](https://guide.cryosparc.com/processing-data/all-job-types-in-cryosparc/helical-reconstruction-beta/helical-symmetry-in-cryosparc)
- [CryoSPARC reconstruction algorithm 说明](https://discuss.cryosparc.com/t/reconstruction-algorithm-parameter-type-during-deposition/11086/2)、[CTF correction 解释](https://discuss.cryosparc.com/t/phase-flipping-or-flipping-amplitude-correction/9340)、[Auto mask tightening](https://discuss.cryosparc.com/t/fsc-mask-auto-tightening/1350)
- [SerialEM metadata 格式](https://bio3d.colorado.edu/SerialEM/stableHlp/html/about_formats.htm)、[SerialEM script commands](https://bio3d.colorado.edu/SerialEM/stableHlp/html/script_commands.htm)

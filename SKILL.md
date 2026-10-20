---
name: cryoem-peptide-deposition
description: Prepare and review EMDB/PDB OneDep depositions for chemically synthesized linear peptides and peptide assemblies from single-particle or helical cryo-EM. Extract acquisition metadata, inspect CryoSPARC read-only, fill and save authorized OneDep forms, and produce a review table without formally submitting by default.
---

# 短肽 cryo-EM 结构存档

把本批实验、处理记录和文件检查结果转换为 OneDep 可填写内容，并交付实际保存值的审核表。适用于 EMDB 地图、PDB 坐标联合提交，或先地图、后模型的关联提交。

本公开候选版不带真实实验文件或个人身份记录，另附维护者授权公开的 JEOL CRYO ARM 300 与铜网参考 profile。它可在资料缺少时作为默认选项提示用户；采用的默认值与当批实测值分别标记。旧 class 和旧软件版本不足以作为新条目的参数证据。

## 按当前任务读文件

- 提取采集参数、核对单位或建立设备档案：读 [采集元数据](references/acquisition-metadata.md)，按需运行只读检查脚本。
- 未提供设备/载网参数，或用户要求同机默认预填：读 [JEOL CRYO ARM 300 默认选项](references/jeol-cryoarm300-default-profile.md)，提示用户采用范围，不重复查已经收录的硬件信息。
- 文件类型、各页字段、模型准备、报告问题：读 [OneDep 逐页指南](references/onedep-field-guide.md) 的相关模块。
- 开始新条目或交付审核表：复制 [输入与审核模板](assets/new-deposition-template.md) 到用户指定的记录位置。
- 演练证据选择和未知项处理：读 [合成示例](examples/synthetic-deposition.md)。示例不是实验结果或成功提交记录。
- 用户明确提供本地配置时：参考 [配置示例](config.example.json) 的结构，人工核对该配置适用于当前样品与批次。脚本不会自动加载这个配置。

完整单文件移交可使用生成的 `deposition-handbook.md`；已读模块时不再重复加载整本手册。

## 从证据到保存

**任务开始先收集资料。**先读已有附件与本次记录；尚未提供时，请用户提供实际采集 log/`.mdoc`/shottest 或 Record 设置，并说明显微镜/探测器/模式和载网品牌孔型、金属、mesh、支持膜。不要重复索取已给信息。缺少资料时直接列出内置 JEOL CRYO ARM 300 与 Quantifoil 铜网配置，提示可选用默认预填；已明确采用该 profile 时不再逐字段重复确认，继续整理其余资料，不因没有日志而停住整个任务。

默认候选、用户采纳的默认（尚未经本批核实）、本批观测三者分开。可采用范围见 profile；曝光时间、整批电影数、实际软件版本及最终重构结果没有默认值。后续本批证据冲突时列出差异并更新拟填值，不能把默认写成“日志实测”。

1. **锁定对象。**记录当前样品、批次、class、CryoSPARC 项目/作业、页面内 deposition session 和 requested archive。会话编号与正式 EMD/PDB 编号分别保存；旧标签标题不能证明当前页面身份。
2. **日志优先，补问缺项。**先检查用户已提供的实际采集 log、`.mdoc`、shottest、Record 设置及处理日志。没有时索取对应批次文件。测试脚本、设计目标和历史方法只能预填，不能覆盖实际采集记录。一次只补问当前仍缺少且需要填写的信息。
3. **建立参数表。**每项记录值、单位、来源位置、覆盖范围和证据状态：设备配置、本批观测、用户确认、计算值、未知或冲突。逐位 D/L、端基、修饰、作者和公开安排都按当前条目确认。
4. **只读核对处理。**根据本批地图输出追溯最终 CryoSPARC 作业和版本，区分起始/筛选/最终片段数、输入/最终螺旋参数、原始/校正后/地图采样。读取作业不授权修改参数、选择类、接受结果或运行作业。
5. **填写并读回。**用户授权填写时，调用当前环境实际可用的浏览器工具；先读工具文档，复用用户指定页面，一次处理一个 session。保存或普通 Continue 后重新读取完整字段与错误状态；需要刷新验证时先确认传输和服务器处理已经结束。
6. **生成审核材料。**列出实际输入值和读回值、英文 Details、中文解释、证据、空项原因、冲突及保存状态。有截图能力时按用户要求留存截图；截图属于用户的私人记录，不放入公开源码。

## 浏览器执行边界

- CryoSPARC 默认只读；OneDep 按当次授权填写和普通保存，默认停在用户审核处。**不勾选报告接受项或 Terms，不执行正式 Submit/Deposit/Release，不发送 Communication 消息。**技能调用本身不扩大授权。
- 上传或服务器处理进行时，观察文件行、进度和错误；不刷新、不离开，不删除、取消或重复上传。会话不符、登录失效或验证码出现时停止写入，报告一次具体问题。
- 选择主图、显示阈值和文件用途要有当前证据；不能只依赖文件名。保留用户已明确指定的值，矛盾时解释并补问，不静默覆盖。
- 无浏览器工具时，输出逐字段可粘贴内容和未完成项目；不要声称已填入、保存或提交。定时跟进需要用户要求及环境的调度能力，不由本技能自动开启。

## 只读检查

在包根目录运行，Python 3.10+，仅使用标准库：

```bash
python scripts/inspect_inputs.py --help
python scripts/inspect_inputs.py --log actual.log --mdoc movie.mdoc --map primary.mrc --fsc curve.xml --pdb model.pdb
```

结果写到标准输出 JSON；路径和引文可能含私人信息。由用户选择保存位置，原文件保持原样。MRC 默认只检查头部，不代表整张地图、科学质量或服务器端上传副本已验证；格式检查也不等于模型可以提交。转换坐标应另建副本，保持坐标、手性与连接关系并重新核对。

## 复用与报告判断

设备档案可减少重复检索。资料缺少时，剂量、离焦、采样等仅可按 profile 提示历史采集候选；用户采纳后可预填并标明尚未经本批核实。曝光、运行版本和最终重构结果仍需本批证据。区分 TargetDefocus、测得离焦与 CTF 搜索范围；帧数或文件时间差不能替代曝光。

先检查验证报告的条目、生成时间和版本，再与已保存字段核对。只有网站正式分配的 EMD/PDB 编号才能用于关联；不要把 session 编号写成存档号。class 的模型与地图必须一一对应，地图已上传或表单已保存不等于正式提交完成。

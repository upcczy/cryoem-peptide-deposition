# cryoem-peptide-deposition

用于化学合成线性短肽及其装配体的 cryo-EM 结构存档助手：从采集与处理证据获取参数，准备 EMDB/PDB OneDep 表单，保存后生成审核表。支持单颗粒与螺旋重构，以及先 EMDB、后关联 PDB 的路线。

**状态：0.1.0 公开审核候选；仓库已公开，尚未发布正式 Release；许可证待维护者确认。** [MIT 文本草案](assets/mit-text-proposal.txt) 仅供审核，尚未授予开源许可，见 [许可待审核说明](references/licensing-review.md)。

An evidence-led AI workflow for peptide cryo-EM depositions. Read-only metadata tools, browser-assisted form preparation, and saved-value review; no formal submission by default. The repository is public as a review candidate. No formal release or open-source license has been issued.

## 能做什么

- 读取 log、shottest、SerialEM `.mdoc`、MRC 头、FSC XML 和旧 PDB，输出带来源、覆盖范围及冲突的 JSON。
- 将设备档案与每批实测值分开；区分目标离焦、实测离焦与 CTF 搜索范围，原始电影、处理微图与地图采样。
- 开始任务时收集 log/mdoc/shottest、显微镜与载网信息；资料不足时提示可选的 JEOL CRYO ARM 300 和 Quantifoil 铜网默认 profile，避免重复寻找已收录参数。
- 指导选择主图/半图/mask/FSC 等上传类型，填写序列、D/L、端基、制样、采集、重构和引用字段。
- 有可用浏览器工具并获用户授权时，只读核对 CryoSPARC，填写、普通保存 OneDep，再读回完整值并输出审核表。
- 无浏览器时，交付逐字段可粘贴内容，明确哪些步骤尚未在网站执行。

它不会操作显微镜或替代科学判断。检查器不登录、不上传、不联网、不修改实验数据；MRC 只读头部，不能证明完整数组无损。默认不运行 CryoSPARC 作业、不接受报告或条款、不正式提交，不自动创建定时任务。

## 文件入口

| 文件 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | AI 任务入口、证据流程和操作终点 |
| [AGENTS.md](AGENTS.md) | 本目录的简短查找与维护规则 |
| [OneDep 逐页指南](references/onedep-field-guide.md) | 文件类型、字段、报告与模型准备 |
| [采集参数指南](references/acquisition-metadata.md) | 设备 profile、批次取证、单位和未知项 |
| [JEOL CRYO ARM 300 默认选项](references/jeol-cryoarm300-default-profile.md) | 维护者已授权的设备/铜网配置与历史采集候选，缺资料时供用户选用 |
| [输入与审核模板](assets/new-deposition-template.md) | 新条目资料与实际保存值审核表 |
| [合成演练](examples/synthetic-deposition.md) | 用虚构输入演练新样品、证据冲突与留空 |
| [配置示例](config.example.json) | 可选本地配置的结构；脚本不会自动加载 |
| [inspect_inputs.py](scripts/inspect_inputs.py) | 标准库只读参数检查器 |
| [build_package.py](scripts/build_package.py) | 允许清单打包、手册和 SHA-256 manifest |

构建后还会得到 `deposition-handbook.md` 和 `dist/` 下的 ZIP。手册用于集中阅读和移交；需要运行脚本时使用完整包。手册、manifest 和 ZIP 都从源文件生成，不手改，也不作为新的实验案例。

## 快速开始

纯文档阅读不需要 Python。运行本包脚本需要 **Python 3.10+**，仅标准库，无额外运行依赖。在本包根目录执行：

```bash
python scripts/inspect_inputs.py --help
python scripts/inspect_inputs.py --log actual.log --mdoc movie.mdoc --map primary.mrc --fsc curve.xml --pdb model.pdb
```

按实际资料只传存在的选项，不必凑齐。测试日志用 `--test-log shottest.log`（也可用 `--shottest`），与 `--log` 的实际采集证据分开。仅当整批电影数已有可靠证据时使用 `--expected-movies N`。CLI 参数和实际支持字段以 `--help` 为准，不假定所有软件的日志格式相同。

JSON 写到标准输出，可能含真实路径与证据片段。需要保存时先在包外或 `records/` 建立私人目录，例如：

```bash
python scripts/inspect_inputs.py --log actual.log > records/inspection.json
```

先复制模板、填写当前样品和已有证据，再要求 AI 处理。未提供采集记录、显微镜或载网参数时，AI 会先收集缺项，并提示内置默认 profile 供用户选用；用户已明确采用时不再逐字段重复询问。示例请求：

```text
使用 $cryoem-peptide-deposition，先读取本批实际采集日志、mdoc 和最终地图；
我的样品序列、端基和目标 class 见我提供的条目记录。
只读核对我已打开的 CryoSPARC 最终作业，核对 OneDep 页面内会话身份后，
填写并普通保存已授权页面，不正式提交，最后给我实际保存值、来源和空项的审核表。
```

调用 skill 可以串起这套流程，但不能自动获得未提供的证据、浏览器权限或网站登录。下一批先检查本次已有记录，只有未知、冲突、未保存或已变更的字段才重新查证。

## 在 AI 环境中使用

**Codex：**将整个包安装到当前环境的 skills 目录后，以 `$cryoem-peptide-deposition` 调用；支持按描述自动识别。安装前确认没有同名私人 skill，避免覆盖。此公开候选保留相同技能名，不能与同名私人版本混装后期望二者各自独立。

**其他 AI：**直接提供 `SKILL.md`，由它按需读取参考文件；只能提供单文件时使用构建的手册。脚本使用常规 Python，浏览器调用遵循各环境实际提供的工具文档，不依赖硬编码的 Codex 工具名。

可选本地档案：复制 `config.example.json` 为 `config.local.json`，由用户填入已核实设备、适用范围和日期，交给 AI 明确读取。它是人工/AI 的输入资料，**不是**检查器自动生效的配置。内置 JEOL profile 也需按范围采用：设备/铜网可按用户选择预填；历史剂量、离焦和采样候选标明“用户采纳默认，未经本批核实”，不能伪称实测。曝光、整批电影数、运行版本、作者、公开安排及最终重构结果不从旧批次默认继承。个人 Source 习惯只能在用户明确授权且适用于当前字段时复用，不能成为所有用户的统一答案。

## 本地检查、构建与安装

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/build_package.py
python scripts/build_package.py --verify-only
```

构建会重建手册、相对路径 SHA-256 manifest 和 `dist/cryoem-peptide-deposition-0.1.0.zip`（版本取自 `VERSION`），再读回 ZIP，核对文件成员、CRC 和每项内容哈希。`--verify-only` 只核验已有产物。manifest 不含自身哈希，不是签名，也不证明来源可信。

ZIP 仅收录脚本中逐文件列出的允许清单，不递归打包整个目录。新增公开文件需同步清单。未列出的配置、记录、实验数据、截图、`.git`、缓存和 `dist/` 不会因为存在于目录而自动进入包。

如需安装，先查看 `python scripts/build_package.py --help`，再显式传 `--install-dir`，目标必须是另外一个名为 `cryoem-peptide-deposition` 的目录。目标里出现清单外文件时，脚本在复制前拒绝，保留额外文件；不要为通过检查而删除私人资料。目标中同名文件会被更新，因此已有同名安装应先由用户决定备份与替换。

提供了 GitHub Actions 的检查配置；它运行离线测试与构建，不发布 Release、不部署，也不接收网站凭据。仅有配置不表示已经在 GitHub 跑过。

## 隐私与 Git

此候选包使用合成 fixture 和演练示例，另含维护者已授权公开的设备/载网参数及注明范围的历史采集参考；未带实际作者、存档会话、实验日志、模型或真实截图。运行产生的数据应放在包外或 `records/`，私人档案用 `config.local.json`。`.gitignore` 能减少误加入的机会，但不会删除已跟踪内容或历史提交里的资料。

准备提交代码时，先检查 `git status --short` 和暂存差异，明确确认文件再提交，不将真实实验目录整体加入 Git。构建允许清单只约束 ZIP，不能代替 Git 暂存区的内容审查。检查器和构建器均不调用 `git push` 或创建远程仓库。

## 正式发行前由维护者审核

1. 确认第三方来源、版权主体和许可证，按 [许可待审核说明](references/licensing-review.md) 定稿。
2. 每次同步前确认公开树与历史提交没有私人资料，核对目标仓库。
3. 运行上面的检查，审核 ZIP 与手册；正式 Release 或后续外部变更按当次任务授权处理。

公开仓库：[upcczy/cryoem-peptide-deposition](https://github.com/upcczy/cryoem-peptide-deposition)。公开可见不等于已经选定开源许可证。

本项目不保证任何数据库接受提交。实际表单、词表和帮助优先；参考资料中的既有链接不等于本版本逐页重新核实了网站要求。

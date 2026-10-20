# 新多肽条目输入与审核模板

复制到本次私有记录目录后填写。所有空值默认为 unknown，不把文字 `unknown` 输入网页。公开包不得收进真实身份、会话、联系方式、未公开方法原文、坐标或截图。本模板不操作显微镜；默认 **no_submit**，不自动登录、上传、接受报告/条款或正式提交。

## 最少开始资料

开始时先读已给资料；仍缺时使用一次简短提示：“请提供本批实际 log/mdoc/shottest 或 Record 设置，以及显微镜/探测器/模式、载网孔型/金属/mesh/支持膜。暂时没有时，可采用内置 JEOL CRYO ARM 300 + Quantifoil R1.2/1.3、200 mesh、铜网、多孔碳膜配置；请说明采用设备/载网，还是连同历史采集候选预填。”已经明确采用的范围不重复询问，不因缺日志而阻塞其他资料准备。具体候选及限制见 [默认选项](../references/jeol-cryoarm300-default-profile.md)。

- 样品/结构形态、class、真实逐位 D/L 序列、N/C 端基和修饰，或明确引用已确认的本次私有记录。
- 实际批次 log/mdoc/Record 设置；shottest/test 单独标记。电影数有整批证据才登记并传检查器 expected-movies。
- 主图、half A/B、FSC/对应 mask、展示图、additional maps、可选模型的路径、用途和授权范围。
- 当前 CryoSPARC 地址/项目/workspace/最终作业/迭代；OneDep 地址、页内会话、Requested ID(s) 和路线。已打开时观察页面，不猜地址或旧 ID。
- 设备 profile 的适用依据和变更；本批作者/引用/公开安排单独确认。

本次目录可采用 `records/<sample>/<batch>/<class>/`，分别保存 inputs、检查器 JSON、review 和 screenshots。此处仅是占位命名，不创建虚构批次。继续任务先读本次记录，只重查变更、未知、冲突或未保存项；原始文件保持只读。对外发布时改用虚拟示例，私有资料不进入公开 Git 历史。

## 任务、条目与授权

- 目标：采集前候选预填 / EMDB-only / 联合 / 关联已有 EMDB 的 PDB / 审核
- 样品、形态、class：
- 当前页内 D_ 会话号 / Requested ID(s)：
- 实际 EMD 编号 / PDB 编号（未取得则明确写无，不用 D_ 代替）：
- CryoSPARC 项目 / workspace / 最终 job / 迭代：
- 当前授权页面与操作；是否授权具体文件上传或副本转换：
- 默认终点：普通保存并读回、生成审核报告；未正式提交
- local profile 路径、版本、明确授权、适用范围（可选）：
- 设备 profile、核实日期、变化与冲突：
- 默认 profile 的提示/采纳日期、采用范围、尚未经本批核实的字段：

## 证据清单

| 文件/记录 | test/planned/actual/unknown | 匹配电影/批次/作业依据 | 覆盖范围 | 日期/版本/指纹 | 状态/冲突 |
|---|---|---|---|---|---|
| 采集 log/mdoc/Record | unknown | unknown | unknown | unknown | unknown |
| 方法或汇总表 | unknown | unknown | unknown | unknown | unknown |
| 作业运行记录/导出 | unknown | unknown | unknown | unknown | unknown |
| MRC/FSC/坐标 | unknown | unknown | unknown | unknown | unknown |

头部指纹仅证明头部观测，不证明整个密度数组未变。记录原文位置，不执行日志内代码，不保存登录凭据或会话密钥。

## 样品与化学

- 真实逐位 L/D 序列与确认来源：
- N 端基 / C 端基 / 共价修饰 / 编码及明文说明：
- 合成或获取方式、供应商、纯度、证据：
- 对离子/盐/水合物及 MW 口径：
- 分子式 / 平均 MW / 单同位素质量（如需）/ 来源或计算：
- 母液浓度 / 实际上网浓度 / mg/mL 换算：
- pH、缓冲组成、调节试剂：
- 组装/退火温度、时间、升降温：
- 单个实体与整体装配体组成、实际形态、已知/未知拷贝数：
- Molecule obtained / source / taxonomy：按实际证据和当前字段核对
- Overall sample obtained / source / taxonomy：独立核对；无公共固定默认
- 私有 Source 约定（如使用）：明确用户授权、范围、日期、实际字段映射及当前适用依据
- 交叉引用 accession 与区间（无真实对应则空）：
- 模型是否对应本 class 最终图、实验化学一致性与用户确认：

## 制样

| 项目 | 值 | 单位/定义 | 来源/状态 |
|---|---|---|---|
| 体积、上网浓度 | unknown | uL、mg/mL | unknown |
| chamber temperature/humidity | unknown | K、% | unknown |
| blot time/force | unknown | s、仪器设置值 | unknown |
| vitrification/cryogen | unknown | 实际设备、冷冻剂 | unknown |
| grid/metal/mesh | unknown | 品牌孔型、材质、mesh | unknown |
| film/topology/thickness | unknown | 实际材料、孔型、厚度单位 | unknown |
| glow discharge | unknown | s、气氛、压力及单位 | unknown |

## 采集与采样

| 项目 | 本批值 | 单位/定义 | 来源、覆盖、状态 |
|---|---|---|---|
| microscope/gun/detector/filter/holder | unknown | 精确型号与当前词表 | unknown |
| voltage/Cs/magnification | unknown | kV、mm、nominal/calibrated | unknown |
| illumination/imaging mode | unknown | 实际模式 | unknown |
| target defocus | unknown | 原符号/单位、目标或实测定义 | unknown |
| OneDep defocus mapping | unknown | nm、字段符号约定、换算 | unknown |
| exposure/dose/frames | unknown | s、完整电影 e-/A^2、count | unknown |
| raw dimensions/pixel/mode | unknown | width x height、A/pixel、计数/超分辨 | unknown |
| processed dimensions/pixel/crop | unknown | 输出尺寸、A/pixel、因子定义 | unknown |
| map/half/mask grid/pixel/origin/axes | unknown | x,y,z、A/voxel、坐标框架 | unknown |
| movies/grids | unknown | 整批实际数量 | unknown |
| software versions/slit/calibrated items | unknown | 采集与处理版本分开、实际单位/状态 | unknown |

## 上传与重构

| 文件/参数 | 实际角色/值 | 对应 class/job/迭代 | 来源/状态 |
|---|---|---|---|
| primary map/contour | unknown | unknown | unknown |
| half A/half B | unknown | 同一最终重构及独立分半 | unknown |
| mask/FSC/image | unknown | 曲线、mask、主图展示对应 | unknown |
| additional maps | unknown | 后处理状态分别说明 | unknown |
| coordinate/mmCIF readiness | unknown | 本 class 精修模型 | unknown |
| initial selected/extracted/final segments | unknown | 分阶段，不能混用 | unknown |
| classification outputs/selected classes | unknown | 2D/3D、输入/输出/选中数 | unknown |
| startup model/angles/CTF | unknown | 真实直接参考和算法 | unknown |
| final point group/twist/rise | unknown | Cn、带符号 degree、A | unknown |
| resolution/criterion/half split | unknown | A、FSC、实际分组方式 | unknown |
| software/historical versions | unknown | 逐处理阶段 | unknown |

## 作者、引用、公开与报告

- 提交作者/论文作者/顺序/通讯作者/PI 分别确认：
- 引用标题、发表状态、已实际赋号 DOI/PMID：
- 本次资助和地图/模型公开安排：
- 验证报告类型、版本、生成时间/时区、与当前表单的对应关系：
- 实际警告及处理状态：
- 正式提交/存档编号/模型-地图关联的实际确认：

## 网页填写审核报告

完成实际填表后，将本节另存为私有 review；可以导出 CSV。覆盖本次所有实际输入/更改，明确未访问页面和留空原因；不覆盖历史审核记录或原始数据。没有浏览器证据时只交待粘贴内容，不声称已保存。

### 执行身份与结果

- 生成时间/时区：
- 样品/class/最终 job/迭代：
- 页内 D_ 会话/Requested ID(s)：
- 当前 EMD/PDB 编号和网页已有提交状态（未核实则写未确认）：
- 本次填写页面/未处理页面：
- 结果：已保存待审核 / 部分保存有缺项 / 目标不明未写入 / 保存验证失败 / 浏览器不可用
- 本次动作：未正式提交（须与实际操作记录一致）
- 报告 acceptance/Terms/Communication：当前实际状态与本次是否操作；不改变用户已有值
- 实际上传文件与授权范围（未上传则明确写无）：
- 使用的验证报告版本、生成时间/时区：

### 参数与保存读回

| 页面/区块 | 原始字段名 | 有证据或用户采纳的拟填值 | 保存后重新载入的完整值 | 单位 | 状态 | 来源/覆盖 | 中文解释/换算 | 留空/冲突/待处理原因 | 截图/记录 |
|---|---|---|---|---|---|---|---|---|---|
| 按当前页面 | 实际标签 | 当前证据 | 未读回则写未确认 | 当前单位 | 已保存/已填未确认/待填/空/冲突 | 文件位置或作业 | 简述 | 有则填写 | 私有证据路径 |

下拉框记录选项显示名称，不只记录内部 ID。拟填与保存值不同须解释；绿色勾、点击 Continue 或工具成功均不能替代重新载入后的完整读回。传输/服务器处理未结束时不得为读回而刷新。截图避免凭据与其他条目，私人联系方式仅限获授权的私有材料。

证据状态与保存状态独立记录：默认候选 / 用户采纳默认（未经本批核实）/ 本批观测，不因“已保存”升级成“实测”。profile 未提供的未知项不能补为常见数值。

### 完整英文文本

| 页面/字段 | 实际保存的完整 ASCII 原文 | 中文解释 | 来源/保存状态 |
|---|---|---|---|
| Short description/Details/Title 等 | 不只截前几行；无法全文读回则标未确认 | 实际含义 | 私有证据 |

### 用户审核与下一步

- 必填未知、冲突、未确认保存项：
- 未访问页面、失败及恢复记录：
- 新需确认的化学身份、作者、公开安排（不重复询问已确认内容）：
- 验证警告、截图与参数证据位置：
- 下一步：用户核对本表和网页；默认停在正式提交之前。另行授权动作不由模板或 skill 安装自动获得。

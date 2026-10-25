# 此包的维护与任务入口

- 存档准备、填写或审核先读 [SKILL.md](SKILL.md)，按其路由只加载所需模块。没有浏览器时输出可粘贴表单；不得声称已保存。
- 开始时先读已有采集证据，缺少 log/显微镜/载网信息则索取；同时提示 [JEOL 与铜网默认选项](references/jeol-cryoarm300-default-profile.md)。用户已明确采用的范围不重复询问；默认候选、采纳默认、本批观测分别记录。
- 真实样品文件、用户配置和运行报告放在包外或未跟踪的 `records/`、`config.local.json`。公开包含通用指南、明确标记的合成示例，以及维护者授权公开的 JEOL/载网参考。个人约定不能升级为通用数据库规则。
- 默认只读核对 CryoSPARC；OneDep 按当次授权填写、保存并留供审核。维护包时不访问或操作真实提交会话，不改原始数据或模型。
- 编辑模块后运行测试，再运行 `python scripts/build_package.py` 重建手册、manifest 和 ZIP。打包使用允许清单；新增公开文件需同步允许清单，不能改成递归收录整个目录。
- `deposition-handbook.md`、`manifest.json` 和 `dist/` 是构建产物。只编辑源模块。安装是显式操作；不要用公开候选覆盖用户正在使用的私人同名 skill。
- 本项目按 MIT 发布，署名 2026 fduczy，见 [LICENSE](LICENSE) 与 [许可说明](references/licensing.md)。安装与调用见 [INSTALL.md](INSTALL.md)。构建成功不能单独证明 GitHub Release 已发布或存档网站已接受提交，外部结果需另外核验。

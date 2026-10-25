# 下载、安装与调用

版本：0.1.0。许可证：MIT，Copyright (c) 2026 fduczy。

## 方式一：下载 Release ZIP

1. 在 [v0.1.0 Release](https://github.com/upcczy/cryoem-peptide-deposition/releases/tag/v0.1.0) 下载 `cryoem-peptide-deposition-0.1.0.zip`。它是完整技能包；单独的手册主要用于阅读和移交。
2. 解压到希望保存代码的位置，例如 Windows 的 `F:\AI-skills\`。完整技能根目录应直接包含 `SKILL.md`、`INSTALL.md`、`LICENSE`、`scripts/`、`references/`、`assets/` 和 `agents/`。
3. 在新电脑的 Codex 中提供解压目录，复制下面的请求。已有同名私人版本时，先决定备份和替换，不把两个同名技能混作同一版本。

```text
请读取我提供目录中的 INSTALL.md 和 SKILL.md，安装 cryoem-peptide-deposition。
源码保留在我指定的非系统盘位置。先检查同名 skill，不覆盖已有私人版本。
按当前 Codex 支持的技能发现目录复制或建立入口，安装后验证相对路径、
LICENSE、参考文件和脚本完整，并确认可以调用。
```

Codex 的当前官方本地发现位置包括项目内 `.agents/skills/` 和用户目录下 `.agents/skills/`，并支持链接到另一位置的 skill 文件夹。也可让环境自带的 skill-installer 按实际支持的目录安装，不照搬别人的用户名、盘符或安装路径。仅把文件解压在任意目录，不保证它会自动出现在技能列表中。

## 方式二：从固定 GitHub 标签安装

在 Codex 中请求：

```text
请使用 $skill-installer 安装 upcczy/cryoem-peptide-deposition 的 v0.1.0 标签。
skill 位于仓库根目录，安装名为 cryoem-peptide-deposition。
先检查同名技能，不覆盖已有私人版本。
```

如果 AI 使用系统安装脚本，对应参数为：

```text
--repo upcczy/cryoem-peptide-deposition --path . --name cryoem-peptide-deposition --ref v0.1.0
```

`--path .` 指仓库根目录，必须显式给出 `--name`。这条路线安装标签中的源码；生成手册和 manifest 以 Release 完整 ZIP 中的版本为准。

## 调用与本机条件

安装完成后，在下一条消息中使用：

```text
$cryoem-peptide-deposition
请读取本批实际采集日志、样品信息和最终地图，核对参数。
在我授权后填写并普通保存 OneDep 页面，最后生成实际保存值审核表。
```

若技能尚未出现，重新启动 Codex 后再检查。纯文档阅读无需 Python；运行包内脚本需要 Python 3.10+，仅用标准库。网页操作使用新电脑实际提供的浏览器工具与登录会话。技能包不包含 Codex 程序、浏览器连接、网站账户、真实实验资料或私人配置。

## 校验与更新

Release 的 `SHA256SUMS.txt` 用于比较下载附件的 SHA-256。完整 ZIP 内另有 `manifest.json`，逐项记录包内文件的大小与哈希；它们是完整性校验，不是数字签名。

源码用户可运行 `python scripts/build_package.py --verify-only` 核对本机已构建的 ZIP。若只有解压后的完整包，可先重建，或让 AI 逐项校验 manifest。需要显式复制安装时，现有构建器支持 `--install-dir`；目标必须是另一个名为 `cryoem-peptide-deposition` 的目录，使用前确认没有应保留的同名文件。

更新到新版本需要再次下载或安装，GitHub 上的修改不会自动替换已安装的副本。保留自己的样品记录在包外，记录使用的版本标签，便于回溯。

官方参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)。

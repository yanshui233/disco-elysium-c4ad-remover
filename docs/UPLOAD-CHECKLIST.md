# 双平台上传 + 交付流程（v1.2.0）

> 照顺序做即可。所有要填的文字都在 `docs/NEXUS-UPLOAD.md` 和
> `docs/NEXUS-DESCRIPTION-BBCode.txt` 里，直接复制。

---

## 0. 上传前的一次性准备（约 3 分钟）

### 0.1 LICENSE 署名 —— 已完成 ✅

`LICENSE` 第 3 行已填：

```
Copyright (c) 2026 盐水 <1248102646@qq.com>
```

### 0.2 git 提交作者 —— 已完成 ✅

本仓库已设为本项目的提交身份：

```bash
git config user.name  "盐水"
git config user.email "1248102646@qq.com"
```

（以上是**仓库级**配置，只影响 `disco-elysium-c4ad-remover`。若想让本机所有仓库
都用这个身份：把上面的 `git config` 换成 `git config --global`。）

### 0.3 确认待上传文件

| 文件 | 用途 |
|---|---|
| `dist/DiscoElysium_ZeroParades_AdRemover_Windows_v1.2.0.zip` | N 网主文件 + 发朋友 |
| `dist/DiscoElysium_ZeroParades_C4Ad_BepInEx_src_v1.2.0.zip` | N 网可选文件 |
| `disco-elysium-c4ad-remover/`（整个目录） | GitHub 仓库 |

---

## 1. 上传到 Nexus Mods

### 1.1 创建 mod 页面

1. 登录 [nexusmods.com](https://www.nexusmods.com)。
2. 进入游戏页：[nexusmods.com/discoelysium](https://www.nexusmods.com/discoelysium)。
3. 点 **Add mod**（或右上角头像菜单 → **Upload a mod**）。
4. 填基本信息：

   | 字段 | 填什么 |
   |---|---|
   | Mod name | `Zero Parades Banner Remover (C4Ad)` |
   | Category | `Miscellaneous` |
   | Version | `1.2.0` |
   | Short description / Summary | `docs/NEXUS-UPLOAD.md` 里 "Short description" 那段 |

5. **Description 页面**：N 网描述编辑器**只支持 BBCode，不解析 Markdown**。
   切到 **BBCode** 标签页，把 `docs/NEXUS-DESCRIPTION-BBCode.txt` 里
   虚线以下的内容整段贴进去（不要用 Markdown 版，会显示成一堆 `##` 和反引号）。

### 1.2 上传文件

1. 进入 **Manage files**（文件管理）标签页 → **Upload file**。
2. 选 `DiscoElysium_ZeroParades_AdRemover_Windows_v1.2.0.zip`。
3. 文件分类选 **Main files**，版本号 `1.2.0`，描述可写
   `Windows installer (no Python). Includes uninstall.`
4. 再 **Upload file** 一次，选 `..._C4Ad_BepInEx_src_v1.2.0.zip`。
5. 文件分类选 **Optional files**，描述必须注明：
   `Source only -- requires BepInEx 6, you compile it yourself. Not prebuilt.`

### 1.3 权限（Permissions & rights）

建议全部选**允许**，理由是可以让更新失效后被别人接手移植：

- Modification — allow
- Conversion / re-upload — allow with credit
- Assets — 本 mod 不含第三方素材

### 1.4 发布

1. 回到 mod 页顶部，点 **Publish**（或把状态设为 Published）。
2. **首次上传会进人工审核**，通常几小时到 24 小时。审核看的主要就是：
   能装、**能卸**、不含游戏原素材 —— 这三点我们都已经满足。
3. 通过后 mod 页才对外可见。

---

## 2. 上传到 GitHub

### 2.1 建远端仓库

在 GitHub 网页点 **New repository**：

- Repository name：`disco-elysium-c4ad-remover`
- 可见性：**Public**
- **不要**勾 "Add a README" / ".gitignore" / "license"（本地已经有了，勾了会冲突）

### 2.2 push 本地仓库（本地已 init、已提交、tag 已打）

```bash
cd disco-elysium-c4ad-remover
git remote add origin https://github.com/<你的用户名>/disco-elysium-c4ad-remover.git
git push -u origin main
git push origin v1.2.0
```

> 不想用命令行：把 `dist/DiscoElysium_ZeroParades_AdRemover_GitHub_Repo_v1.2.0.zip`
> 解压，在仓库页点 **uploading an existing file**，把文件拖进去提交。缺点是
> 一次拖那么多文件容易漏，也不带 git 历史，**推荐还是 push**。

### 2.3 建 Release 并挂附件

1. 仓库页右侧 **Releases** → **Create a new release**。
2. Choose a tag：`v1.2.0`（本地已有这个 tag，push 后会出现在列表里）。
3. Release title：`v1.2.0`
4. 说明直接贴 `CHANGELOG.md` 里 1.2.0 段。
5. 把**两个 N 网包**作为附件拖进 "Attach binaries"：
   - `DiscoElysium_ZeroParades_AdRemover_Windows_v1.2.0.zip`
   - `DiscoElysium_ZeroParades_C4Ad_BepInEx_src_v1.2.0.zip`
6. **Publish release**。

这样两个平台共用一个仓库，N 网用户和 GitHub 用户都能下载。

### 2.4 仓库简介（About 栏）

- Description：
  `Removes the ZERO PARADES advert from Disco Elysium's main menu. Off-screen patch, no mod loader, fully reversible.`
- Topics：
  `disco-elysium`, `mod`, `unity`, `il2cpp`, `zero-parades`, `ad-remover`

---

## 3. 交付（怎么给出去）

### 3.1 给测试的朋友

直接把 `DiscoElysium_ZeroParades_AdRemover_Windows_v1.2.0.zip` 发给他，
转发文案用现成的 `dist/SEND-TO-FRIEND.txt`（微信/QQ 全文复制即可）。

让他跑 **装 → 卸 → 再装** 闭环：

1. `install.bat` → 进游戏，横幅应消失
2. `uninstall.bat` → 再进游戏，横幅应**回来**（回来才证明卸载干净）
3. `install.bat` → 再消失

反馈时让他带上：bat 窗口全文截图、Windows 版本、Steam 还是 GOG、
`disco_Data\level2` 的文件大小。

### 3.2 给公开用户

- **N 网用户**：从 mod 页下载 Main file，解压双击 `install.bat`。
- **GitHub 用户**：从 Releases 下载同一个包，README 里有完整说明。
- **Steam Deck / Linux 用户**：用包里的 `c4ad_mod.py`（只需 Python 3）。

---

## 4. 上传后自检

- [ ] `LICENSE` 占位符已替换
- [ ] N 网 Description 用的是 **BBCode** 版（页面显示标题是加粗大字，不是 `##`）
- [ ] N 网两个文件分别落在 **Main files** / **Optional files**
- [ ] 可选文件描述里写明了"源码，需自行编译"
- [ ] GitHub Release 挂上了两个 zip 附件
- [ ] 两个包里都**没有** `level2`、`.c4ad-backup`、`bin/`、`obj/`
- [ ] 版本号三处一致：压缩包名 / `CHANGELOG.md` / N 网文件条目，都是 `1.2.0`

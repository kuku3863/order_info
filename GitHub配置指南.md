# GitHub 配置指南

## 📋 准备工作

### 1. 安装 Git
如果还没有安装 Git，请先下载安装：
- 官网下载：https://git-scm.com/download/win
- 安装时选择默认选项即可

### 2. 配置 Git 用户信息
打开命令行（PowerShell 或 Git Bash），执行以下命令：

```bash
# 设置用户名（替换为你的GitHub用户名）
git config --global user.name "你的用户名"

# 设置邮箱（替换为你的GitHub邮箱）
git config --global user.email "你的邮箱@example.com"
```

## 🚀 上传到 GitHub 的步骤

### 方法一：使用 GitHub Desktop（推荐新手）

1. **下载安装 GitHub Desktop**
   - 官网：https://desktop.github.com/
   
2. **登录 GitHub 账户**
   - 打开 GitHub Desktop
   - 点击 "Sign in to GitHub.com"
   - 输入你的 GitHub 账户信息

3. **创建仓库**
   - 点击 "Create a New Repository on your hard drive"
   - Name: `order-management-system`（或你喜欢的名字）
   - Local path: 选择你的项目文件夹 `d:\桌面\学习`
   - 勾选 "Initialize this repository with a README"
   - 点击 "Create repository"

4. **发布到 GitHub**
   - 点击 "Publish repository"
   - 取消勾选 "Keep this code private"（如果你想公开）
   - 点击 "Publish repository"

### 方法二：使用命令行

1. **在项目目录初始化 Git**
```bash
cd d:\桌面\学习
git init
```

2. **添加文件到暂存区**
```bash
git add .
```

3. **提交文件**
```bash
git commit -m "Initial commit: 订单管理系统"
```

4. **在 GitHub 创建仓库**
   - 登录 GitHub.com
   - 点击右上角的 "+" 号
   - 选择 "New repository"
   - Repository name: `order-management-system`
   - 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"
   - 点击 "Create repository"

5. **连接本地仓库到 GitHub**
```bash
# 添加远程仓库（替换为你的GitHub用户名）
git remote add origin https://github.com/你的用户名/order-management-system.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

## 🔐 安全配置

### 1. 使用 Personal Access Token（推荐）

如果推送时要求密码，建议使用 Personal Access Token：

1. **创建 Token**
   - 登录 GitHub
   - 点击头像 → Settings
   - 左侧菜单 → Developer settings
   - Personal access tokens → Tokens (classic)
   - Generate new token (classic)
   - 选择权限：repo（完整仓库权限）
   - 生成并复制 token

2. **使用 Token**
   - 推送时用户名输入你的 GitHub 用户名
   - 密码输入刚才复制的 token

### 2. 配置 SSH（可选）

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "你的邮箱@example.com"

# 添加到 SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 复制公钥内容
cat ~/.ssh/id_ed25519.pub
```

然后在 GitHub Settings → SSH and GPG keys 中添加公钥。

## 📁 项目结构说明

已为你创建了 `.gitignore` 文件，以下文件/文件夹将被忽略：

- `__pycache__/` - Python 缓存文件
- `*.sqlite` - 数据库文件（包含敏感数据）
- `.vscode/` - IDE 配置
- `*.log` - 日志文件
- `app/static/uploads/` - 用户上传的文件
- `*.zip`, `*.7z` - 压缩包
- `*.bat` - 批处理文件
- 备份文件等

## 🔄 日常使用

### 提交更改
```bash
# 查看状态
git status

# 添加更改的文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到 GitHub
git push
```

### 拉取更新
```bash
# 从 GitHub 拉取最新更改
git pull
```

## ⚠️ 注意事项

1. **数据库文件**：`.gitignore` 已配置忽略数据库文件，避免上传敏感数据
2. **配置文件**：如果有包含密码等敏感信息的配置文件，请添加到 `.gitignore`
3. **定期备份**：虽然代码在 GitHub 上，但数据库需要单独备份
4. **分支管理**：建议使用分支进行开发，主分支保持稳定

## 🆘 常见问题

### 推送失败
- 检查网络连接
- 确认 GitHub 用户名和密码/token 正确
- 尝试使用 `git push --force-with-lease`（谨慎使用）

### 文件太大
- GitHub 单个文件限制 100MB
- 大文件请使用 Git LFS 或云存储

### 忘记提交信息
```bash
# 修改最后一次提交信息
git commit --amend -m "新的提交信息"
```

---

**祝你使用愉快！如有问题，随时询问。** 🎉
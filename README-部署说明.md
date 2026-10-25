# 小白爱AI｜人工智能趋势信息网

## 文件说明
- `index.html`：GitHub Pages 网站
- `scripts/scrape.py`：从公开 RSS / arXiv feed 抓取最近24小时信息，去重、分类并生成数据
- `data.json`：自动生成的网页数据
- `daily-brief.md`：自动生成的 Markdown 简报
- `.github/workflows/update.yml`：GitHub Actions 定时任务

## 部署步骤
1. 将本压缩包内的文件上传到现有仓库根目录，保留 `.github/workflows/update.yml` 的目录结构。
2. 仓库 Settings → Pages → Build and deployment，选择 `Deploy from a branch`，分支 `main`，目录 `/(root)`，保存。
3. 仓库 Actions 页面，若首次运行提示需要启用工作流，请点击启用。
4. Actions → `Update AI Daily Brief` → `Run workflow`，手动运行一次。
5. 等工作流完成后，检查仓库根目录是否生成 `data.json` 与 `daily-brief.md`，再打开 Pages 网站。

## 重要限制
- GitHub Pages 只负责展示；GitHub Actions 才负责定时采集。
- 当前版本使用公开 RSS 与 arXiv feed，不直接抓取 X / Reddit / YouTube 热榜，也没有 API 来验证点赞、播放量或赚钱收入。
- 每个分类最多显示5条；如果最近24小时没有足够的可靠新内容，就会显示不足提示，而不是用旧消息或编造内容补足。
- RSS 源可能变更或暂时不可用，可在 Actions 日志中查看错误。
- GitHub Actions 的免费额度及 GitHub Pages 使用条款请以 GitHub 当前政策为准。

# my-website

本仓库包含一个用于抓取知乎指定问题下所有回答的命令行脚本 `zhihu_scraper.py`。下面按照“准备环境 → 查看帮助 → 实际运行 → 常见疑问”四个步骤，带你完整体验脚本的使用方式。

## 1. 准备工作
1. 安装 [Python 3.8 及以上版本](https://www.python.org/downloads/)。
2. （可选）创建并激活虚拟环境，例如：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows 使用: .venv\Scripts\activate
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
   如果系统中同时存在 `python` 与 `python3`，请保持命令一致，例如使用 `python3` 与 `pip3`。

## 2. 查看命令行帮助
脚本自带帮助信息，可以先运行：
```bash
python zhihu_scraper.py --help
```
你会看到所有可选参数的说明，例如如何指定输出文件、请求间隔、一次抓取的回答数量以及如何提供 Cookie。遇到问题时，先查看这里能快速确认参数含义。

## 3. 实际运行示例
1. 找到要抓取的知乎问题页面，例如：https://www.zhihu.com/question/123456789。
2. 在终端进入脚本所在目录：
   ```bash
   cd /path/to/my-website
   ```
3. 执行脚本：
   ```bash
   python zhihu_scraper.py https://www.zhihu.com/question/123456789 --limit 20 --delay 0.5 -o answers.txt
   ```
   - `--limit` 控制每次请求的回答数量（默认 20，建议不要调得太高）。
   - `--delay` 控制请求之间的间隔秒数，适当增加可以降低触发风控的概率。
   - `-o/--output` 可以把抓取的结果保存到文件，否则内容会直接打印到终端。
   - 如果知乎提示需要登录，可在浏览器已登录状态下复制整段 Cookie，并通过 `--cookie "z_c0=...;"` 传入。

**示例输出（节选）**：
```text
答案 1（作者：知乎用户）
----------------------------------------
第一位回答者的正文……

答案 2（作者：某某）
----------------------------------------
第二位回答者的正文……
```

脚本运行结束后，终端会显示“已将 X 条回答保存到 answers.txt”或直接打印所有回答文本。

## 4. 常见疑问
- **命令提示找不到 `python`？** 在 Windows 上可以尝试 `py`；在部分 Linux/macOS 环境下使用 `python3`、`pip3`。
- **提示缺少 `requests` 模块？** 说明依赖尚未安装，重新执行 `pip install -r requirements.txt`。
- **接口返回 403 或为空？** 增加 `--delay`、减小 `--limit`，必要时携带有效 Cookie 并确认该问题对登录用户可见。
- **想只抓取部分回答？** 修改命令中的 `--limit`，同时可以按 Ctrl+C 手动停止。

只需按上述顺序操作，就能顺利抓取指定问题的全部回答。

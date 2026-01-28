📝 NotebookLM 门诊记录单 RPA 自动化助手

本项目是一个基于 Playwright 的自动化 RPA 工具，专门用于批量调用 Google NotebookLM 的 AI 能力。它能自动读取指定文件夹中的医疗素材（文本、PDF、图片），通过 AI 梳理并生成标准格式的 Word 版门诊记录单。

🛠️ 第一步：环境配置

请在 Anaconda Prompt 或终端中依次执行以下步骤：

1. 创建并激活虚拟环境

# 创建名为 nblm 的环境，建议使用 Python 3.10
conda create -n nblm python=3.10

# 激活环境
conda activate nblm


2. 安装项目依赖

# 安装必要的 Python 库
pip install playwright python-docx playwright-stealth

# 安装浏览器内核（本项目强制使用 Microsoft Edge）
playwright install msedge


⚙️ 第二步：路径配置

在运行脚本前，请使用编辑器打开 run.py，根据你的电脑实际情况修改以下路径：

变量名

说明

BASE_DIR

项目的主目录（包含脚本的路径）

SOURCE_FOLDER

源文件夹：请将待处理的病人资料按文件夹存放于此

OUTPUT_FOLDER

结果文件夹：生成的 Word 门诊单将保存在这里

文件夹结构示例： > test/张三_20231024/ (放张三的所有检查报告、图片等)

test/李四_20231025/ (放李四的相关资料)

🚀 第三步：操作流程

整个流程分为 “登录授权” 和 “自动化执行” 两个阶段。

1. 登录授权（仅需执行一次）

由于 Google 账号有严格的登录校验，我们需要先手动登录并保存状态：

python log.py


操作： 脚本会启动一个 Edge 浏览器。

动作： 请在弹出的浏览器中手动完成 Google 账号登录。

结束： 登录成功并看到 NotebookLM 主界面后，回到终端按 回车键。脚本会保存登录信息到 user_data 文件夹并关闭浏览器。

2. 批量生成门诊记录单

确保已关闭所有由脚本打开的 Edge 窗口后，运行核心脚本：

python run.py


自动化逻辑：

自动遍历 SOURCE_FOLDER 下的子文件夹。

为每个文件夹在 NotebookLM 中新建一个笔记本。

批量上传该文件夹内的所有文件。

自动输入预设的 Prompt（提示词）。

等待 AI 回复完成后，将结果抓取并导出为 .docx 文件。

⚠️ 注意事项

环境冲突： 运行 run.py 前必须关闭 log.py 打开的浏览器，否则会因为数据目录被锁定而报错。

网络要求： 必须确保网络环境可以稳定访问 notebooklm.google.com。

Prompt 修改： 如果需要更改生成的格式，可以在 run.py 的 PROMPT_TEXT 变量中修改指令。

防检测机制： 脚本模拟了真人的输入速度和操作行为，但请勿在短时间内极高频率地运行，以免触发 Google 的风控验证。

📂 项目结构

log.py: 用于初始化环境和手动登录。

run.py: 核心执行逻辑，负责批量处理。

user_data/: (自动生成) 存放浏览器缓存和登录状态。

README.md: 项目操作指南。
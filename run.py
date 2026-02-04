import os
import time
import re
from docx import Document
from playwright.sync_api import sync_playwright
import playwright_stealth

# ================= 配置区 =================
BASE_DIR = r"C:\Users\asus\Desktop\RPA_GG"
USER_DATA_DIR = os.path.join(BASE_DIR, "user_data")
SOURCE_FOLDER = r"C:\Users\asus\Desktop\test" 
OUTPUT_FOLDER = r"C:\Users\asus\Desktop\result"
import textwrap

PROMPT_TEXT = textwrap.dedent("""
"# Role: 临床医学数据整理专家\\n# Task: 根据原始患者资料撰写标准化、纯净版临床病历摘要，使用中文宋体，严谨溯源不得包含来源编号。\\n\\n### 1. 核心约束\\n- **严禁溯源：** 输出内容中不得包含任何原始资料中的任何引用来源编号。\\n- **客观真实：** 仅基于原始数据，严禁臆造或推测未提及的信息。\\n- **专业规范：** 使用医学标准术语（如：脉管内癌栓、ECOG评分、三线治疗、PD/SD/PR等）。\\n\\n### 2. 输出结构与格式要求\\n请严格按照以下层级排版，确保各级标题清晰：\\n\\n## 【基础信息】\\n- **姓名：**\\n- **性别：**\\n- **年龄：**\\n\\n## 【主诉】\\n- 原始数据中明确提及的‘主诉’内容。\\n\\n## 【一、现病史】\\n- **诊疗经过：** 必须按 YYYY-MM-DD 格式，清晰描述：\\n  1. 发现病情及首诊细节。\\n  2. 手术情况：手术名称、术后病理细节（分期、分化程度、切缘情况等）。\\n  3. 各线治疗方案：明确标注起止日期、药物组合（如：化疗、靶向、免疫治疗）。\\n  4. 疗效评估：历次复查的对比情况、病情进展（PD）描述。\\n- **当前症状：** 描述目前的症状、体征表现及 ECOG 体能评分。\\n\\n## 【二、既往史】\\n - 非本病肿瘤史：\\n 慢性病史：\\n 手术史：\\n 过敏史：\\n\\n## 【三、辅助检查】\\n- 包含检查项目名称、检查/报告日期、出具报告的机构、检查结果\\n1. **病理及免疫组化：** 详细列出常规 IHC 指标及靶向/免疫相关核心指标。\\n2. **基因检测 (NGS)：** 描述主要变异基因、TMB/MSI 状态及化疗药物代谢评估等。\\n3. **影像学检查：** 包含最新的解剖学改变及 RECIST 评估结论。\\n4. **实验室检查：** 列出肿瘤标志物、血常规、生化等检查的异常指标。"
""").strip()

if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
# ==========================================

def save_to_word(content, folder_name):
    doc = Document()
    doc.add_heading(f'临床病历摘要 - {folder_name}', 0)
    doc.add_paragraph(content)
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", folder_name)
    save_path = os.path.join(OUTPUT_FOLDER, f"{safe_name}_病历摘要.docx")
    doc.save(save_path)
    return save_path

def run_notebooklm_final_fix():
    folder_groups = {}
    for root, dirs, files in os.walk(SOURCE_FOLDER):
        valid_files = [os.path.join(root, f) for f in files if f.lower().endswith(('.txt', '.pdf', '.docx', '.png', '.jpg', '.jpeg')) and not f.startswith('~$')]
        if valid_files: folder_groups[os.path.basename(root)] = valid_files

    with sync_playwright() as p:
        print("🚀 启动 NotebookLM 引擎...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, channel="msedge", headless=False,
            ignore_default_args=["--enable-automation"], args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()
        try: playwright_stealth.stealth(page)
        except: pass

        for folder_name, file_paths in folder_groups.items():
            print(f"\n📁 正在处理: 【{folder_name}】")
            try:
                page.goto("https://notebooklm.google.com/", wait_until="networkidle")
                page.get_by_text("新建笔记本").click()
                page.wait_for_url("**/notebook/*", timeout=50000)

                # --- 原始上传逻辑 ---
                print("🎯 正在上传文件...")
                with page.expect_file_chooser() as fc_info:
                    page.get_by_text("上传文件").click()
                file_chooser = fc_info.value
                file_chooser.set_files(file_paths)
                
                # 给充足的时间让“9个来源”处理完成
                print("⏳ 等待文件上传解析...")
                time.sleep(120) 

                # --- 输入与发送逻辑 (重点修复) ---
                print("⌨️ 准备输入指令...")
                # 定位输入框
                chat_box = page.locator("textarea.query-box-input, [role='textbox']").last
                chat_box.wait_for(state="visible")
                
                initial_count = page.locator("button:has-text('保存到笔记')").count()

                # 点击并模拟真人输入，触发按钮变蓝
                chat_box.click()
                chat_box.press_sequentially(PROMPT_TEXT, delay=20) 
                time.sleep(1)

                # 尝试点击蓝色发送按钮
                # 根据截图：按钮在 query-box 容器内，通常带有 mat-icon
                send_button = page.locator(".query-box button:has(mat-icon), .query-box button[aria-label*='发'], .query-box button.send-button").last
                
                if send_button.is_visible():
                    print("🚀 点击发送按钮...")
                    # 强制点击，防止被透明层遮挡
                    send_button.click(force=True, timeout=10000)
                else:
                    print("⚠️ 没找到按钮，使用 Enter 键发送...")
                    page.keyboard.press("Enter")

                # --- 原始提取逻辑 ---
                print("🤖 等待 AI 响应完成...")
                for i in range(120):
                    if page.locator("button:has-text('保存到笔记')").count() > initial_count:
                        print("✅ AI 响应已完成")
                        break
                    time.sleep(2)

                print("⏳ 预留 30 秒提取内容...")
                time.sleep(30) 

                target_locator = page.locator(".message-content")
                if target_locator.count() > 0:
                    final_text = target_locator.last.inner_text()
                    path = save_to_word(final_text, folder_name)
                    print(f"🎉 处理成功: {path}")
                else:
                    print("❌ 未能定位到回复内容")

            except Exception as e:
                print(f"❌ 错误: {e}")
                page.screenshot(path=f"fail_{folder_name}.png")

        context.close()

if __name__ == "__main__":
    run_notebooklm_final_fix()

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
PROMPT_TEXT = "请帮我梳理成 门诊记录单 格式，不带来源编号（即去掉末尾数字）的纯净版门诊记录单，删去诊断建议部分"

if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
# ==========================================

def save_to_word(content, folder_name):
    doc = Document()
    doc.add_heading(f'门诊记录单 - {folder_name}', 0)
    doc.add_paragraph(content)
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", folder_name)
    save_path = os.path.join(OUTPUT_FOLDER, f"{safe_name}_汇总记录.docx")
    doc.save(save_path)
    return save_path

def run_notebooklm_fixed_v5():
    folder_groups = {}
    for root, dirs, files in os.walk(SOURCE_FOLDER):
        valid_files = [os.path.join(root, f) for f in files if f.lower().endswith(('.txt', '.pdf', '.docx', '.png', '.jpg', '.jpeg')) and not f.startswith('~$')]
        if valid_files: folder_groups[os.path.basename(root)] = valid_files

    with sync_playwright() as p:
        print("🚀 启动 NotebookLM 稳定版引擎...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, channel="msedge", headless=False, slow_mo=100,
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
                page.wait_for_url("**/notebook/*", timeout=30000)

                # --- 原始上传代码 ---
                print("🎯 正在上传文件...")
                with page.expect_file_chooser() as fc_info:
                    page.get_by_text("上传文件").click()
                file_chooser = fc_info.value
                file_chooser.set_files(file_paths)
                print(f"✅ 已上传 {len(file_paths)} 个文件")

                # --- 监控输入框就绪 ---
                chat_box = page.locator("textarea.query-box-input").last
                chat_box.wait_for(state="visible", timeout=120000)
                
                initial_count = page.locator("button:has-text('保存到笔记')").count()

                print("⌨️ 正在注入梳理指令...")
                chat_box.click(force=True)
                chat_box.fill(PROMPT_TEXT)
                chat_box.dispatch_event("input")
                time.sleep(1)

                # --- 发送指令 ---
                page.keyboard.press("Enter")
                print("🤖 指令已发送...")

                # --- 监控生成完成 ---
                for i in range(150):
                    if page.locator("button:has-text('保存到笔记')").count() > initial_count:
                        print("✅ AI 触发完成标志")
                        break
                    time.sleep(2)

                # --- ⭐ 核心修复：根据源码进行精准抓取 ---
                print("⏳ 固定等待 30 秒确保内容全部写完...")
                time.sleep(30) 

                print("📝 正在精准提取正文内容...")
                
                # 方案：直接定位所有的 message-content，取最后一个
                # 根据 HTML 源码，message-content 专门存放回复文本
                # 不会包含 header 里的 "7个来源" 和 footer 里的图标
                
                target_locator = page.locator(".message-content")
                
                if target_locator.count() > 0:
                    # 获取最新回复的纯文本
                    final_text = target_locator.last.inner_text()
                    
                    if len(final_text) > 50:
                        path = save_to_word(final_text, folder_name)
                        print(f"🎉 提取成功！文件已存入: {path}")
                    else:
                        print("⚠️ 提取到的文本太短，尝试回退到 markdown 容器...")
                        # 备选：如果 content 内部有 markdown 结构，尝试深度探测
                        final_text = page.locator(".markdown-rendered, [role='presentation']").last.inner_text()
                        save_to_word(final_text, folder_name)
                else:
                    raise Exception("无法定位到 .message-content 容器")

            except Exception as e:
                print(f"❌ 流程出错: {e}")
                page.screenshot(path=f"debug_{folder_name}.png")

        context.close()
        print("\n✅ 处理结束。")

if __name__ == "__main__":
    run_notebooklm_fixed_v5()
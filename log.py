import os
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.getcwd(), "user_data")

def launch_edge_for_login():
    with sync_playwright() as p:
        print(f"🚀 正在通过 Microsoft Edge 启动笔记本...")
        
        # 使用持久化上下文
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="msedge",  # 👈 关键点：指定使用 Edge 浏览器
            headless=False,
            # 💡 核心：抹除自动化控制特征，防止被 Google 检测
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
            viewport={'width': 1400, 'height': 900}
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # 强制抹除 navigator.webdriver 特征
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page.goto("https://notebooklm.google.com/")
        
        print("\n📢 请在 Edge 窗口中完成 Google 登录。")
        print("✅ 登录成功后，回到这里按回车键保存并退出。")
        input("按下回车键以保存并退出...")
        context.close()

if __name__ == "__main__":
    launch_edge_for_login()
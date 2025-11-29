"""
PythonAnywhere 自动续期脚本
优先使用API接口，如果不可用则回退到浏览器自动化
"""

import os
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session():
    """创建带重试机制的requests会话"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def renew_via_api(username, password):
    """尝试通过API接口续期"""
    session = get_session()
    
    # 1. 登录获取session
    print("正在登录PythonAnywhere...")
    login_url = "https://www.pythonanywhere.com/login/"
    
    # 先获取登录页面获取CSRF token
    response = session.get(login_url)
    if response.status_code != 200:
        return False, f"无法访问登录页面: {response.status_code}"
    
    # 尝试从cookie或页面中获取CSRF token
    csrf_token = None
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
    elif 'csrfmiddlewaretoken' in response.text:
        # 从HTML中提取CSRF token
        import re
        match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
        if match:
            csrf_token = match.group(1)
    
    # 2. 提交登录表单
    login_data = {
        'auth-username': username,
        'auth-password': password,
    }
    if csrf_token:
        login_data['csrfmiddlewaretoken'] = csrf_token
    
    headers = {
        'Referer': login_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = session.post(login_url, data=login_data, headers=headers, allow_redirects=False)
    
    # 检查是否登录成功（通常会有重定向）
    if response.status_code not in [200, 302]:
        return False, f"登录失败: {response.status_code}"
    
    # 如果重定向，跟随重定向
    if response.status_code == 302:
        session.get(response.headers.get('Location', '/'))
    
    # 3. 尝试调用续期API
    # 根据页面结构，续期可能是POST到 /user/{username}/webapps/{webapp_id}/extend/
    webapp_id = f"{username}_pythonanywhere_com"
    extend_url = f"https://www.pythonanywhere.com/user/{username}/webapps/{webapp_id}/extend/"
    
    # 尝试POST请求
    response = session.post(extend_url, headers=headers, allow_redirects=True)
    
    if response.status_code == 200:
        # 检查响应内容确认是否成功
        if 'success' in response.text.lower() or 'extended' in response.text.lower():
            return True, "续期成功（通过API）"
        elif 'error' in response.text.lower():
            return False, "API返回错误"
    
    return False, "API方式不可用，将使用浏览器自动化"


def renew_via_browser(username, password):
    """使用浏览器自动化续期（回退方案）"""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        return False, "Playwright未安装，请运行: pip install playwright && playwright install chromium"
    
    print("使用浏览器自动化方式...")
    
    with sync_playwright() as p:
        headless_mode = os.getenv("HEADLESS", "true").lower() == "true"
        browser = p.chromium.launch(headless=headless_mode)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        try:
            # 登录
            print("正在登录...")
            page.goto("https://www.pythonanywhere.com/login/")
            page.wait_for_load_state('networkidle')
            
            username_input = page.wait_for_selector("input[name='auth-username'], input#id_auth-username", timeout=10000)
            username_input.fill(username)
            
            password_input = page.wait_for_selector("input[name='auth-password'], input#id_auth-password", timeout=10000)
            password_input.fill(password)
            
            login_button = page.wait_for_selector("button[type='submit'], input[type='submit']", timeout=10000)
            login_button.click()
            
            page.wait_for_url("**/user/**", timeout=20000)
            print("✓ 登录成功")
            
            # 导航到webapp页面
            print("正在导航到Web应用配置页面...")
            webapp_id = f"{username}_pythonanywhere_com"
            webapp_url = f"https://www.pythonanywhere.com/user/{username}/webapps/#tab_id_{webapp_id}"
            page.goto(webapp_url)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(3000)
            
            # 查找并点击按钮
            print("正在查找续期按钮...")
            
            # 监听网络请求，看点击按钮时是否有API调用
            api_called = []
            def handle_request(request):
                if 'extend' in request.url.lower() or 'webapp' in request.url.lower():
                    api_called.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': request.headers
                    })
            
            page.on('request', handle_request)
            
            # 查找按钮
            button_selectors = [
                "button:has-text('Run until 3 months from today')",
                "button:has-text('Run until')",
            ]
            
            button_found = False
            for selector in button_selectors:
                try:
                    button = page.wait_for_selector(selector, timeout=3000)
                    if button:
                        print(f"✓ 找到按钮")
                        button.scroll_into_view_if_needed()
                        page.wait_for_timeout(1000)
                        
                        print("正在点击按钮...")
                        button.click()
                        page.wait_for_timeout(3000)
                        
                        if api_called:
                            print(f"检测到API调用: {api_called[0]['method']} {api_called[0]['url']}")
                        
                        print("✓ 按钮已点击")
                        button_found = True
                        break
                except PlaywrightTimeout:
                    continue
            
            if not button_found:
                return False, "无法找到续期按钮"
            
            browser.close()
            return True, "续期成功（通过浏览器自动化）"
            
        except Exception as e:
            browser.close()
            return False, f"浏览器自动化失败: {str(e)}"


def main():
    username = os.getenv("PYTHONANYWHERE_USERNAME")
    password = os.getenv("PYTHONANYWHERE_PASSWORD")
    
    if not username or not password:
        print("错误: 请设置环境变量 PYTHONANYWHERE_USERNAME 和 PYTHONANYWHERE_PASSWORD")
        sys.exit(1)
    
    webapp_id = f"{username}_pythonanywhere_com"
    
    print("=" * 60)
    print("PythonAnywhere 自动续期脚本")
    print("=" * 60)
    print(f"用户名: {username}")
    print(f"Web应用ID: {webapp_id}\n")
    
    # 先尝试API方式
    print("[方法1] 尝试使用API接口...")
    success, message = renew_via_api(username, password)
    
    if not success and "API方式不可用" in message:
        # 如果API不可用，使用浏览器自动化
        print(f"\n[方法2] {message}")
        success, message = renew_via_browser(username, password)
    
    print("\n" + "=" * 60)
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

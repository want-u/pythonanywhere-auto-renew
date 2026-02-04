import os
import time
import requests

print("DEBUG: 开始执行")
username = os.getenv("PYTHONANYWHERE_USERNAME")
password = os.getenv("PYTHONANYWHERE_PASSWORD")

print(f"DEBUG: 用户名 = {username}")
print(f"DEBUG: 密码 = {'*' * len(password) if password else 'None'}")


session = requests.Session()
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.pythonanywhere.com",
    "Referer": "https://www.pythonanywhere.com/login/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# 1、获取登录页面 - csrfmiddlewaretoken
url = "https://www.pythonanywhere.com/login/"
response = session.get(url, headers=headers)
print("1、获取登录页面 - csrfmiddlewaretoken", response)

s = response.text
# name="csrfmiddlewaretoken" value="rZhgV59Z9z1Q80Yw5XrLCEOe3e5wZYLIZp6ppbBluH4izIXVXVD7uc39wyhHgXPn"
csrfmiddlewaretoken_start = 'name="csrfmiddlewaretoken" value="'
value_key_index = s.find(csrfmiddlewaretoken_start)
val_start = value_key_index + len(csrfmiddlewaretoken_start)
val_end = s.find('"', val_start)
csrfmiddlewaretoken = s[val_start:val_end]

# 打印结果
print("csrfmiddlewaretoken:", csrfmiddlewaretoken)
time.sleep(1.5)

# 2、提交登录表单
url = "https://www.pythonanywhere.com/login/"
data = {
    "csrfmiddlewaretoken": csrfmiddlewaretoken,
    "auth-username": username,
    "auth-password": password,
    "login_view-current_step": "auth",
}
response = session.post(url, headers=headers, data=data)
# print(response.text)
print("2、提交登录表单", response)

if response.status_code != 200:
    exit(403)
time.sleep(1.5)

# 3、获取webapps页面 - csrfmiddlewaretoken
url = "https://www.pythonanywhere.com/user/%s/webapps/" % username
response = session.get(url, headers=headers)
# print(response.text)
print("3、获取webapps页面 - csrfmiddlewaretoken", response)

s = response.text
csrfmiddlewaretoken_start = 'name="csrfmiddlewaretoken" value="'
value_key_index = s.find(csrfmiddlewaretoken_start)
val_start = value_key_index + len(csrfmiddlewaretoken_start)
val_end = s.find('"', val_start)
csrfmiddlewaretoken = s[val_start:val_end]
print("csrfmiddlewaretoken:", csrfmiddlewaretoken)
time.sleep(1.5)

# 4、进行网站续期
url = "https://www.pythonanywhere.com/user/%s/webapps/%s.pythonanywhere.com/extend" % (
    username,
    username,
)
data = {"csrfmiddlewaretoken": csrfmiddlewaretoken}
response = session.post(url, headers=headers, data=data)
# print(response.text)
print("4、进行网站续期", response)

print("DEBUG: 自动续期完成!")

import requests
import os

# 测试文件上传功能
url = "http://localhost:8000/api/upload"

# 准备测试文件
file_path = "backend/requirements.txt"
if not os.path.exists(file_path):
    print(f"测试文件不存在: {file_path}")
    exit(1)

# 准备表单数据
files = {
    'file': open(file_path, 'rb'),
}

data = {
    'description': '测试文件上传',
    'project_id': 'project_001',
}

print(f"测试文件上传到: {url}")
print(f"使用测试文件: {file_path}")

# 发送请求
try:
    response = requests.post(url, files=files, data=data)
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        print("\n测试成功！")
    else:
        print(f"\n测试失败，状态码: {response.status_code}")
except Exception as e:
    print(f"\n测试失败，发生异常: {e}")
finally:
    # 关闭文件
    files['file'].close()
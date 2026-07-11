#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

BASE_URL = 'http://localhost:8000'

# 登录
login_data = {'username': 'admin', 'password': 'admin123'}
response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 测试图像预测
image_path = 'backend/uploads/Apple2 (1).jpg'
print('=== 测试图像预测 ===')
with open(image_path, 'rb') as f:
    files = {'file': ('test.jpg', f, 'image/jpeg')}
    response = requests.post(f'{BASE_URL}/api/model/predict', files=files, headers=headers)

print(f'状态码: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print(f'预测结果:')
    print(f'  病害名称: {result.get("disease_name")}')
    print(f'  置信度: {result.get("confidence")}')
    print(f'  风险等级: {result.get("risk_level")}')
    print(f'  类别名称: {result.get("class_name")}')
else:
    print(f'失败: {response.text}')
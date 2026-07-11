#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

BASE_URL = 'http://localhost:8000'

print('=== 测试后端API ===')

# 1. 登录
print('\n1. 登录测试')
login_data = {'username': 'admin', 'password': 'admin123'}
response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
print(f'状态码: {response.status_code}')
if response.status_code == 200:
    token = response.json()['access_token']
    print('登录成功')
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. 获取用户信息
    print('\n2. 获取用户信息')
    response = requests.get(f'{BASE_URL}/api/auth/me', headers=headers)
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.json()}')
    
    # 3. 模型状态
    print('\n3. 模型状态')
    response = requests.get(f'{BASE_URL}/api/model/status', headers=headers)
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text}')
    
    # 4. RAG查询
    print('\n4. RAG查询')
    response = requests.get(f'{BASE_URL}/api/rag/query', params={'query': '苹果黑星病'}, headers=headers)
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text}')
    
    # 5. 模型指标
    print('\n5. 模型指标')
    response = requests.get(f'{BASE_URL}/api/model/metrics', headers=headers)
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text}')
else:
    print(f'登录失败: {response.text}')
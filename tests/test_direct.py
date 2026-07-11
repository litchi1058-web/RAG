#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

BASE_URL = 'http://localhost:8000'

print('=== 直接测试 ===')
response = requests.get(f'{BASE_URL}/api/health')
print(f'health: {response.status_code} - {response.text}')

# 检查路由
import urllib.request
try:
    with urllib.request.urlopen(f'{BASE_URL}/openapi.json') as f:
        content = f.read().decode('utf-8')
        if 'model' in content:
            print('openapi.json contains model routes')
        else:
            print('openapi.json does NOT contain model routes')
except Exception as e:
    print(f'Error: {e}')
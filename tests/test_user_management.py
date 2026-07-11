#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

BASE_URL = 'http://localhost:8000'

print('=== 测试用户管理API ===')

# 1. 登录
print('\n1. 登录')
login_data = {'username': 'admin', 'password': 'admin123'}
response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
print('登录成功')

# 2. 获取用户列表
print('\n2. 获取用户列表')
response = requests.get(f'{BASE_URL}/api/users', headers=headers)
print(f'状态码: {response.status_code}')
users = response.json()
print(f'用户数量: {len(users)}')
for u in users:
    print(f"  - ID:{u['id']}, 用户名:{u['username']}, 角色:{u['role']}, 状态:{u['is_active']}")

# 3. 新增用户
print('\n3. 新增用户')
create_data = {'username': 'test_user', 'password': 'test123', 'role': 'farmer'}
response = requests.post(f'{BASE_URL}/api/users', json=create_data, headers=headers)
print(f'状态码: {response.status_code}')
if response.status_code == 200:
    print(f"创建成功: {response.json()}")
else:
    print(f"失败: {response.text}")

# 4. 再次获取用户列表
print('\n4. 再次获取用户列表')
response = requests.get(f'{BASE_URL}/api/users', headers=headers)
users = response.json()
print(f'用户数量: {len(users)}')
for u in users:
    print(f"  - ID:{u['id']}, 用户名:{u['username']}, 角色:{u['role']}, 状态:{u['is_active']}")

# 5. 编辑用户
test_user = next((u for u in users if u['username'] == 'test_user'), None)
if test_user:
    print(f'\n5. 编辑用户 (ID: {test_user["id"]})')
    update_data = {'role': 'data_manager', 'is_active': 1}
    response = requests.put(f'{BASE_URL}/api/users/{test_user["id"]}', json=update_data, headers=headers)
    print(f'状态码: {response.status_code}')
    if response.status_code == 200:
        print(f"更新成功: {response.json()}")
    else:
        print(f"失败: {response.text}")

# 6. 删除用户
test_user = next((u for u in users if u['username'] == 'test_user'), None)
if test_user:
    print(f'\n6. 删除用户 (ID: {test_user["id"]})')
    response = requests.delete(f'{BASE_URL}/api/users/{test_user["id"]}', headers=headers)
    print(f'状态码: {response.status_code}')
    if response.status_code == 200:
        print(f"删除成功: {response.json()}")
    else:
        print(f"失败: {response.text}")

# 7. 测试删除admin（应该失败）
print('\n7. 测试删除admin（应该失败）')
response = requests.delete(f'{BASE_URL}/api/users/1', headers=headers)
print(f'状态码: {response.status_code}')
print(f'响应: {response.text}')
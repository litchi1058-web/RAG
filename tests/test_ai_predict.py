#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

image_path = 'backend/uploads/Apple2 (1).jpg'
url = 'http://localhost:8001/ai/predict'

try:
    with open(image_path, 'rb') as f:
        files = {'file': ('test.jpg', f, 'image/jpeg')}
        response = requests.post(url, files=files)
    
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print(f'Response: {response.json()}')
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Exception: {e}')
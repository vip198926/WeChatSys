#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021-1-31 18:57:16
# @Author  : 青稞
# @Site    : 生成100个不重复的28位数随机字符串
# @File    : test.py

import random
import string

# 生成100个不重复的28位数随机字符串
results = []
for i in range(100):
    result = random.sample(string.ascii_letters, 28)
    results.append("".join(result))

for i in results:
    print(i)
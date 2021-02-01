#!/usr/bin/python3
# -*- encoding=utf8 -*-

# 视一视刷广告
# By 青稞
# 2021-01-29 15:55:10

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。


import time
from logger import logger
from multiProgress import Partition, Reader
from wxSys import brushAds

if __name__ == '__main__':

    file_name = 'data.txt'  # 数据文件名
    thread_num = 5  # 线程数量

    start_tool = brushAds()  # 初始化
    start_time = time.time()  # 起始时间
    p = Partition(file_name, thread_num)
    t = []
    pos = p.part()
    # 生成线程
    for i in range(thread_num):
        t.append(Reader(file_name, *pos[i]))
    # 开启线程
    for i in range(thread_num):
        t[i].start()
    for i in range(thread_num):
        t[i].join()

    end_time = time.time()  # 结束时间
    start_tool.send_wechat()

    logger.info("全部任务完成，用时：%f" % (end_time - start_time))

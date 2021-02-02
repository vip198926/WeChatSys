#!/usr/bin/python3
# -*- encoding=utf8 -*-

# 视一视刷广告
# By 青稞
# 2021-01-29 15:55:10

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。


import time
from logger import logger
from wxSys import brushAds

if __name__ == '__main__':
    start_time = time.time()  # 起始时间
    logger.warning('------任务开始-------->..')
    start_tool = brushAds()  # 初始化

    start_tool.randomData()  # 随机生成新的数据文件

    start_tool.start_Thread()  # 启动多线程任务

    start_tool.send_wechat(start_time)  # 把开始时间传给推送到微信以计算总共耗时

    logger.warning('全部任务完成，停止运行')

#!/usr/bin/python3
# -*- encoding=utf8 -*-

# 视一视刷广告
# By 青稞
# 2021-01-29 15:55:10

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。
import time
from log.logger import logger
from wx_sys.wxSys import brushAds

if __name__ == '__main__':
    start_time = time.time()  # 起始时间
    logger.warning('------任务开始-------->..')
    start_tool = brushAds()  # 初始化
    # 加入异常处理，中断后也可以推送到微信
    try:
        start_tool.randomData()  # 随机生成新的数据文件
        start_tool.start_Thread()  # 启动多线程任务
    except:
        logger.exception('运行发生异常')
    finally:  # 有无异常都执行的语句
        start_tool.send_wechat(start_time)  # 把开始时间传给推送到微信以计算总共耗时
        logger.warning('Good Bye！')

#!/usr/bin/python3
# -*- encoding=utf8 -*-

# 视一视刷广告
# By 青稞
# 2021-01-29 15:55:10

import logging
import logging.handlers
import os
import time

from wx_sys.config import global_config

'''
日志模块
'''
# 把获取的时间转换成"年月日格式”
time_now = time.strftime("%Y%m%d", time.localtime())
logs_dir = '../logs'
logs_name = logs_dir + '/wxSys_' + str(time_now) + '.log'
# print(logs_dir, logs_name)
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

LOG_FILENAME = logs_name
logger = logging.getLogger()
LOG_LEVEL = global_config.get('config', 'log_level')

# 从配置文件中读取日志级别并设置日志级别
if LOG_LEVEL == 'debug':
    log_level = logging.DEBUG
    formatter_ = logging.Formatter('%(asctime)s %(process)d %(threadName)s %(filename)s[%(lineno)d] %(levelname)s: %(message)s', datefmt= '%m-%d %H:%M:%S')
elif LOG_LEVEL == 'info':
    log_level = logging.INFO
    formatter_ = logging.Formatter('%(asctime)s %(threadName)s %(levelname)s: %(message)s', datefmt='%m-%d %H:%M:%S')
elif LOG_LEVEL == 'warn':
    log_level = logging.WARNING
    formatter_ = logging.Formatter('%(asctime)s %(threadName)s %(levelname)s: %(message)s', datefmt='%m-%d %H:%M:%S')


def set_logger():
    logger.setLevel(log_level)
    formatter = formatter_
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=10485760, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


set_logger()

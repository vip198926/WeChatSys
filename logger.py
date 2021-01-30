import logging
import logging.handlers
import os
import time

'''
日志模块
'''
# 把获取的时间转换成"年月日格式”
time_now = time.strftime("%Y%m%d", time.localtime())
logs_dir = 'logs'
logs_name = logs_dir + '/wxSys_' + str(time_now) + '.log'
# print(logs_dir, logs_name)
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

LOG_FILENAME = logs_name
logger = logging.getLogger()


def set_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    # formatter = logging.Formatter('%(asctime)s - %(process)d-%(threadName)s - '
    #                               '%(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=10485760, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


set_logger()

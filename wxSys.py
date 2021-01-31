#!/usr/bin/python3
# -*- encoding=utf8 -*-

# 视一视刷广告
# By 青稞
# 2021-01-29 15:55:10


import hashlib
import http.client
import json
import random
import string
import time

import requests

from logger import logger


class brushAds(object):
    def __init__(self):

        # self.missionStart()
        self.requestURL = ""  # 请求网址
        self.requestData = ""  # 请求数据
        self.submitURL = ""  # 提交网址
        self.submitData = ""  # 提交数据
        self.randnum = ""  # 提交数据中用到的参数randnum
        self.adid = ""  # 提交数据中用到的参数adid
        self.income = 0.0  # 计数收益

    def missionStart(self, sub_num=20, retry=3):
        """
        开始任务执行

        :param sub_num: 提交次数，默认20次
        :param retry: 提交返回空后重试次数，默认3次
        :return: 无
        """
        logger.info('任务开始..')
        # 从文件读取账号数据
        file_object = self.get_data_file()
        # 遍历账号数据
        m = 0.0  # 账号计数
        for line in file_object:
            m += 1
            # print(line)
            # 从账号数据中分割出请求的网址和表求的post数据
            data = line.split("----")
            self.requestURL = data[0]  # 请求网址
            self.requestData = data[1]  # 请求数据
            # print(self.requestURL)
            # print(self.requestData)
            n = 0  # 提交次数计数
            i = 0  # 提交返回空计数(任务上限后返回空)
            while n < sub_num:
                n += 1
                logger.info('当前执行第：%d 条数据 第：%d 次请求, 今日累计收益：%.3f', m, n, self.income)
                # 请求广告接口，返回提交所需要的参数uid,randnum
                while True:
                    try:
                        res = self.webpage_visit(self.requestURL, self.requestData)
                        break
                    except Exception as e:
                        logger.error('请求数据发生异常,异常信息【%s】稍后重试..', str(e))
                    time.sleep(random.randint(1, 2))

                # print(res)
                if res is None:
                    logger.error("获取提交所需参数失败，返回信息：【】")
                    # break 语句可以跳出 for 和 while 的循环体。如果你从 for 或 while 循环中终止，任何对应的循环 else 块将不执行。
                    # continue 语句被用来告诉 Python 跳过当前循环块中的剩余语句，然后继续进行下一轮循环。
                    continue

                # logger.info("获取提交所需参数成功，返回信息：" + res)
                # logger.info('获取提交所需参数成功')
                # 将返回的json 数据 res 转换成表
                s = json.loads(res)
                # 提取提交所需要的adid和randnum
                self.randnum = s['randnum']
                self.adid = s['uid']
                # print(self.randnum, self.adid)
                # 构造提交所需要的网址和post数据 成功True,失败False
                makeRes = self.ConsReqParameters(self.requestURL, self.requestData)
                # print('提交网址：', self.submitURL)
                # print('提交数据：', self.submitData)

                # 再次或重试请求间隔
                retryInterval = random.randint(5, 10)
                if makeRes:
                    # 随机延迟15-30秒
                    interval = random.randint(20, 30)
                    logger.info('休眠 %d 秒后提交数据', interval)
                    time.sleep(interval)
                    while True:
                        try:
                            submitRes = self.webpage_visit(self.submitURL, self.submitData)
                            break
                        except Exception as e:
                            logger.error('提交数据发生异常,异常信息【%s】稍后重试..', str(e))
                        time.sleep(random.randint(1, 2))
                else:
                    logger.info('休眠 %d 秒后尝试重试', retryInterval)
                    time.sleep(retryInterval)
                    continue

                if submitRes == '':
                    i += 1
                    if i >= retry:
                        logger.warn('当日任务已达上限')
                        break
                    else:
                        logger.error('当前提交数据返回【】，休眠 %d 秒后重试，已重试次数：%d', retryInterval, i)
                else:
                    self.income = self.income + 0.11
                    submitRes = json.loads(submitRes)
                    msg = repr(submitRes['msg'])  # repr() 函数可以将字符串转换为python的原始字符串（即忽视各种特殊字符的作用）
                    msg = msg.replace('\\n', '').replace('\\', ' ')  # 多次字符串替换
                    logger.info('第：%d 条数据 第：%d 次提交成功,返回信息: %s 今日累计收益：%.3f', m, n, msg, self.income)
                    logger.info('休眠 %d 秒后继续任务', retryInterval)
                time.sleep(retryInterval)
        # 跑完后把累计收益推送到微信
        while True:
            try:
                self.send_wechat('今日任务完成，共 ' + str(m) + ' 条数据，累计收益: ' + str(format(self.income, '.3f')))
                break
            except Exception as e:
                logger.error('推送到微信发生异常,异常信息【%s】稍后重试..', str(e))
            time.sleep(random.randint(2, 5))

    def ConsReqParameters(self, url, data):
        """
        构造提交所用的网址和数据
        :param url: 原请求网址，从文件所获取
        :param data: 原请求数据，从文件所获取
        :return: 构造成功True，失败False
        """
        # logger.info('构造提交所用的网址和数据..')

        # 构造提交网址
        # str1 = "Hello.python";
        # str2 = ".";
        # print str1.index(str2);  # 结果5
        # print str1[:str1.index(str2)]  # 获取 "."之前的字符(不包含点)  结果 Hello
        # print str1[str1.index(str2):];  # 获取 "."之前的字符(包含点) 结果.python
        urlTmp = url[:url.index('sign')]
        # print('urlTmp:', urlTmp)
        url = urlTmp + 'sign=' + self.md5()
        # print('url:', url)
        # https://x.zhichi921.com/app/index.php?i=8&t=0&v=1.0.2&from=wxapp&c=entry&a=wxapp&do=doujin_addtemp&&sign=26183073f9cc2ac03a32275e47c63094
        # https://x.zhichi921.com/app/index.php?i=8&t=0&v=1.0.2&from=wxapp&c=entry&a=wxapp&do=doujin_kanwanad&&sign=b80be4affe90aa5fd5afc199690f68a8
        self.submitURL = url.replace('doujin_addtemp', 'doujin_kanwanad')
        # print('submitURL', self.submitURL)
        # logger.info('提交网址构造成功：' + self.submitURL)
        # logger.info('提交网址构造成功')
        # 构造提交数据
        # m=shenqi_pingce&xopenid=od9LS5BrJ54EE8HIEjHUG-PDoRUI&gucid=0&fid=318&appname=Weixin&now_title=%E6%BD%9C%E6%84%8F%E8%AF%86%E9%87%8C%E4%BD%A0%E6%98%AF%E5%93%AA%E7%A7%8D%E7%A5%9E%E8%AF%9D%E5%8A%A8%E7%89%A9%EF%BC%9F
        # m=shenqi_pingce&xopenid=od9LS5BrJ54EE8HIEjHUG-PDoRUI&gucid=0&adid=随机ID&randnum=随机数
        # m=shenqi_pingce&xopenid=od9LS5BrJ54EE8HIEjHUG-PDoRUI&gucid=0&adid=173614&randnum=40355
        # m=shenqi_pingce&xopenid=oxh0i5f9yapwAfMFNVhhs5tDUJ4s&gucid=&fid=318&id=385&f_from=513&appname=Weixin&now_title=%20%E5%9C%A8%E7%B9%81%E5%8D%8E%E9%87%8C%E8%87%AA%E5%BE%8B%EF%BC%8C%E5%9C%A8%E8%90%BD%E9%AD%84%E9%87%8C%E8%87%AA%E5%8A%B1
        # m=shenqi_pingce&xopenid=oxh0i5f9yapwAfMFNVhhs5tDUJ4s&gucid=&id=385&f_from=513&adid=随机ID&randnum=随机数
        # m=shenqi_pingce&xopenid=oxh0i5bDqVbe8Do74muQ-0lXeY0U&gucid=&id=385&f_from=513&adid=173636&randnum=56630

        if data.find('gucid=&') > -1:
            # 从 data 中截取appname=Weixin 左边的字符
            dataTmp = data[:data.index('appname=Weixin')]
            # print('dataTmp0', dataTmp)
            # 获取中间字符串 fid=318 并把它替换成空字符''
            fid = self.GetMiddleStr(dataTmp, '&gucid=', '&id=')
            dataTmp = dataTmp.replace(fid, '')  # 把dataTmp 中的fid=xxx替换成空字符
            # print('dataTmp1', dataTmp)
        elif data.find('gucid=0&') > -1:
            dataTmp = data[:data.index('fid=')]
            # print('dataTmp2', dataTmp)
        else:
            logger.info('构造提交参数失败，请检查数据或试一试修改了返回值')
            return False
        # 提交数据构造完成
        self.submitData = dataTmp + 'adid=' + str(self.adid) + '&randnum=' + str(self.randnum)
        # print('submitData', self.submitData)
        # logger.info('提交数据构造成功：' + self.submitData)
        # logger.info('提交数据构造成功')
        return True

    def get_data_file(self):
        """
        从文件读取账号数据
        :return:返回文件数据
        """
        # logger.info('读取账号数据..')
        try:
            with  open('data.txt', 'r', encoding='UTF-8') as f:
                data_file = f.readlines()
                # print(data_file)
                f.close()
            return data_file
        except Exception as e:
            # raise SKException('读取账号数据失败')
            logger.error('读取账号数据发生异常,异常信息【%s】', str(e))
            exit()

    def webpage_visit(self, url, data):
        """
        post 网页访问
        :param url: 网址
        :param data: post 数据
        :return: true/false
        """

        conn = http.client.HTTPSConnection("x.zhichi921.com")
        payload = data
        headers = {
            'Host': 'x.zhichi921.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'Accept': ' */*',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.12(0x17000c21) NetType/WIFI Language/zh_CN',
            'Referer': 'https://servicewechat.com/wx43c05964dae7ad89/4/page-frame.html',
            'Content-Length': len(payload),
            'Accept-Language': 'zh-cn'
        }

        while True:
            try:
                conn.request("POST", url, payload, headers)
                res = conn.getresponse()
                data = res.read()
                return data.decode("utf-8")
            except Exception as e:
                # raise SKException('网络访问失败，正在重试..')
                logger.error('网络访问发生异常,异常信息【%s】，正在重试..', str(e))
                time.sleep(random.randint(1, 3))

    def md5(self):
        """
        从指定字符中取出一定数量的字符MD5加密成32位
        :return: 返回MD5加密后的32位字符
        """
        # 先从多个字符中选取指定数量的字符组成新字符串
        data = ''.join(random.sample(
            ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', 'f',
             'e', 'd', 'c', 'b', 'a'], 10))
        # print(data)
        # data = random.randrange(0, 101, 1)
        # 得到md5算法对象
        hash_md5 = hashlib.md5()
        # 准备要计算md5的数据（bytes类型）
        data = data.encode('utf-8', errors='ignore')
        # 计算
        hash_md5.update(data)
        # 获取计算结果(16进制字符串，32位字符)
        md5_str = hash_md5.hexdigest()
        # 打印结果
        # print(md5_str)
        return md5_str

    def GetMiddleStr(self, content, startStr, endStr):
        """
        根据开头和结尾字符串获取中间字符串的方法
        :param content:原字符串
        :param startStr:开始字符串
        :param endStr:结尾字符串
        :return: 提取出来的字符串
        """
        # content：<div class="a">提取的字符串</div>
        # startStr：<div class="a">
        # endStr：</div>
        # 返回结果：提取的字符串
        startIndex = content.index(startStr)
        if startIndex >= 0:
            startIndex += len(startStr)
        endIndex = content.index(endStr)
        return content[startIndex:endIndex]

    def send_wechat(self, message):
        """
        推送信息到微信
        :param message: 要推送的信息
        :return:
        """
        url = 'http://sc.ftqq.com/{}.send'.format('SCT3556TCbQX4pSjlpwLT7Oi1SUs91cG')
        payload = {
            "text": '今日收益',
            "desp": message
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, '
                          'like Gecko) Mobile/15E148 MicroMessenger/7.0.12(0x17000c21) NetType/WIFI Language/zh_CN '
        }
        requests.get(url, params=payload, headers=headers)
        logger.info('今日数据信息已推送至微信')





    def get_xopenid(self):
        results = []
        for i in range(100):
            result = random.sample(string.ascii_letters, 28)
            results.append("".join(result))

        for i in results:
            print(i)


class SKException(Exception):

    def __init__(self, message):
        super().__init__(message)

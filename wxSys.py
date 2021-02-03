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
import threading
import time
from concurrent.futures.process import ProcessPoolExecutor

import requests
from soupsieve.util import deprecated
from config import global_config
from logger import logger

income = 0.0  # 累计金额
submitNum = 0  # 累计提交
nullNum = 0  # 累计无效提交

class brushAds(object):
    def __init__(self):

        filePath = 'data/'
        self.oldDataPath = filePath + global_config.get('config', 'oldFileName')  # 原数据文件目标
        self.newDataPath = filePath + global_config.get('config', 'newFileName')  # 新数据文件目标
        self.thread_num = int(global_config.get('config', 'threadNum'))  # 要启动的线程数量
        self.outputNum = int(global_config.get('config', 'outputNum'))  # 要生成新数据的数量
        self.sub_num = int(global_config.get('config', 'sub_num'))  # 提交上限次数
        self.retry = int(global_config.get('config', 'retry'))  # 提交重试次数

        self.headers = ''
        self.requestURL = ""  # 请求网址
        self.requestData = ""  # 请求数据
        self.submitURL = ""  # 提交网址
        self.submitData = ""  # 提交数据
        self.randnum = ""  # 提交数据中用到的参数randnum
        self.adid = ""  # 提交数据中用到的参数adid

    def _get_random_useragent(self):
        """生成随机的User-Agent

        :return: User-Agent字符串
        """
        return random.choice(USER_AGENTS)

    def start_Thread(self):
        """
        启动多线程任务

        :return: 无
        """
        p = Partition(self.newDataPath, self.thread_num)
        t = []
        pos = p.part()
        # 生成线程
        for i in range(self.thread_num):
            t.append(Reader(self.newDataPath, *pos[i]))
        # 开启线程
        for i in range(self.thread_num):
            t[i].start()
        for i in range(self.thread_num):
            t[i].join()

    def missionStart(self, line, threadId):
        """
        立即开始任务

        :param line: 网址和post数据
        :param threadId: 线程ID
        :return:
        """
        self._missionStart(line, threadId)

    @deprecated
    def start_by_proc_pool(self, work_count=5):
        """
        多进程进行抢购
        work_count：进程数量
        """
        with ProcessPoolExecutor(work_count) as pool:
            for i in range(work_count):
                pool.submit(self.missionStart)
                time.sleep(1)

    def randomData(self):
        """
        从原数据中读取文件并随机组合成指定数量新的列表并替换其中的xopenid
        再写入到新的文件中

        :return: 无
        """
        file_list = self._get_data_file()  # 读取原数据文件
        # logger.debug('原始数据列表：%s', file_list)
        new_file_list = []
        # 循环随机从原文件中取一行生成新列表 执行outputNum次
        for i in range(self.outputNum):
            while True:
                try:
                    # 从原始数据中随机取出一条数据加入到新的列表中
                    ran = random.randint(0, len(file_list) - 1)
                    # logger.debug('随机取一条：%s', file_list[ran])
                    new_file_list.append(file_list[ran])
                    break
                except Exception as e:
                    logger.exception('生成新列表数据发生异常,异常信息【%s】稍后重试..', str(e))

        self._newData(new_file_list)  # 替换xopenid并写入文件

    def _newData(self, new_file_list):
        """
        随机生成新xopenid并替换原来的值，
        并于生成新的请求数据，
        并写入newData.txt文件

        :param new_file_list: 要生成的原数据列表 网址----数据 组合
        :return:无
        """
        new_list = []  # 存放新生成的数据
        for old_list in new_file_list:
            oldXopenid = self._GetMiddleStr(old_list, '&xopenid=', '&gucid=')  # 提取出旧xopenid值
            newXopenid = self._get_xopenid()
            dataTmp = old_list.replace(oldXopenid, newXopenid)  # 替换xopenid的值
            new_list.append(dataTmp)
            # logger.debug('替换xopenid后的：%s', new_list)

        # 把替换后的数据列表写入文件 'self.newDataPath'
        self._writeToFile(self.newDataPath, new_list)

    def _writeToFile(self, filename, data_list):  # filename为写入CSV文件的路径，data为要写入数据列表.
        """
        把数据列表写入文件

        :param data_list: 要写入的数据列表
        :return: 无
        """
        file = open(filename, 'w', encoding='UTF-8')
        n = 0
        for new_data in data_list:
            # s = str(data_list[i]).replace('[', '').replace(']', '')  # 去除[],这两行按数据不同，可以选择
            # s = s.replace("'", '').replace(',', '') + '\n'  # 去除单引号，逗号，每行末尾追加换行符
            file.write(new_data)
            n += 1
        file.close()
        logger.warning('%d 条数据保存成功', n)

    def _missionStart(self, line, threadId):
        """
        执行具体任务

        :param line: 网址和post数据
        :param threadId: 线程ID
        :return: 无
        """
        global income, submitNum, nullNum
        # 从数据中分割出请求的网址和请求的post数据
        reqData = line.split("----")
        self.requestURL = reqData[0]  # 请求网址
        self.requestData = reqData[1].replace('\\n', '')  # 请求数据
        self.headers = self._get_random_useragent()  # 生成随机的User Agent
        logger.debug(self.headers)

        n = 0  # 提交次数计数
        i = 0  # 提交返回空计数(任务上限后返回空)

        while n < self.sub_num:
            n += 1
            retryInterval = random.randint(10, 15)  # 再次或重试请求间隔
            logger.debug('线程ID：%d 第：%d 次请求', threadId, n)
            # 请求广告接口，返回提交所需要的参数uid,randnum
            resp = ''
            try:
                resp = self._webpage_visit(self.requestURL, self.requestData)
                if resp.find('uid') == -1 and resp.find('randnum') == -1:
                    resp = ''
            except Exception as e:
                logger.exception('请求数据发生异常,异常信息【%s】稍后重试..', str(e))

            if resp == '':
                logger.error("获取提交所需参数失败，返回信息：【】")
                # break 语句可以跳出 for 和 while 的循环体。如果你从 for 或 while 循环中终止，任何对应的循环 else 块将不执行。
                # continue 语句被用来告诉 Python 跳过当前循环块中的剩余语句，然后继续进行下一轮循环。
                time.sleep(retryInterval)
                continue
            # {"code":1,"uid":"199970","randnum":63283,"fanqian_arr":1}
            logger.debug("获取提交所需参数成功，返回信息：" + resp)
            # 将返回的json 数据 resp 转换成表
            s = json.loads(resp)
            # 提取提交所需要的adid和randnum
            self.randnum = s['randnum']
            self.adid = s['uid']
            # 构造提交所需要的网址和post数据 成功True,失败False
            makeRes = self._ConsReqParameters(self.requestURL, self.requestData)
            submitRes = ''
            if makeRes:
                # 随机延迟15-30秒
                interval = random.randint(32, 55)
                logger.info('休眠 %d 秒后提交数据', interval)
                time.sleep(interval)

                try:
                    submitRes = self._webpage_visit(self.submitURL, self.submitData)
                except Exception as e:
                    logger.error('提交数据发生异常,异常信息【%s】稍后重试..', str(e))

            else:
                logger.info('休眠 %d 秒后尝试重试', retryInterval)
                time.sleep(retryInterval)
                continue

            if submitRes == '':
                i += 1
                if i >= self.retry:
                    logger.warning('此线程今日任务已达上限')
                    break
                else:
                    logger.error('当前提交数据返回【】，休眠 %d 秒后重试，已重试次数：%d', retryInterval, i)
            else:
                submitNum += 1
                submitRes = json.loads(submitRes)
                msg = repr(submitRes['msg'])  # repr() 函数可以将字符串转换为python的原始字符串（即忽视各种特殊字符的作用）
                msg = msg.replace('\\n', '').replace('\\', ' ').replace(' ', '').replace('\'', '')  # 多次字符串替换
                if msg.find('入账') > -1:
                    income += 0.11
                    addMoney = '有效'
                    msg = msg[:38] + '.. ..[' + msg[-9:-1]+']'
                else:
                    nullNum += 1
                    addMoney = '无效'
                    msg = msg
                logger.warning('第：%d 次提交 %s 累计提交：%d 无效：%d 累计收益：%.3f 返回:%s', n, addMoney, submitNum, nullNum, income, msg)
                logger.info('休眠 %d 秒后继续', retryInterval)
            time.sleep(retryInterval)

    def _ConsReqParameters(self, reqURL, reqData):
        """
        构造提交所用的网址和数据

        :param reqURL: 原请求网址，从文件所获取
        :param reqData: 原请求数据，从文件所获取
        :return: 构造成功True，失败False
        """
        logger.info('构造提交所用的网址和数据..')
        # 构造提交网址
        # str1 = "Hello.python";
        # str2 = ".";
        # print str1.index(str2);  # 结果5
        # print str1[:str1.index(str2)]  # 获取 "."之前的字符(不包含点)  结果 Hello
        # print str1[str1.index(str2):];  # 获取 "."之前的字符(包含点) 结果.python
        # https://x.zhichi921.com/app/index.php?i=8&t=0&v=1.0.2&from=wxapp&c=entry&a=wxapp&do=doujin_addtemp&&sign=26183073f9cc2ac03a32275e47c63094
        # https://x.zhichi921.com/app/index.php?i=8&t=0&v=1.0.2&from=wxapp&c=entry&a=wxapp&do=doujin_kanwanad&&sign=b80be4affe90aa5fd5afc199690f68a8
        self.submitURL = reqURL.replace('doujin_addtemp', 'doujin_kanwanad')  # 字符串替换
        # 构造提交数据
        # m=shenqi_pingce&xopenid=od9LS5BrJ54EE8HIEjHUG-PDoRUI&gucid=0&fid=318&appname=Weixin&now_title=%E6%BD%9C%E6%84%8F%E8%AF%86%E9%87%8C%E4%BD%A0%E6%98%AF%E5%93%AA%E7%A7%8D%E7%A5%9E%E8%AF%9D%E5%8A%A8%E7%89%A9%EF%BC%9F
        # m=shenqi_pingce&xopenid=od9LS5BrJ54EE8HIEjHUG-PDoRUI&gucid=0&adid=随机ID&randnum=随机数
        # m=shenqi_pingce&xopenid=od9LS5BrJ54EE8HIEjHUG-PDoRUI&gucid=0&adid=173614&randnum=40355
        # m=shenqi_pingce&xopenid=oxh0i5f9yapwAfMFNVhhs5tDUJ4s&gucid=&fid=318&id=385&f_from=513&appname=Weixin&now_title=%20%E5%9C%A8%E7%B9%81%E5%8D%8E%E9%87%8C%E8%87%AA%E5%BE%8B%EF%BC%8C%E5%9C%A8%E8%90%BD%E9%AD%84%E9%87%8C%E8%87%AA%E5%8A%B1
        # m=shenqi_pingce&xopenid=oxh0i5f9yapwAfMFNVhhs5tDUJ4s&gucid=&id=385&f_from=513&adid=随机ID&randnum=随机数
        # m=shenqi_pingce&xopenid=oxh0i5bDqVbe8Do74muQ-0lXeY0U&gucid=&id=385&f_from=513&adid=173636&randnum=56630

        if reqData.find('gucid=&') > -1:
            # 从 reqData 中截取appname=Weixin 左边的字符
            dataTmp = reqData[:reqData.index('appname=Weixin')]
            # 获取中间字符串 fid=318 并把它替换成空字符''
            fid = self._GetMiddleStr(dataTmp, '&gucid=', '&id=')
            dataTmp = dataTmp.replace(fid, '')  # 把dataTmp 中的fid=xxx替换成空字符
        elif reqData.find('gucid=0&') > -1:
            dataTmp = reqData[:reqData.index('fid=')]
        else:
            logger.error('构造提交参数失败，请检查数据或试一试修改了返回值')
            return False
        # 提交数据构造完成
        self.submitData = dataTmp + 'adid=' + str(self.adid) + '&randnum=' + str(self.randnum)
        logger.info('成功构造提交所用的网址和数据..')
        return True

    def _get_data_file(self):
        """
        从文件读取账号数据
        :return:返回文件数据
        """
        logger.debug('读取账号数据..')
        try:
            with open(self.oldDataPath, 'r', encoding='UTF-8') as f:
                data_file = f.readlines()
                f.close()
            return data_file
        except Exception as e:
            # raise SKException('读取账号数据失败')
            logger.exception('读取账号数据发生异常,异常信息【%s】', str(e))
            exit()

    def _webpage_visit(self, url, data):
        """
        post 网页访问

        :param url: 网址
        :param data: post 数据
        :return: 成功返回返回值，失败返回空
        """

        conn = http.client.HTTPSConnection("x.zhichi921.com")
        payload = data
        headers = {
            'Host': 'x.zhichi921.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'Accept': ' */*',
            'User-Agent': self.headers,
            'Referer': 'https://servicewechat.com/wx43c05964dae7ad89/4/page-frame.html',
            'Content-Length': len(payload),
            'Accept-Language': 'zh-cn'
        }

        urlTmp = url[:url.index('sign')]  # 获取 "sign"之前的字符(不包含sign)
        url = urlTmp + 'sign=' + self._md5()  # 变换sign的值

        try:
            conn.request("POST", url, payload, headers)
            resp = conn.getresponse()
            data = resp.read()
            return data.decode("utf-8")
        except Exception as e:
            logger.exception('网络访问发生异常,异常信息【%s】', str(e))
            return ''

    def _md5(self):
        """
        从指定字符中取出一定数量的字符MD5加密成32位

        :return: 返回MD5加密后的32位字符
        """
        # 先从多个字符中选取指定数量的字符组成新字符串
        data = ''.join(random.sample(
            ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', 'f',
             'e', 'd', 'c', 'b', 'a'], 10))
        # reqData = random.randrange(0, 101, 1)
        # 得到md5算法对象
        hash_md5 = hashlib.md5()
        # 准备要计算md5的数据（bytes类型）
        data = data.encode('utf-8', errors='ignore')
        # 计算
        hash_md5.update(data)
        # 获取计算结果(16进制字符串，32位字符)
        md5_str = hash_md5.hexdigest()
        # 打印结果
        # logger.debug('md5_str: %s', md5_str)
        return md5_str

    def _GetMiddleStr(self, content, startStr, endStr):
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

    def send_wechat(self, start_time):
        """
        推送信息到微信

        :param start_time: 程序开始执行时间
        :return: 无
        """

        url = 'http://sc.ftqq.com/{}.send'.format('SCT3556TCbQX4pSjlpwLT7Oi1SUs91cG')

        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        end_time = time.time()  # 结束时间
        timeCost = str(format(((end_time - start_time) / 60), '.3f'))
        message = time_now + ' 任务完成 耗时: ' + timeCost + ' 分钟 累计执行: ' + str(submitNum) + '无效：' + str(nullNum) + ' 次 累计返回: ' + str(
            format(income, '.3f'))

        payload = {
            "text": time_now + ' 统计信息',
            "desp": message
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, '
                          'like Gecko) Mobile/15E148 MicroMessenger/7.0.12(0x17000c21) NetType/WIFI Language/zh_CN '
        }

        while True:
            try:
                requests.get(url, params=payload, headers=headers)
                logger.warning(message + ' 已推送至微信')
                break
            except Exception as e:
                logger.exception('推送至微信发生异常,异常信息【%s】稍后重试..', str(e))
            time.sleep(random.randint(30, 60))

    def _get_xopenid(self):
        """
        生成 xopenid
        :return: 返回新 xopenid
        """
        results = []
        for i in range(1):
            result = random.sample(string.ascii_letters, 28)
            results.append("".join(result))
        for i in results:
            # logger.debug("生成新xopenid: %s", i)
            return i


class SKException(Exception):

    def __init__(self, message):
        super().__init__(message)


class Reader(threading.Thread):
    """
    Reader类，继承threading.Thread
    @__init__方法初始化
    @run方法实现了读文件的操作
    """

    def __init__(self, file_name, start_pos, end_pos):
        super(Reader, self).__init__()
        self.file_name = file_name  # 文件名
        self.start_pos = start_pos  # 文件起始位置
        self.end_pos = end_pos  # 文件结束位置

    def run(self):
        fd = open(self.file_name, 'r', encoding='UTF-8')
        '''
        该if块主要判断分块后的文件块的首位置是不是行首，
        是行首的话，不做处理
        否则，将文件块的首位置定位到下一行的行首
        '''
        if self.start_pos != 0:
            fd.seek(self.start_pos - 1)
            if fd.read(1) != '\n':
                fd.readline()
                self.start_pos = fd.tell()
        fd.seek(self.start_pos)
        '''
        对该文件块进行处理
        '''
        while self.start_pos <= self.end_pos:
            line = fd.readline()
            '''
            do somthing
            '''
            t = threading.currentThread()
            threadId = t.ident
            brushAds().missionStart(line, threadId)  # 把读取到的文件行分配给开始任务
            self.start_pos = fd.tell()


class Partition(object):
    """
    对文件进行分块，文件块的数量和线程数量一致
    """

    def __init__(self, file_name, thread_num):
        self.file_name = file_name
        self.block_num = thread_num

    def part(self):
        fd = open(self.file_name, 'r')
        fd.seek(0, 2)
        pos_list = []
        file_size = fd.tell()
        block_size = file_size / self.block_num
        start_pos = 0
        for i in range(self.block_num):
            if i == self.block_num - 1:
                end_pos = file_size - 1
                pos_list.append((start_pos, end_pos))
                break
            end_pos = start_pos + block_size - 1
            if end_pos >= file_size:
                end_pos = file_size - 1
            if start_pos >= file_size:
                break
            pos_list.append((start_pos, end_pos))
            start_pos = end_pos + 1
        fd.close()
        return pos_list


USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 8.0; ONEPLUS A3000 Build/OPR1.170623.032; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.143 Crosswalk/24.53.595.0 XWEB/155 MMWEBSDK/21 Mobile Safari/537.36 MicroMessenger/6.6.7.1321(0x26060739) NetType/WIFI Language/zh_CN MicroMessenger/6.6.7.1321(0x26060739) NetType/4G Language/zh_CN miniProgram",
    "Mozilla/5.0 (Linux; Android 7.1.1; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN miniProgram",
    "Mozilla/5.0 (Linux; Android 7.1.1; OD103 Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN miniProgram",
    "Mozilla/5.0 (Linux; Android 7.0; Mi-4c Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN miniProgram",
    "Mozilla/5.0 (Linux; Android 6.0.1; MI 4LTE Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2692 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/427 MicroMessenger/7.0.19.1760(0x27001334) Process/appbrand3 WeChat/arm32 NetType/4G Language/zh_CN ABI/arm32",
    "Mozilla/5.0 (Linux; Android 6.0.1; SM919 Build/MXB48T; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN",
    "Mozilla/5.0 (Linux; Android 5.1.1; vivo X6S A Build/LMY47V; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN",
    "Mozilla/5.0 (Linux; Android 5.1; HUAWEI TAG-AL00 Build/HUAWEITAG-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043622 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_1 like Mac OS X) AppleWebKit/604.4.7 (KHTML, like Gecko) Mobile/15C153 MicroMessenger/6.6.1 NetType/4G Language/zh_CN",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Mobile/14G60 MicroMessenger/6.6.1 NetType/4G Language/zh_CN",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13F69 MicroMessenger/6.6.1 NetType/4G Language/zh_CN",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_2 like Mac OS X) AppleWebKit/604.4.7 (KHTML, like Gecko) Mobile/15C202 MicroMessenger/6.6.1 NetType/4G Language/zh_CN",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_1_1 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) Mobile/15B150 MicroMessenger/6.6.1 NetType/4G Language/zh_CN",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.12(0x17000c21) NetType/4G Language/zh_CN"
]

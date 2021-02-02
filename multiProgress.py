#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021-1-31 18:57:16
# @Author  : 青稞
# @Site    : 多线程读取文件
# @File    : multiProgress.py

# import threading
#
# from wxSys import brushAds
#
#
# class Reader(threading.Thread):
#     """
#     Reader类，继承threading.Thread
#     @__init__方法初始化
#     @run方法实现了读文件的操作
#     """
#
#     def __init__(self, file_name, start_pos, end_pos):
#         super(Reader, self).__init__()
#         self.file_name = file_name  # 文件名
#         self.start_pos = start_pos  # 文件起始位置
#         self.end_pos = end_pos  # 文件结束位置
#         self.start_tool = brushAds()
#
#     def run(self):
#         fd = open(self.file_name, 'r', encoding='UTF-8')
#         '''
#         该if块主要判断分块后的文件块的首位置是不是行首，
#         是行首的话，不做处理
#         否则，将文件块的首位置定位到下一行的行首
#         '''
#         if self.start_pos != 0:
#             fd.seek(self.start_pos - 1)
#             if fd.read(1) != '\n':
#                 fd.readline()
#                 self.start_pos = fd.tell()
#         fd.seek(self.start_pos)
#         '''
#         对该文件块进行处理
#         '''
#         while self.start_pos <= self.end_pos:
#             line = fd.readline()
#             '''
#             do somthing
#             '''
#             t = threading.currentThread()
#             threadId = t.ident
#             self.start_tool.missionStart(line, threadId)  # 把读取到的文件行分配给开始任务
#             self.start_pos = fd.tell()
#
#
# class Partition(object):
#     """
#     对文件进行分块，文件块的数量和线程数量一致
#     """
#
#     def __init__(self, file_name, thread_num):
#         self.file_name = file_name
#         self.block_num = thread_num
#
#     def part(self):
#         fd = open(self.file_name, 'r')
#         fd.seek(0, 2)
#         pos_list = []
#         file_size = fd.tell()
#         block_size = file_size / self.block_num
#         start_pos = 0
#         for i in range(self.block_num):
#             if i == self.block_num - 1:
#                 end_pos = file_size - 1
#                 pos_list.append((start_pos, end_pos))
#                 break
#             end_pos = start_pos + block_size - 1
#             if end_pos >= file_size:
#                 end_pos = file_size - 1
#             if start_pos >= file_size:
#                 break
#             pos_list.append((start_pos, end_pos))
#             start_pos = end_pos + 1
#         fd.close()
#         return pos_list

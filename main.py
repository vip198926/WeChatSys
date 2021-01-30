# coding:utf8

# 视一视刷广告
# By 青稞
# 2021-01-29 15:55:10


# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。


from wxSys import brushAds

if __name__ == '__main__':
    start_tool = brushAds()
    # 开始任务
    # sub_num – 提交次数，默认20次
    # interval – 请求后与提交之间的间隔时间，默认30秒
    # retryInterval – 重试提交或第二次提交间隔时间，默认10秒
    # retry – 提交返回空后重试次数，默认3次
    start_tool.missionStart(sub_num=20, retry=3)

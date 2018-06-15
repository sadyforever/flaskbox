import functools

import datetime
import random

from flask import session, current_app, g

from info import db
from info.models import User, News


def do_index_class(index):
    """自定义过滤器，过滤点击排序html的class"""
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


# 每次都需要用到用户登录的信息,高度重复代码,放到g变量中使用
def user_login_data(f):
    # 使用 functools.wraps 去装饰内层函数，可以保持当前装饰器去装饰的函数的 __name__ 的值不变
    # 装饰器装饰函数func会把func的名字改成wrapper,但是flask中url_map的路由列表中函数名字是不能重复的
    # 这个装饰器装饰视图函数的谁,就把名字改了,所以在改动上提供flask中内置的functools.wraps还原成原名字
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id", None)
        user = None
        if user_id:
            # 尝试查询用户的模型
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        # 把查询出来的数据赋值给g变量
        g.user = user
        return f(*args, **kwargs)
    return wrapper






# def query_user_data():
#     user_id = session.get("user_id", None)
#     user = None
#     if user_id:
#         # 尝试查询用户的模型
#         try:
#             user = User.query.get(user_id)
#         except Exception as e:
#             current_app.logger.error(e)
#         return user
#     return None



# 点击排行工具函数
def clickrank():
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)

    # 定义一个空的字典列表，里面装的就是字典
    news_dict_li = []
    # 遍历对象列表，将对象的字典添加到字典列表中
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())
    return news_dict_li


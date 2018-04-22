from flask import render_template, current_app, session, flash

from info.models import User
from . import index_blu


@index_blu.route('/')
def index():

    # 用户访问主页,如果是已经登录的应该直接给出头像和用户名div,没登录才显示登录/注册,所以这个模块写在index中
    # 如果是登录过的用户,会在cookie中有我们给的user_id和(看我们给啥了)
    user_id = session.get('user_id',None)  # 取不到必须有空值,来保证是没登录的


    # 这个是关键,如果user查询失败说明没有这个用户,那么data中使用user.to_dict()就不合法了,因为没有user这个变量
    user = None     # 没有的话,报错:local variable 'user' referenced before assignment



    if user_id: # 如果能取到id,那就已经登录了
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)


    # print(user)   # <User 11>是个对象,所以需要to_dict方法变成字典
    # 从sql数据库查询到的是对象模型,把对象给到模板渲染 render_template
    data = {        # models中的to_dict方法,返回字典
        'user': user.to_dict() if user else None    # 这个相当于三元表达式,又像函数推导式: 用户存在则执行方法,不存在就是None,用三元的原因也是None不能使用to_dict方法,报错:NoneType' object has no attribute 'to_dict
    }
    # flash(data)使用消息闪现data是{ key : 对象模型  }  所以从sql数据库中查询出来的内容是对象模型,所以要遍历所以要用 什么.什么 的方法
    # data = {'user': {'id': 11, 'nick_name': '18811110000', 'avatar_url': '', 'mobile': '18811110000', 'gender': 'MAN', 'signature': '', 'followers_count': 0, 'news_count': 0}}
    return render_template('news/index.html',data=data)


@index_blu.route('/favicon.ico')
def favicon():
    # 浏览器请求主页的时候,默认最后会有个请求logo的请求,而这个请求要的是静态文件,并不是模板
    # 所以不能用render_template
    # send_static_file方法返回静态文件
    # 必须有current_app
    return current_app.send_static_file('news/favicon.ico')
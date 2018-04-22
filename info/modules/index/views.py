from flask import render_template, current_app, session, flash

from info.models import User, News
from . import index_blu


@index_blu.route('/')
def index():
    '''
    1.右上角头像显示
    2.点击排行显示
    :return:
    '''

    # 1.用户访问主页,如果是已经登录的应该直接给出头像和用户名div,没登录才显示登录/注册,所以这个模块写在index中
    # 如果是登录过的用户,会在cookie中有我们给的user_id和(看我们给啥了)
    user_id = session.get('user_id',None)  # 取不到必须有空值,来保证是没登录的


    # 这个是关键,如果user查询失败说明没有这个用户,那么data中使用user.to_dict()就不合法了,因为没有user这个变量
    user = None     # 没有的话,报错:local variable 'user' referenced before assignment



    if user_id: # 如果能取到id,那就已经登录了
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)






    # 2.右侧点击排行
    # 如果查询数据库有问题,那news_list变量在下边想要使用遍历,必须有有这个变量,定义空列表
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)

    # print(news_list)  # 这是个查询
    # print(type(news_list))  # <class 'flask_sqlalchemy.BaseQuery'>
    # 查询出来的news_list是对象列表,想想数据库是怎么保存的
    # [ { new 1的数据}, {new 2的数据}, {new 3的数据}]
    # 而你不能传个对象过去啊,虽然它是列表,但是是对象列表,遍历添加到新列表中

    # 定义一个空的字典列表，里面装的就是字典
    news_dict_li = []
    # 遍历对象列表，将对象的字典添加到字典列表中
    for news in news_list:
        # print(news)  # <News 1086>
        # print(type(news))  # <class 'info.models.News'>
        # if news_dict_li == []:
        #     print(news.to_basic_dict()) # {'id': 1086, 'title': '华尔街见闻早餐FM-Radio|2018年1月11日', 'source': '张舒', 'digest': '①标普纳指年内首跌，但银行股涨，媒体称中国或暂缓增持美债令美元美债跌②一周大逆转：瑞波币回吐60%涨幅转跌，以太币涨50%争夺数字货币龙头③伯克希尔任命两位新副主席，巴菲特称距确定“传位”人更进一步④巴菲特：数字货币将以悲剧告终，自己永远不会持有⑤加拿大预计美国将很快退出NAFTA⑥加拿大向WTO对美发起贸易诉讼，美方称只会利好中国⑦上海网信办：必须严厉打击微博热搜产业链⑧楼市新一轮“松绑”：青岛、天津可租房落户，广州加大落户支持。', 'create_time': '2018-01-11 07:01:17', 'index_image_url': 'https://wpimg.wallstcn.com/164cf47b-057c-41ad-b558-54c944054e49.png', 'clicks': 211}
        news_dict_li.append(news.to_basic_dict())
    # 虽然数据要求对了,但是样式还差前三个,使用自定义过滤器,在工具文件夹中新建common模块
    # 既然有自定义过滤器,需要注册进去 app















    # print(user)   # <User 11>是个对象,所以需要to_dict方法变成字典
    # 从sql数据库查询到的是对象模型,把对象给到模板渲染 render_template
    data = {        # models中的to_dict方法,返回字典
        'user': user.to_dict() if user else None,    # 这个相当于三元表达式,又像函数推导式: 用户存在则执行方法,不存在就是None,用三元的原因也是None不能使用to_dict方法,报错:NoneType' object has no attribute 'to_dict
        "news_dict_li": news_dict_li,
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
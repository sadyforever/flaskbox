from flask import render_template, g, current_app, abort, jsonify, request

from info import db
from info.models import News, Comment, CommentLike
from info.modules.news import news_blu
from info.utils.common import user_login_data, clickrank
from info.utils.response_code import RET

# 新闻详情页(默认加载的时候 整个页面的渲染)
@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    '''
    新闻详情
    :param news_id:
    :return:
    '''
    # 新闻详情页中,无论是点赞,还是收藏,还是评论,或者最原始的只是通过首页点到详情页,都要判断用户的登录状态
    # 所以这段代码重复利用太高,可以中上下文中的g变量,是个全局变量
    # 简单方法,可以把内容写进函数中,然后再相应模块调用
    # 但是flask框架使用装饰器比较普遍,g变量就是基于装饰器来使用的,相当于工具,放到工具文件夹中
    # 1.用户登录信息
    user = g.user

    # 2.右侧的新闻排行的逻辑(可以写到工具函数中,通过调用)
    # news_list = []
    # try:
    #     news_list = News.query.order_by(News.clicks.desc()).limit(6)
    # except Exception as e:
    #     current_app.logger.error(e)
    #
    # # 定义一个空的字典列表，里面装的就是字典
    # news_dict_li = []
    # # 遍历对象列表，将对象的字典添加到字典列表中
    # for news in news_list:
    #     news_dict_li.append(news.to_basic_dict())
    news_dict_li = clickrank()


    # 3.查询新闻数据
    news = None

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        # 报404错误，404错误统一显示页面后续再处理
        abort(404)

    # 更新新闻的点击次数
    news.clicks += 1




    # 4.是否是收藏　
    is_collected = False

    # if 用户已登录：
    #     判断用户是否收藏当前新闻，如果收藏：
    #         is_collected = True

    if user:
        # 判断用户是否收藏当前新闻，如果收藏：
        # collection_news 后面可以不用加all，因为sqlalchemy会在使用的时候去自动加载,因为lazy的缘故
        # print(user.collection_news)
        if news in user.collection_news:  # TODO  验证user.collection_news是什么类型 query类型,查询类型,而当真正调用的时候查询结果就是对象了
            # print(user.collection_news)
            is_collected = True
    # print(is_collected) # 我改了收藏表格,在这打印确实是True,但是前段样式还没做





    # 5.去查询评论数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_dict_li = []

    for comment in comments:
        comment_dict = comment.to_dict()
        comment_dict_li.append(comment_dict)


    data = {
        'user':user.to_dict() if user else None,
        'news_dict_li':news_dict_li,
        'news':news.to_dict(), # 一个新闻对象不是列表不遍历但需要处理
        'is_collected':is_collected,
        'comments':comment_dict_li
    }
    return render_template('news/detail.html',data=data)


# 收藏按钮
@news_blu.route('/news_collect', methods=["POST"])
@user_login_data
def collect_news():
    """
    收藏新闻
    1. 接受参数
    2. 判断参数
    3. 查询新闻，并判断新闻是否存在
    :return:
    """

    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 1. 接受参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 2. 判断参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 查询新闻，并判断新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 4. 收藏以及取消收藏
    if action == "cancel_collect":
        # 取消收藏
        if news in user.collection_news:
            user.collection_news.remove(news)
    else:
        # 收藏
        if news not in user.collection_news:
            # 添加到用户的新闻收藏列表
            user.collection_news.append(news)

    return jsonify(errno=RET.OK, errmsg="操作成功")



# 发表评论的表单 , 和回复已有评论逻辑相同,只不过多了一个参数 : 回复的是哪条评论 parent_id
@news_blu.route('/news_comment',methods=['POST'])
@user_login_data
def comment_news():
    """
    评论新闻或者回复某条新闻下指定的评论
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg="用户未登录")

    # 1. 取到请求参数
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    # 2. 判断参数
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")


    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询新闻，并判断新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 3. 初始化一个评论模型，并且赋值
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id

    # 添加到数据库
    # 为什么要自己去commit()?，因为在return的时候需要用到 comment 的 id
    # db.session.add(comment)

    '''
    报错: to_dict(self)     方法中需要使用self 看一下里边全是self
    "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
    AttributeError: 'NoneType' object has no attribute 'strftime'
    '''
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()


    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())




# 评论点赞
@news_blu.route('/comment_like',methods=['POST'])
@user_login_data
def comment_like():
    """
    评论点赞
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 1. 取到请求参数
    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([comment_id, news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment_id = int(comment_id)
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    if action == "add":
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                    CommentLike.comment_id == comment.id).first()
        # 如果没有点赞
        if not comment_like_model:
            # 点赞评论
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment.id
            db.session.add(comment_like_model)

    else:
        # 取消点赞评论
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment.id).first()
        # 如果能取到模型,说明已经点赞了,然后
        if comment_like_model:
            comment_like_model.delete()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")

    return jsonify(errno=RET.OK, errmsg="OK")


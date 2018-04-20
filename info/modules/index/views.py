from flask import render_template, current_app

from . import index_blu


@index_blu.route('/')
def index():
    return render_template('news/index.html')


@index_blu.route('/favicon.ico')
def favicon():
    # 浏览器请求主页的时候,默认最后会有个请求logo的请求,而这个请求要的是静态文件,并不是模板
    # 所以不能用render_template
    # send_static_file方法返回静态文件
    # 必须有current_app
    return current_app.send_static_file('news/favicon.ico')
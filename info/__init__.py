# 日志的import
import logging
from logging.handlers import RotatingFileHandler

# 初始化app和db的import
from flask import Flask
# ext表示扩展extend 只不过它用的 . 形式
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_session import Session
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis


# 共用的import
from config import config





# 初始化数据库
#  在Flask很多扩展里面都可以先初始化扩展的对象，然后再去调用 init_app 方法去初始化
db = SQLAlchemy() # type :


# https://www.cnblogs.com/xieqiankun/p/type_hints_in_python3.html
# redis_store变量在函数中不能被外部引用,所以定义全局变量 = None
redis_store = None  # type: StrictRedis
# 而在别的模块用的时候没有智能提示
# python3.6特有的变量注释方法,让python给出相关提示




def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 核心初始化函数,用于返回manager中的app对象,所有需要和app关联的初始化操作都在这里
def create_app(config_name):

    # 配置日志,传入所使用的环境,获取对应的日志等级,调用日志函数
    setup_log(config_name)


    # 1.创建app对象
    app = Flask(__name__)
    # 加载配置信息,最基本的格式并不需要加载所以没印象,从对象中加载
    # 传入环境名字,在config模块中的字典确定对应的哪个对象,确定所使用的配置
    app.config.from_object(config[config_name])

    # 2.通过app初始化 mysql数据库 对象db
    db.init_app(app)   # 看上边的注释

    # 初始化redis数据库储存对象
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)


    # 3.小点
    # 开启CSRF验证
    CSRFProtect(app)
    # 设置session保存指定位置,这个是flask中的session
    Session(app)


    from info.utils.common import do_index_class
    # 添加自定义过滤器                           过滤器名字
    app.add_template_filter(do_index_class, "index_class")



    # 使用请求钩子设置cookie
    @app.after_request
    def after_request(response):
        # 生成随机的csrf_token值,flask框架的csrf模块提供方法
        csrf_token = generate_csrf()
        response.set_cookie('csrf_token',csrf_token)
        return response






    # 注册蓝图
    # 主页
    from info.modules.index import index_blu  # 蓝图尽量保持哪用在哪引入
    app.register_blueprint(index_blu)
    # 注册
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    # 必须返回app 给到manager接收
    return app
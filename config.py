# 配置模块   把配置信息写到一个模块的好处 : 当需要改配置的时候只需要来着改,
#           其他的模块的书写格式是 引入模块  配置类.属性

import logging  # python自带模块 logging 设置日志等级
from redis import StrictRedis


# 只涉及到两种数据库 1.redis 2.mysql  需要配置信息
# 还有一个就是 什么环境 决定Debug和日志等级


class Config(object):
    """项目的配置"""

    # csrf和session都需要设置 , 系统内置带一个随机生成随机码的模块,需要看视频,不会也没太大关系
    SECRET_KEY = "iECgbYWReMNxkRprrzMo5KAQYnb2UeZ3bwvReTSt+VSESW0OB8zbglT+6rEcDW9X"

    # 为mysql数据库添加配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information27"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis的配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379




    # flask框架的session

    # Session保存配置
    SESSION_TYPE = "redis"
    # 开启session签名 , 更严格的加密
    SESSION_USE_SIGNER = True
    # 指定 Session 保存的 redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 设置需要过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2




    # 设置日志等级
    LOG_LEVEL = logging.DEBUG  # 日志等级记录DEBUG以上的,等级分类看讲义

# 不同环境使用的模式不同(Debug) 然后日志等级不同    继承然后重写
class DevelopmentConfig(Config):
    """开发环境下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境下的配置"""
    DEBUG = False
    LOG_LEVEL = logging.WARNING     # 日志等级只记录warning以上的


class TestingConfig(Config):
    """单元测试环境下的配置"""
    DEBUG = True
    TESTING = True

# 一个变量   通过传入确定是哪种环境  开发还是生产
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# app 和 db 是初始化得到的 (应用 和 数据库)
from info import create_app, db

# 使用函数创建app,传入参数是声明是 生成环境  还是 开发环境
app = create_app('development')

manager = Manager(app)

Migrate(app,db) # app和数据库db对象关联

manager.add_command('db',MigrateCommand)

if __name__ == '__main__':
    manager.run()  #  manager模块两个功能, 命令行传参Manager
                    # 执行迁移 migrate 和 MigrateCommand
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# app 和 db 是初始化得到的 (应用 和 数据库)    这个必须引入models创建迁移文件使用
from info import create_app, db, models

# 使用函数创建app,传入参数是声明是 生成环境  还是 开发环境
app = create_app('development')

manager = Manager(app)

Migrate(app,db) # app和数据库db对象关联

manager.add_command('db',MigrateCommand)

from info.models import User
@manager.option('-n', '-name', dest="name")
@manager.option('-p', '-password', dest="password")
def createsuperuser(name, password):

    if not all([name, password]):
        print("参数不足")

    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)

    print("添加成功")
if __name__ == '__main__':
    manager.run()  #  manager模块两个功能, 命令行传参Manager
                    # 执行迁移 migrate 和 MigrateCommand
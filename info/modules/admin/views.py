import time

from datetime import datetime,timedelta
from flask import request, current_app, session, render_template, g, redirect, url_for

from info import constants
from info.models import User
from info.modules.admin import admin_blu

# 后台登录逻辑
from info.utils.common import user_login_data


@admin_blu.route('/login', methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        # 去 session 中取指定的值
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        # 如果用户id存在，并且是管理员，那么直接跳转管理后台主页
        if user_id and is_admin:
            return redirect(url_for('admin.admin_index'))
        return render_template('admin/login.html')

    # 取到登录的参数
    username = request.form.get("username")
    password = request.form.get("password")
    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数不足")

    try:
        user = User.query.filter(User.mobile == username).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="数据查询失败")

    if not user:
        return render_template('admin/login.html', errmsg="用户不存在")

    if not user.check_password(password):
        return render_template('admin/login.html', errmsg="密码错误")

    if not user.is_admin:
        return render_template('admin/login.html', errmsg="用户权限错误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = True

    # url_for直接指向视图函数名
    return redirect(url_for('admin.admin_index'))

# 后台主页
@admin_blu.route('/index')
@user_login_data
def admin_index():
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())

# 后台用户统计表格数据,前端树状图没了,只剩数量了
@admin_blu.route('/user_count')
def user_count():
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 月新增数
    mon_count = 0
    t = time.localtime()
    begin_mon_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    # 将字符串转成datetime对象
    begin_mon_date = datetime.strptime(begin_mon_date_str, "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日新增数
    day_count = 0
    begin_day_date = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 拆线图数据

    active_time = []
    active_count = []

    # 取到今天的时间字符串
    today_date_str = ('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday))
    # 转成时间对象
    today_date = datetime.strptime(today_date_str, "%Y-%m-%d")

    for i in range(0, 31):
        # 取到某一天的0点0分
        begin_date = today_date - timedelta(days=i)
        # 取到下一天的0点0分
        end_date = today_date - timedelta(days=(i - 1))
        count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                  User.last_login < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime('%Y-%m-%d'))

    # User.query.filter(User.is_admin == False, User.last_login >= 今天0点0分, User.last_login < 今天24点).count()

    # 反转，让最近的一天显示在最后
    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }

    return render_template('admin/user_count.html', data=data)


# 用户列表
@admin_blu.route('/user_list')
def user_list():
    page = request.args.get("page", 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    users = []
    current_page = 1
    total_page = 1

    try:
        paginate = User.query.filter(User.is_admin == False).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 进行模型列表转字典列表
    user_dict_li = []
    for user in users:
        user_dict_li.append(user.to_admin_dict())

    data = {
        "users": user_dict_li,
        "total_page": total_page,
        "current_page": current_page,
    }

    return render_template('admin/user_list.html', data=data)
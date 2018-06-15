from datetime import datetime
import random
import re

from flask import request, abort, current_app, make_response, json, jsonify, session

from info import redis_store, constants, db
from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET
from . import passport_blu
from  info.utils.captcha.captcha import captcha


# 虽然看index的注册div中图片验证码那写好了,但是关键是后边的onclick
# 请求主页的时候不是一次返回所有数据的,浏览器发现有图片等内容,会向服务器再次发送请求,请求地址就是src,所以关键就是重写src
# 重写src放在onclick的函数中,因为看不清的时候用户点击也是会返回图片的
@passport_blu.route('/image_code')
def get_image_code():
    # 这个视图函数给用户提供验证码,需要模块pip install Pillow这个模块是产生验证码的模块需要用的
    # 验证码 : 不是我们自己写的用到别人写的模块,把它当做工具在框架结构中新建工具文件夹utils
    # 把captcha文件夹放进工具文件夹中,captcha模块是帮我们产生验证码的,可以点进去看看
    # 还有一个文件response_code,每个公司都有自己使用的状态码,也是一个小工具文件吧,用这个文件的变量来给出状态码  文件名.变量名=状态码

    '''
    生成图片验证码并返回
    1. 取到参数
    2. 判断参数是否有值
    3. 生成图片验证码
    4. 保存图片验证码文字内容到redis
    5. 返回验证码图片
    :return:
    '''

    # 1.取出参数
    # args : 取到url的 ? 后面的参数
    image_code_id = request.args.get('imageCodeId',None) # 默认为None不至于崩
    # 服务器在请求中获取数据的时候要不就try要不就有默认值,要不然服务器崩溃了

    # 2.判断参数有值
    if not image_code_id:
        return abort(403)

    # 3.生成图片验证码
    # captcha那个模块,生成的验证码由 名字  验证码文字内容  验证码图片和文字整体  三部分组成
    name , text,image = captcha.generate_captcha()

    # 4.保存 随机值 和 验证码文字内容 到 redis中
    try:                 # key: 随机码            value:验证码文字内容          第三个参数是过期时间ex: 用了之前的小变量模块constants,其实就是一个数
        redis_store.set('ImageCodeId_' + image_code_id, text,300) # constants.IMAGE_CODE_REDIS_EXPIRES
    except Exception as e:
        current_app.logger.error(e)   # 获取当前问题保存到log中
        abort(500)  # 服务器问题500

    # 5.返回验证码图片
    response = make_response(image)
    # 设置响应内容的格式,怕有的浏览器不识别
    response.headers['Content-Type'] = 'image/jpg'
    return response




# 手机验证码只能通过第三方平台来发送,第三方提供接口,根据指定要求把 电话号 验证码内容 发送给第三方
# 云通信内的接口文件只支持2.7版本,用印哥给的
# 第三方py文件放到lib文件夹内
@passport_blu.route('/sms_code',methods=['POST'])
def sms_code():
    '''
    1. 获取参数：手机号，验证码文字内容（校验），图片验证码的编号 (key)
    2. 校验参数(参数是否符合规则，判断是否有值)
    3. 用验证码编号redis中取出验证码文字
    4. 验证码校验，不一致，验证码输入错误
    5. 一致，生成短信验证码的内容(随机数据)
    6. 发送短信验证码
    7. 告知发送结果（倒计时）
    :return:
    '''


    # 手机号:知道发给谁      图片验证码:判断验证码正确与否        验证码随机码: 从redis中取出验证码文字内容的key
    # 发过来的数据是json格式,这是前端决定的,而且用了接口文档的形式,让你熟悉这种作业方式,见讲义
    # {'mobile':'18811111111' , 'image_code':'ABCD' , 'image_code_id':'addasdasdasdasdas'}
    # 1.获取参数        params 参数个数
    # 后端接收json格式 解码成字典
    # ? 后边的用args获取      post方式用data获取

    # params_dict = json.loads(request.data) 可以直接写成
    params_dict = request.json

    mobile = params_dict['mobile']
    image_code = params_dict['image_code']
    image_code_id = params_dict['image_code_id']

    # 2.校验参数(是否符合逻辑,是否为空)
    if not all([mobile,image_code,image_code_id]):
        # {"errno": "4100", "errmsg": "参数有误"}
        # 必须按照公司指定的状态码给出,并且前端要求给出json格式

        return jsonify(errno=RET.PARAMERR,errmsg='参数有误')

    if not re.match(r'1[35678]\d{9}',mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 3.用验证码的编号 从redis中取出验证吗文字内容
    # print(mobile + image_code + image_code_id)
    try:
        real_image_code = redis_store.get("ImageCodeId_" + image_code_id).decode()  # redis中取出的是byte类型
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    # print(real_image_code)
    # 因为设置了过期时间,所以这个取不到值要考虑到
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")


    # 4.校验   有个大小写区分的问题,这个需要单独考虑,如果用户都写的大写,我们也要支持
    # 所以都大写或都小写
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

    # 5.校验一致,用第三方py文件生成随机验证码
    # 变量第三方模块要用   %06d : 生成随机数  一共6位  位数不够用0在前边补充
    sms_code_str = '%06d' % random.randint(0,999999)
    current_app.logger.debug("短信验证码内容是：%s" % sms_code_str)
    # # 6.发送短信验证码
    # result = CCP().send_template_sms(mobile,[sms_code_str,60],'1')
    # if result != 0:
    #     # 代表发送不成功  看第三方模块 0 成功  -1 不成功
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")

    # 保存验证码到redis ,都是验证身份的凭证
    try:                            # 没设置过期时间
        redis_store.set('SMS_' + mobile, sms_code_str , 300 )
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")


    # 如果成功,告知结果
    return jsonify(errno=RET.OK, errmsg="发送成功")



@passport_blu.route('/register',methods=['POST'])
def register():
    '''
    1.获取参数(手机号, 短信验证码,密码)
    2.校验参数
    3.用mobile取到redis中的短信验证码并校验
    4.一致,初始化User对象,并赋值
    5.user添加到数据库
    6.返回结果
    :return:
    '''

    # 1.获取参数
    params_dict = request.json
    mobile = params_dict['mobile']
    smscode = params_dict['smscode']
    password = params_dict['password']

    # 2.校验参数
    if not all([mobile,smscode,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不能为空')
    # 校验手机号是否正确
    if not re.match('1[35678]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")




    # 判断手机号是否已存在
    # 查询数据库有问题,没实现
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    if  user:
        return jsonify(errno=RET.DATAEXIST,errmsg='用户已经存在')








    # 3.校验短信验证码
    try:
        real_sms_code = redis_store.get('SMS_'+mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据查询失败')
    if not real_sms_code:
        return jsonify(errno=RET.NODATA,errmsg='验证码已过期')

    if real_sms_code.decode() != smscode:
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")


    # 4.一致,初始化User对象,并且赋值
    user = User()
    user.mobile = mobile
    # 用户昵称暂时没有 ,使用手机号代替
    user.nick_name = mobile
    # 记录用户最后一次登录的时间
    user.last_login = datetime.now()   # 注意这个的引入
    # TODO 对密码加密
    # 需求：在设置 password 的时候，去对 password 进行加密，并且将加密结果给 user.password_hash 赋值
    # 表中的密码是password_hash 而不是password,建议在数据库储存的是加密后的密码
    # 在这把用户输入的密码赋值给user.password,在User类中添加password方法,这样赋值就合理了
    # 而python高级中的@propery方法,可以把class中的一个函数当做属性来用
    # 其实核心是想要使用Werkzeug工具集中的密码 加密 和 验证 函数
    # 具体更改看models模块给class User 添加@propery方法
    user.password = password



    # 5.添加到数据库 ,没有智能提示为什么
    try:
        db.session.add(user)    # 因为有的字段唯一unquite,所以手机号重复到这也不能保存
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

    # 因为注册完直接跳转已经登录的页面,所以需要直接给到cookie
    # 所以直接往session中保存数据表示当前已经登录
    session['user_id'] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    # 7. 返回响应
    return jsonify(errno=RET.OK, errmsg="注册成功")





@passport_blu.route('/login',methods=['POST'])
def login():
    '''
    1.获取参数
    2.校验参数
    3.从sql中取出用户数据
    4.校验mobile和password
    5.登录成功返回session在cookie中
    :return:
    '''
    # 1.获取参数
    params_dict = request.json
    mobile = params_dict['mobile']
    password = params_dict['password']
    # 2.校验参数
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验手机号是否正确
    if not re.match('1[35678]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 3. 校验密码是否正确
    # 先查询出当前是否有指定手机号的用户
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    # 校验登录的密码和当前用户的密码是否一致
    # 使用user中的check_password函数来验证,其实为了使用Werkzeug工具集的check_password_hash
    # 帮我们取到password_hash的加密密码,和用户输入的明文密码校验
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或者密码错误")


    # 4.保存用户登录状态
    # session用于储存用户的敏感信息,这个是不能发给cookie的,如果没设置cookie那么发过去的就是session
    # 用户请求登录,账号和密码我们获取到了,储存了session还需要设置cookie
    # 而cookie设置在 app的初始化中 使用请求钩子 after.request 每次请求给出响应结果都执行
    # 这样cookie中设置了csrf,csrf其实是每次的验证在涉及到身份信息的时候
    session['user_id'] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    # 设置当前用户最后一次登录的时间
    user.last_login = datetime.now()
    # try:
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)
    # 如果在视图函数中，对模型身上的属性有修改，那么需要commit到数据库保存
    # 但是其实可以不用自己去写 db.session.commit(),前提是对SQLAlchemy有过相关配置
    # 其实unique也可以改变值,只不过是在当前字段内唯一而已
    # SQLALCHEMY_COMMIT_ON_TEARDOWN = True 这个配置就不需要我们手动commit了,只要有更改自动提交

    # 5. 响应
    print('&')
    return jsonify(errno=RET.OK, errmsg="登录成功")

    # TODO CSRF设置



@passport_blu.route("/logout", methods=['POST','GET'])
def logout():
    """
    清除session中的对应登录之后保存的信息
    :return:
    """
    # pop方法,必须有None虽然正常逻辑没事肯定能删除,但是这是防测试的,严谨一些
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)
    session.pop('is_admin', None)
    # 返回结果
    return jsonify(errno=RET.OK, errmsg="OK")

'''
前端逻辑:
function logout() {
    $.get('/passport/logout', function (resp) {
        location.reload()
    })
}

'''


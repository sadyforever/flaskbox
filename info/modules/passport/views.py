from flask import request, abort, current_app, make_response

from info import redis_store, constants
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
        redis_store.set('imageCodeId_' + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)   # 获取当前问题保存到log中
        abort(500)  # 服务器问题500

    # 5.返回验证码图片
    response = make_response(image)
    # 设置响应内容的格式,怕有的浏览器不识别
    response.headers['Content-Type'] = 'image/jpg'
    return response


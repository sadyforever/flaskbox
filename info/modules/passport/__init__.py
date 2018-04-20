from flask import Blueprint
                                            # 地址的前缀 取决于前端给你传过来的地址
passport_blu = Blueprint('passport',__name__,url_prefix='/passport')
                                            # 因为前端传过来的都是在 /passport 的基础上然后 /什么的,所以在这填入前缀,views视图路由位置就写的少了
from . import views
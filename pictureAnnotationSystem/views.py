import json
import os
import time
from PIL import Image

from django.http import HttpResponse
from django.shortcuts import render


# 显示首页
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from pictureAnnotation import settings


def showIndex(request):
    return render(request, 'index.html')

# 显示测试页面
def showTest(request):
    return render(request, 'test.html')

# 文件上传
@csrf_exempt
def file_upload(request):
    response = HttpResponse()

    # 获取前端传输的文件对象
    file_obj = request.FILES.get('file')
    # 获取文件类型
    img_type = file_obj.name.split('.')[1]
    # 将文件类型中的数据大写全部转换成小写
    img_type = img_type.lower()
    if img_type in ['png', 'jpg', 'jpeg', 'gif']:
        # 将图片存到指定目录
        # 获取当前时间的时间戳
        timestr = str(time.time()).replace('.', '')
        # 获取程序需要写入的文件路径
        path = os.path.join(settings.BASE_DIR, 'static/images/{0}_{1}'.format(timestr, file_obj.name))
        # 根据路径打开指定的文件(以二进制读写方式打开)
        f = open(path, 'wb+')
        # chunks将对应的文件数据转换成若干片段, 分段写入, 可以有效提高文件的写入速度, 适用于2.5M以上的文件
        for chunk in file_obj.chunks():
            f.write(chunk)
        f.close()
        # 读取图片获取宽高 并返回
        img = Image.open(path)
        #  print(img.size[0])
        msg = {'code': 200,
               'url': 'static/images/{0}_{1}'.format(timestr,file_obj.name),
               'width': img.size[0],
               'height': img.size[1],
               'error':' '}
    else:
        # 存储失败, 返回错误信息
        msg = {'code': 305, 'url': '', 'error': '暂不支持该类型'}

    respMsg = json.dumps(msg)
    # 如果不是Ajax的jsonp的异步请求就正常返回Json数组，如果是Ajax就要加jsonpCallback
    response.write(respMsg)
    return response


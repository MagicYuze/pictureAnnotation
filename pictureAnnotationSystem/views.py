import json
import os
import time
import random

import cv2
import numpy as np
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


# 分割图片
@csrf_exempt
def cut_pic(request):
    response = HttpResponse()
    try:
        if request.POST["url"] == '':
            msg = {'code': 402, 'msg': "请先选择一张图片再进行标注操作"}
            response.write(json.dumps(msg))
            return response
        old_url = request.POST["url"].split('/', 1)[1]
        print(old_url)
        points = request.POST["points"]
        # print(points)
        text = request.POST["ctext"]
        # print(text)
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response

    # 生成图片
    src = cv2.imdecode(np.fromfile(settings.STATICFILES_DIRS[0] + '/' + old_url, dtype=np.uint8), -1)
    width = src.shape[1]
    height = src.shape[0]
    # print(width, height)
    # 加载要截取的位置信息
    jsonStr = json.loads(points)
    # print(len(jsonStr))
    pointArray = []
    for onePoint in jsonStr:
        x = onePoint["x"] + width/2
        y = height/2 - onePoint["y"]
        if x < 0 or y < 0 or x > width or y > height:
            msg = {'code': 403, 'msg': "绘制区域超出图片边界，请重新绘制"}
            response.write(json.dumps(msg))
            return response
        pointArray.append([x, y])
    # print(pointArray)
    pts = np.array(pointArray, np.int32)  # 点坐标转化为numpy数组
    ROI = np.zeros(src.shape, np.uint8)  # 创建与原图同尺寸的空numpy数组，用来保存ROI信息
    cv2.drawContours(ROI, [pts], -1, (255, 255, 255), -1)  # 在ROI空画布上画出轮廓，并填充白色（最后的参数为轮廓线条宽度，如果为负数则直接填充区域）
    imgroi = ROI & src  # ROI和原图进行与运算，筛出原图中的ROI区域
    # cv2.imshow("ROI", imgroi)
    new_url = old_url.split('.')[0] + '_' + str(random.randint(0,100)) + '.' + old_url.split('.')[1]
    new_path = settings.STATICFILES_DIRS[0] + '/' + new_url
    # 保存图片
    cv2.imwrite(new_path, imgroi)
    # 画出轮廓
    # cv2.polylines(src, [pts], True, (0, 255, 255))
    #  展示原图
    # cv2.imshow("img", src)
    #  等待图片的关闭
    # cv2.waitKey()

    url = "../static/" + new_url
    print(url)
    msg = {'code':200, 'url': url}
    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response


# -*-coding:utf-8-*-
import json
import os
import time
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from django.db.models import Max, Min

from django.http import HttpResponse
from django.shortcuts import render
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')


# 显示首页
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from pictureAnnotation import settings
from pictureAnnotationSystem import models
from pictureAnnotationSystem.models import AnnotationInfo, PictureInfo


def showIndex(request):
    return render(request, 'index.html')

# 显示测试页面
def showTest(request):
    return render(request, 'test.html')

# 文件上传
@csrf_exempt
def file_upload(request):
    response = HttpResponse()

    try:
        # 获取前端传输的文件对象
        file_obj = request.FILES.get('file')
        # 获取前端传输的其他参数
        ip = request.POST['ip']
        address = request.POST['address']
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response
    # 获取文件类型
    img_type = file_obj.name.split('.')[1]
    # 将文件类型中的数据大写全部转换成小写
    img_type = img_type.lower()
    url = ''
    width = 0
    height = 0
    if img_type in ['png', 'jpg', 'jpeg', 'gif']:
        # 将图片存到指定目录
        # 获取当前时间的时间戳
        timestr = time.strftime("%Y%m%d%H%M", time.localtime())
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
        width = img.size[0]
        height = img.size[1]
        #  print(img.size[0])
        url = 'images/{0}_{1}'.format(timestr, file_obj.name)
        nowTime = datetime.now()
        nowTimeStr = nowTime.strftime('%Y-%m-%d %H:%M:%S')
        msg = {'code': 200,
               'url': 'static/' + url,
               'width': width,
               'height': height,
               'ip': ip,
               'address': address,
               'time': nowTimeStr
               }
    else:
        # 存储失败, 返回错误信息
        msg = {'code': 305, 'url': '', 'error': '暂不支持该类型'}

    # 保存图片信息到数据库
    pic_info_obj = models.PictureInfo()
    pic_info_obj.pic_url = url
    pic_info_obj.pic_width = width
    pic_info_obj.pic_height = height
    pic_info_obj.pic_user_ip = ip
    pic_info_obj.pic_user_address = address
    pic_info_obj.pic_time = nowTime
    pic_info_obj.save()

    respMsg = json.dumps(msg)
    # 如果不是Ajax的jsonp的异步请求就正常返回Json数组，如果是Ajax就要加jsonpCallback
    response.write(respMsg)
    return response


# 分割图片
def cut_pic(request):
    edit_type = 0 # 记录此次请求目的（0创建 还是 1修改）
    response = HttpResponse()
    try: # 如果有annotation_id参数 则说明是编辑，反之是创建
        annotation_id = request.POST["annotation_id"]
        edit_type = 1
    except MultiValueDictKeyError:
        edit_type = 0

    try:
        if request.POST["url"] == '':
            msg = {'code': 402, 'msg': "请先选择一张图片再进行标注操作"}
            response.write(json.dumps(msg))
            return response
        old_url = request.POST["url"].split('/', 1)[1]
        points = request.POST["points"]
        if edit_type == 0:
            text = request.POST["ctext"]
            dtype = request.POST["type"]
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


    # 获取该图片标注编号的最大值 为了给ROI命名
    pic_info = models.PictureInfo.objects.get(pic_url = old_url)
    annotation_info = pic_info.annotationinfo_set.all()
    if edit_type == 0:
        if len(annotation_info) == 0:
            annotation_id = 1
        else:
            annotation_id = annotation_info.aggregate(Max('annotation_id'))['annotation_id__max']+1
        # print(annotation_id)
    # ROI的文件名（含images/）
    new_url = old_url.split('.')[0] + '_' + str(annotation_id) + '.' + old_url.split('.')[1]
    # 将此记录存入/更新数据库
    nowTime = datetime.now()
    nowTimeStr = nowTime.strftime('%Y-%m-%d %H:%M:%S')
    if edit_type == 0:
        annotation_info_obj = models.AnnotationInfo()
        annotation_info_obj.pic_info = pic_info
        annotation_info_obj.annotation_id = annotation_id
        annotation_info_obj.annotation_text = text
        annotation_info_obj.annotation_type = dtype
    else:
        annotation_info_obj = annotation_info.get(annotation_id = annotation_id)

    annotation_info_obj.annotation_time = nowTime
    annotation_info_obj.annotation_points = points
    annotation_info_obj.save()

    # ROI的访问地址
    new_path = settings.STATICFILES_DIRS[0] + '/' + new_url
    if os.path.exists(new_path):
        os.remove(new_path)

    # 获取外接矩形四个点的坐标
    x, y, w, h = cv2.boundingRect(pts)

    # 如果是编辑图片，则先删除原图

    # 保存图片
    cv2.imencode('.jpg', imgroi[y:y+h, x:x+w])[1].tofile(new_path)
    # 画出轮廓
    # cv2.polylines(src, [pts], True, (0, 255, 255))
    #  展示原图
    # cv2.imshow("img", imgroi[y:y+h, x:x+w])
    #  等待图片的关闭
    # cv2.waitKey()

    url = "static/" + new_url
    # print(url,flush=True)
    # print(url)
    msg = {'code': 200, 'url': url, 'annotation_id': annotation_id, 'time': nowTimeStr}
    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response


# 根据annotation_id和old_url获取标注图片的相关信息
@csrf_exempt
def get_url(request):
    response = HttpResponse()
    try:
        if request.POST["old_url"] == '':
            msg = {'code': 402, 'msg': "未检测到当前图片，请刷新页面重试"}
            response.write(json.dumps(msg))
            return response
        old_url = request.POST["old_url"].split('/', 1)[1]
        # print(old_url)
        annotation_id = request.POST["annotation_id"]
        # print(annotation_id)
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response

    # print(old_url,annotation_id, flush=True)
    try:
        annotation_info = models.PictureInfo.objects.get(pic_url = old_url).annotationinfo_set.get(annotation_id = annotation_id)
    except AnnotationInfo.DoesNotExist:
        msg = {'code': 410, 'msg': "查询图片时出现异常，请刷新后重试"}
        response.write(json.dumps(msg))
        return response
    msg = {
            'code': 200,
            'url': 'static/'+old_url.split('.')[0] + '_' + str(annotation_id) + '.' + old_url.split('.')[1],
            'text': annotation_info.annotation_text,
            'time': annotation_info.annotation_time.strftime("%Y-%m-%d %H:%M:%S"),
            'points': annotation_info.annotation_points,
            'type': annotation_info.annotation_type
          }
    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response


# 获取所有已标注的图片名称和地址
def get_pics(request):
    response = HttpResponse()
    try:
        ip = request.POST["ip"]
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response

    try:
        allInfos = models.PictureInfo.objects.filter(pic_user_ip=ip)
        # print(ip,flush=True)
    except PictureInfo.DoesNotExist:
        msg = {'code': 403, 'msg': "查询图片时出现异常，请刷新后重试"}
        response.write(json.dumps(msg))
        return response
    # 新建一个dict存数据
    picDict = {}
    for info in allInfos:
        # 新建一个Dict存其他数据
        tempDict = {
            'width': info.pic_width,
            'height': info.pic_height,
            'url': info.pic_url,
            'time': info.pic_time.strftime("%Y-%m-%d %H:%M:%S"),
            'ip': info.pic_user_ip,
            'address': info.pic_user_address
        }
        # print(tempDict,flush=True)
        pic_name = info.pic_url.split('/')[1]
        picDict[pic_name] = tempDict
    # print(picDict,flush=True)
    msg = {
            'code': 200,
            'picList': json.dumps(picDict)
          }
    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response


# 根据图片的url获取图片信息以及其所有标注信息
def get_pic_infos(request):
    response = HttpResponse()
    try:
        pic_url = request.POST["pic_url"]
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response

    try:
        pic_infos = models.PictureInfo.objects.get(pic_url=pic_url)
    except PictureInfo.DoesNotExist:
        msg = {'code': 403, 'msg': "查询图片时出现异常，请刷新后重试"}
        response.write(json.dumps(msg))
        return response

    # 新建一个dict存标注的数据们
    annoDict = {}
    for anno_info in pic_infos.annotationinfo_set.all():
        # 新建一个Dict存每个标注的数据
        tempDict = {
            'annotation_id': anno_info.annotation_id,
            'annotation_type': anno_info.annotation_type,
            'annotation_points': anno_info.annotation_points,
            'annotation_text': anno_info.annotation_text,
            'annotation_time': anno_info.annotation_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        annoDict[str(anno_info.annotation_id)] = tempDict

    # 新建一个dict存图片的信息
    picDict = {
        'width': pic_infos.pic_width,
        'height': pic_infos.pic_height,
        'url': pic_infos.pic_url,
        'time': pic_infos.pic_time.strftime("%Y-%m-%d %H:%M:%S"),
        'ip': pic_infos.pic_user_ip,
        'address': pic_infos.pic_user_address,
        'annoList': annoDict
    }

    msg = {
            'code': 200,
            'picList': json.dumps(picDict)
          }
    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response


# 删除某个标注 并返回列表最小的一个标注的信息
def del_annotation(request):
    response = HttpResponse()
    try:
        if request.POST["pic_url"] == '':
            msg = {'code': 402, 'msg': "未检测到当前图片，请刷新页面重试"}
            response.write(json.dumps(msg))
            return response
        pic_url = request.POST["pic_url"].split('/', 1)[1]
        annotation_id = request.POST["annotation_id"]
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response

    # print(pic_url,annotation_id, flush=True)

    path = settings.STATICFILES_DIRS[0] + '/' + pic_url.split('.')[0] + '_' + annotation_id + '.' + pic_url.split('.')[1]
    # print(path,flush=True)
    if os.path.exists(path):
        os.remove(path)
    else:
        msg = {'code': 411, 'msg': "要删除的文件不存在，请刷新页面后重试"}
        response.write(json.dumps(msg))
        return response

    try:
        # 查找数据 并删除
        pic_info = models.PictureInfo.objects.get(pic_url=pic_url)
        annotation_info = pic_info.annotationinfo_set.get(annotation_id=annotation_id)
        annotation_info.delete()
    except AnnotationInfo.DoesNotExist:
        msg = {'code': 403, 'msg': "查询图片时出现异常，请刷新后重试"}
        response.write(json.dumps(msg))
        return response
    try:
        # 查找annotation_id最小的一条数据 并记录 如果没有 url设置为 null
        annotation_min = pic_info.annotationinfo_set.get(
            annotation_id=pic_info.annotationinfo_set.all().aggregate(Min('annotation_id'))['annotation_id__min'])
        # print(annotation_min,flush=True)
        msg = {
            'code': 200,
            'url': 'static/' + pic_url.split('.')[0] + '_' + str(annotation_min.annotation_id) + '.' + pic_url.split('.')[1],
            'text': annotation_min.annotation_text,
            'time': annotation_min.annotation_time.strftime("%Y-%m-%d %H:%M:%S"),
            'points': annotation_min.annotation_points,
            'annotation_min': annotation_min.annotation_id,
            'type': annotation_min.annotation_type
        }
    except AnnotationInfo.DoesNotExist:
        msg = {
            'code': 200,
            'url': 'null',
        }

    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response


# 删除某个图片及其所有标注
def del_picture(request):
    response = HttpResponse()
    try:
        if request.POST["pic_url"] == '':
            msg = {'code': 402, 'msg': "未检测到当前图片，请刷新页面重试"}
            response.write(json.dumps(msg))
            return response
        pic_url = request.POST["pic_url"].split('/', 1)[1]
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response

    # print(pic_url,flush=True)

    # path = settings.STATICFILES_DIRS[0] + '/' + pic_url.split('.')[0] + '_' + annotation_id + '.' + pic_url.split('.')[1]
    # # print(path,flush=True)
    # if os.path.exists(path):
    #     os.remove(path)
    # else:
    #     msg = {'code': 411, 'msg': "要删除的文件不存在，请刷新页面后重试"}
    #     response.write(json.dumps(msg))
    #     return response

    try:
        # 查找数据
        pic_info = models.PictureInfo.objects.get(pic_url=pic_url)
    except PictureInfo.DoesNotExist:
        msg = {'code': 403, 'msg': "查询图片时出现异常，请刷新后重试"}
        response.write(json.dumps(msg))
        return response

    # 删除图片文件
    pic_path = settings.STATICFILES_DIRS[0] + '/' + pic_url
    if os.path.exists(pic_path):
        os.remove(pic_path)
    else:
        msg = {'code': 411, 'msg': "要删除的文件不存在，请刷新页面后重试"}
        response.write(json.dumps(msg))
        return response

    # 迭代pic的标注数据，并删除文件
    annotations = pic_info.annotationinfo_set.all()
    for annotation in annotations:
        annotation_path = settings.STATICFILES_DIRS[0] + '/' + pic_url.split('.')[0] + '_' + str(annotation.annotation_id) + '.' + pic_url.split('.')[1]
        if os.path.exists(annotation_path):
            os.remove(annotation_path)

    # 级联删除数据库中的记录
    pic_info.delete()
    msg = {
        'code': 200,
        'msg': '删除该图片及其所有标注成功'
    }
    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response


# 更新标注内容
def update_annotation_text(request):
    response = HttpResponse()
    try:
        if request.POST["pic_url"] == '':
            msg = {'code': 402, 'msg': "未检测到当前图片，请刷新页面重试"}
            response.write(json.dumps(msg))
            return response
        pic_url = request.POST["pic_url"].split('/', 1)[1]
        annotation_id = request.POST["annotation_id"]
        new_text = request.POST["new_text"]
    except MultiValueDictKeyError:
        msg = {'code': 401, 'msg': "缺少参数"}
        response.write(json.dumps(msg))
        return response

    try:
        # 查找数据
        annotation_info = models.PictureInfo.objects.get(pic_url=pic_url).annotationinfo_set.get(annotation_id=annotation_id)
    except PictureInfo.DoesNotExist:
        msg = {'code': 403, 'msg': "查询图片时出现异常，请刷新后重试"}
        response.write(json.dumps(msg))
        return response

    nowTime = datetime.now()
    nowTimeStr = nowTime.strftime('%Y-%m-%d %H:%M:%S')
    annotation_info.annotation_text = new_text
    annotation_info.annotation_time = nowTime
    annotation_info.save()

    msg = {
        'code': 200,
        'time': nowTimeStr,
        'text': new_text
    }
    respMsg = json.dumps(msg)
    response.write(respMsg)
    return response
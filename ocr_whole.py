# -*- coding:utf-8 -*-
import os
import sys
import cv2
from math import *
import numpy as np
from PIL import Image

# os.environ['CUDA_VISIBLE_DEVICES'] = '2'

sys.path.append(os.getcwd() + '/ctpn')
from ctpn.text_detect import text_detect
from lib.fast_rcnn.config import cfg_from_file
from densenet.model import predict as keras_densenet


# def sort_box(box):
#     """
#     对box进行排序
#     """
#     box = sorted(box, key=lambda x: sum([x[1], x[3], x[5], x[7]]))
#     return box

FIRST = True


def sort_box(box):
    """ 
    对box进行排序
    """
    if len(box > 1):
        new_box = []
        heights = []
        for b in box:
            heights.append(b[5] - b[1])
        heights.sort()
        # max_height = heights[-1]
        max_height = heights[len(heights)//2]
        for b in box:
            height = b[5] - b[1]
            if height > max_height * 0.7:
                new_box.append(b)
        return sorted(new_box, key=lambda x: sum([x[1], x[3], x[5], x[7]]))

    else:
        return sorted(box, key=lambda x: sum([x[1], x[3], x[5], x[7]]))
#
# def dumpRotateImage(img, degree, pt1, pt2, pt3, pt4):
#     height, width = img.shape[:2]
#     heightNew = int(width * fabs(sin(radians(degree))) + height * fabs(cos(radians(degree))))
#     widthNew = int(height * fabs(sin(radians(degree))) + width * fabs(cos(radians(degree))))
#     matRotation = cv2.getRotationMatrix2D((width // 2, height // 2), degree, 1)
#     matRotation[0, 2] += (widthNew - width) // 2
#     matRotation[1, 2] += (heightNew - height) // 2
#     imgRotation = cv2.warpAffine(img, matRotation, (widthNew, heightNew), borderValue=(255, 255, 255))
#     pt1 = list(pt1)
#     pt3 = list(pt3)
#
#     [[pt1[0]], [pt1[1]]] = np.dot(matRotation, np.array([[pt1[0]], [pt1[1]], [1]]))
#     [[pt3[0]], [pt3[1]]] = np.dot(matRotation, np.array([[pt3[0]], [pt3[1]], [1]]))
#     ydim, xdim = imgRotation.shape[:2]
#     imgOut = imgRotation[max(1, int(pt1[1])): min(ydim - 1, int(pt3[1])),
#              max(1, int(pt1[0])): min(xdim - 1, int(pt3[0]))]
#
#     return imgOut

def dumpRotateImage(img, degree, pt1, pt2, pt3, pt4):
    maxdim = max(img.shape[0], img.shape[1])
    RotateMatrix = cv2.getRotationMatrix2D(center=(pt1[0], pt1[1]), angle=degree, scale=1)  # 按第一个点为中心旋转
    RotateMatrix[0][2] += maxdim // 2
    RotateMatrix[1][2] += maxdim // 2
    RotImg = cv2.warpAffine(img, RotateMatrix, (int(maxdim * 1.5), int(maxdim * 1.5)))
    new_points = []
    for point in (pt1, pt2, pt3, pt4):  # 对四个点进行仿射变换，变换到新的图里面
        new_x = RotateMatrix[0][0] * point[0] + RotateMatrix[0][1] * point[1] + RotateMatrix[0][2]
        new_y = RotateMatrix[1][0] * point[0] + RotateMatrix[1][1] * point[1] + RotateMatrix[1][2]
        new_points.append([new_x, new_y])

    xmin = int(min(new_points[0][0], new_points[3][0]))
    xmax = int(max(new_points[1][0], new_points[2][0]))
    ymin = int(min(new_points[0][1], new_points[1][1]))
    ymax = int(max(new_points[2][1], new_points[3][1]))

    cut_img = RotImg[ymin:ymax, xmin:xmax]
    cut_img[cut_img == 0] = 166
    return cut_img

def charRec(img, text_recs, adjust=False):
    """
    加载OCR模型，进行字符识别
    """
    results = {}
    xDim, yDim = img.shape[1], img.shape[0]

    for index, rec in enumerate(text_recs):
        xlength = int((rec[6] - rec[0]) * 0.1)
        ylength = int((rec[7] - rec[1]) * 0.2)
        if adjust:
            pt1 = (max(1, rec[0] - xlength), max(1, rec[1] - ylength))
            pt2 = (rec[2], rec[3])
            pt3 = (min(rec[6] + xlength, xDim - 2), min(yDim - 2, rec[7] + ylength))
            pt4 = (rec[4], rec[5])
        else:
            pt1 = (max(1, rec[0]), max(1, rec[1]))
            pt2 = (rec[2], rec[3])
            pt3 = (min(rec[6], xDim - 2), min(yDim - 2, rec[7]))
            pt4 = (rec[4], rec[5])

        degree = degrees(atan2(pt2[1] - pt1[1], pt2[0] - pt1[0]))  # 图像倾斜角度

        partImg = dumpRotateImage(img, degree, pt1, pt2, pt3, pt4)

        if partImg.shape[0] < 1 or partImg.shape[1] < 1 or partImg.shape[0] > partImg.shape[1]:  # 过滤异常图片
            continue

        image = Image.fromarray(partImg).convert('L')
        text = keras_densenet(image)

        if len(text) > 0:
            results[index] = [rec]
            results[index].append(text)  # 识别文字

    return results


def model(img, adjust=False):
    """
    @img_org: 图片
    @adjust: 是否调整文字识别结果
    """
    global FIRST
    if FIRST:
        FIRST = False
        cfg_from_file('./ctpn/ctpn/text.yml')
    text_recs, img_framed, img = text_detect(img)
    text_recs = sort_box(text_recs)
    result = charRec(img, text_recs, adjust)
    return result, img_framed


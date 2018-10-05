# -*- coding: utf-8 -*-
from werkzeug.utils import secure_filename
from flask import Flask, render_template, jsonify, request, make_response, send_from_directory, abort, send_file
import time
import os
import base64
import cv2
import numpy as np
import datetime
import random
import tensorflow as tf
import demo_final

 
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'jpeg'])

file_dir = os.path.join(basedir, 'upload')
bbox_dir = os.path.join(basedir, 'bbox')
new_filename = ''
output_filename = ''
addrline = ''
addr_base = dict()
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
 
 
 
# 上传文件
@app.route('/upload', methods=['POST'], strict_slashes=False)
def api_upload():
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    if not os.path.exists(bbox_dir):
        os.makedirs(bbox_dir)
    f = request.files['file']
    if f and allowed_file(f.filename):
        fname = secure_filename(f.filename)
        ext = fname.rsplit('.', 1)[1]
        new_filename = Pic_str().create_uuid() + '.' + ext
        f.save(os.path.join(file_dir, new_filename))
        return new_filename
    else:
        return jsonify({"error": 1001, "msg": "上传失败"})
 
@app.route('/download_img/<string:filename>', methods=['GET'])
def download_img(filename):
    global output_filename, addrline
    output_filename, addrline  = demo_final.demo_flask(os.path.join(file_dir, filename))
    if addrline == "":
        addrline = "检测不到地址字段"
    addr_base[filename.split('.')[0]] = addrline
    # print(addrline)
    if request.method == "GET":
        if os.path.isfile(output_filename):
            return send_file(output_filename)
        pass
        
@app.route('/download_txt/<string:filename>', methods=['GET'])
def download_txt(filename):
    if request.method == "GET":
        global output_filename, addrline
        print("Getting txt from: ", filename.split('.')[0] , " : ",addr_base[filename.split('.')[0]])
        #if os.path.isfile(os.path.join(bbox_dir, filename)):
         #   return send_from_directory(bbox_dir, filename, as_attachment=True)
        #pass
        if filename.split('.')[0] in addr_base:
            return addr_base[filename.split('.')[0]]
        else:
            return addrline

class Pic_str:
    def create_uuid(self): #生成唯一的图片的名称字符串，防止图片显示时的重名问题
        nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S");  # 生成当前时间
        randomNum = random.randint(0, 100);  # 生成的随机整数n，其中0<=n<=100
        if randomNum <= 10:
            randomNum = str(0) + str(randomNum);
        uniqueNum = str(nowTime) + str(randomNum);
        return uniqueNum;
 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3389, use_reloader=False, debug=True)

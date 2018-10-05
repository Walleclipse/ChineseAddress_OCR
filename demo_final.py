#-*- coding:utf-8 -*-
import os
import ocr_whole
import time
import shutil
import numpy as np
from PIL import Image
from glob import glob
import Levenshtein
from tgrocery import Grocery
import pickle
import re
from tgrocery.classifier import *
from stupid_addrs_rev import stupid_revise

def is_alphabet(uchar):
   """判断一个unicode是否是英文字母"""
   if (uchar >= u'\u0041' and uchar <= u'\u005a') or (uchar >= u'\u0061' and uchar <= u'\u007a'):
      return True
   else:
      return False


def demo_flask(image_file):
    grocery = Grocery('Addrss_NLP')
    model_name=grocery.name
    text_converter=None
    if (os.path.exists(model_name)):
        tgM=GroceryTextModel(text_converter,model_name)
        tgM.load(model_name)
        grocery.model=tgM
        print('load!!!!!')
    else:
        add_file = open('pkl_data/address1.pkl', 'rb')
        other_file = open('pkl_data/others1.pkl', 'rb')
        add_list = pickle.load(add_file)
        other_list = pickle.load(other_file)
        add_file .close()
        other_file .close()
        grocery = Grocery('Addrss_NLP')
        add_list.extend(other_list)
        grocery.train(add_list)
        print (grocery.get_load_status())
        grocery.save()
        # print('train!!!!!!!!')
    addrline = [] 
    t = time.time()
    result_dir = '/data/share/nginx/html/bbox'
    image = np.array(Image.open(image_file).convert('RGB'))
    result, image_framed = ocr_whole.model(image)
    output_file = os.path.join(result_dir, image_file.split('/')[-1])
    Image.fromarray(image_framed).save(output_file)
    ret_total = ''
    for key in result:
        string1 = result[key][1]
        # print("predict line text :",string1)
        string2 = re.sub("[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*{}[]+", "", string1)
        no_digit = len(list(filter(str.isdigit, string2)))
        no_alpha = len(list(filter(is_alphabet, string2)))
        if '注册' in string2 or '洼册' in string2 or '洼·册' in string2 or '洼.册' in string2 or '汪·册' in string2 or len(set('登记机关') & set(string2)) >= 3 or '电话' in string2 or ((no_digit / len(string2) > 0.7 and no_digit > 5)):
            predict_result='others'
        elif no_alpha>5 or len(set('经营范围化学品') & set(string2)) >= 3 or len(set('年月日') & set(string2)) >= 2:
            predict_result='others'
        else:
            predict_result = grocery.predict(string2)
        if (str(predict_result) == 'address'):
            string1 = string1.replace('《', '(')
            string1 = string1.replace('》', ')')
            string1 = string1.replace('(', '（')
            string1 = string1.replace(')', '）')
            string1 = string1.replace('（（','（')
            if ((not ret_total) or len(string1) > len(ret_total)):
                ret_total = ''
                ret_total += string1
            else:
                ret_total += string1
    
    if '）' in ret_total:
        if '（' not in ret_total:
            ret_total = ret_total.replace('C', '（')
    ret_total = re.sub(r'（(\w)住所(.*)', '', ret_total)
    ret_total = re.sub(r'（(\w)住房(.*)', '', ret_total)
    ret_total = re.sub(r'（不作为(.*)', '', ret_total)
    ret_total = re.sub(r'（有效期(.*)', '', ret_total)
    ret_total = re.sub(r'（仅限(.*)', '', ret_total)
    ret_total = re.sub(r'（临时经营(.*)', '', ret_total)
    ret_total = re.sub(r'（仅限办公(.*)', '', ret_total)
    ret_total = re.sub(r'（经营场所(.*)', '', ret_total)
    ret_total = re.sub(r"^[经]*[营]*[场/住]*[所]*", "", ret_total)
    ret_total = stupid_revise(ret_total)
    print("Mission complete, it took {:.3f}s".format(time.time() - t))
    print('\nRecongition Result:\n')
    print(ret_total)
    return output_file,ret_total



import os
import re
import pandas as pd
import numpy as np
import pickle
from time import time
import heapq
from fuzzywuzzy import fuzz
from Levenshtein import distance


ADDRS_ORDER = {2: 1, 3: 900, 4: 24777, 5: 36135, 6: 43780, 7: 96953, 8: 123455, 9: 136751, 10: 166952,
				  11: 184057, 12: 194794, 13: 219650, 14: 234579, 15: 241632, 16: 245639, 17: 250251,
				  18: 252837, 19: 254605, 20: 256430, 21: 257702, 22: 258438, 23: 258911, 24: 259259,
				  25: 259460, 26: 259655, 27: 259764, 28: 259825, 29: 259868, 30: 259896, 31: 259911,
				  32: 259926, 33: 259929, 34: 259933, 35: 259936, 36: 259936, 37: 259939}

REVISE_DEGREE = 4  #修正到几级地址

CAL_SIMS_METHODS = {0: 'fuzzywuzzy', 1: 'Levenshtein'}  # fuzzywuzzy:2s, Levenshtein:0.2s , fuzzywuzzy_partial_rati0:7s
THRESH_HOLDS = {'fuzzywuzzy': 80, 'Levenshtein': 97}  # 完全匹配：fuzzywuzzy：100， Levenshtein：100
METHOD = CAL_SIMS_METHODS[1]  # 在这里修改相似度算法，0：模糊匹配，1：编辑距离
THRESH = THRESH_HOLDS[METHOD]

#addrs_dir_path = 'libs/so_stupid_smart_adrs_lib_fuck.txt'
addrs_dir_path = 'addrs_libs/so_stupid_smart_adrs_lib_fuck.me.txt'
with open(addrs_dir_path, 'r', encoding='utf-8') as f:
	addrs_lib = f.read()
addrs_lib = addrs_lib.split('\n')

stroke_dir_path = 'addrs_libs/strokes.txt'
with open(stroke_dir_path, 'r', encoding='utf-8') as f:
	stroke_lib = f.read()
stroke_lib = stroke_lib.split('\n')

extra_addrs_dir = 'addrs_libs/full_address1.csv'
extra_lib = pd.read_csv(extra_addrs_dir, encoding='utf-8')
provinces = extra_lib[extra_lib['level']==1].loc[:,'Name']
cities = extra_lib[extra_lib['level']==2].loc[:,'Name']

def may_cut_messy(data):
	flag = re.search('\d室', data)
	if flag is not None:
		data = data[:flag.span()[1]]
	else:
		flag = re.search('\d层', data)
		if flag is not None:
			data = data[:flag.span()[1]]
	cutted_data = data
	for site in provinces:
		flag = re.search(site, data)
		if flag is not None:
			cutted_data = data[flag.span()[0]:]
			return cutted_data
	'''
	for site in cities:
		flag = re.search(site, data)
		if flag is not None:
			cutted_data = data[flag.span()[0]:]
			return cutted_data
	'''
	return cutted_data

def re_prep(orig_data):
	orig_data=may_cut_messy(orig_data)
	punc = "[\s+\.\!\/_,$%^*(+\"\']+|[+——！\-\-()，。？、~@#￥%……&*（）]+"
	if len(orig_data) > 5 and '省' in orig_data[-2:]:
		orig_data = orig_data[:-2] if orig_data[-2]=='省' else orig_data[:-1]
	# if orig_data[-1] in ['.','-','、','.','*']:
		# orig_data = orig_data[:-1]
	#data_ = re.sub('[A-Za-z].*', '', data_)
	#data_ = re.sub('[0-9].*', '', data_)
	data_ = re.sub('市场.*', '', orig_data)
	data_ = re.sub('城市花园.*', '', data_)
	data_ = re.sub('小区.*', '', data_)
	data_ = re.sub('社区.*', '', data_)
	#data_ = re.sub('门市.*', '', data_)
	data_ = re.sub('超市.*', '', data_)
	data_ = re.sub('片区.*', '', data_)
	data_ = re.sub('住宅区.*', '', data_)
	data_ = re.sub('租区.*', '', data_)
	#data_ = re.sub('城市.*', '', data_)
	data_ = re.sub('夜市.*', '', data_)
	data_ = re.sub('服务区.*', '', data_)
	data_ = re.sub('活区.*|工区.*|广场.*', '', data_)
	data_ = re.sub('一区.*', '', data_)
	data_ = re.sub('二区.*', '', data_)
	data_ = re.sub('三区.*', '', data_)
	data_ = re.sub('四区.*', '', data_)
	data_ = re.sub('A区.*|B区.*|C区.*|D区.*|E区.*', '', data_)
	data_ = re.sub('.*?地址', '', data_)
	if len(data_)>9 and '门市' in data_[8:]:
		data_ = re.sub('门市.*', '', data_)
	
	# pattern = '(.*行政区|.*自治区|.*省)?(.*?[市])?(.*?[市|县|盟|州])?(.*[镇|区|乡|街道|街|道])?(.*[村|委员会|委会|市|场|区|所|团|局])?(.*?路)?(\d+号)?'
	pattern = '(.*?行政区|.*?自治区|.*?省)?(.*?市)?(.*?[县|区|州|市|旗])?(.*?街道|.*?[镇|乡|])?(.*?林场|.*?畜场|.*?牧场|.*?农场|.*[村|委员会|委会|市|场|区|所|团|局]])?(.*?路)?(\d+号)?'
	#                   1             1，2,3          2, 3, 4                     4                                               4
	data_split = re.split(pattern, data_)
	data = ''
	for index in range(1, len(data_split)):
		if data_split[index] is not None:
			if index <= REVISE_DEGREE:
				data += data_split[index]
	if len(data) >4 and  ('镇' in data[2:-2] or '街道' in data[:-2]) and data[-1]=='州':
		data = re.sub('镇.*', '镇', data)
		data = re.sub('街道.*', '街道', data)
	#tail = re.sub(punc, '', orig_data)[len(data):]
	tail = orig_data[len(data):]
	#data = re.sub(punc, '', data)
	
	
	return data, tail

def stupid_match_single(data):
	small_stupid_match = []
	low = ADDRS_ORDER[min(max(len(data) - 3, 2),35)] - 1
	up = ADDRS_ORDER[min(len(data) + 4, 37)] - 1
	s_addrs_lib = addrs_lib[low:up]
	for addrs in s_addrs_lib:
		if METHOD == 'Levenshtein':
			sims = 100 - distance(data, addrs)
			if '市' in addrs or '省' in addrs:
				sims2 = 100 - distance(data, addrs.replace('市','').replace('省',''))
				if sims2 > sims:
					sims = sims2
					addrs = addrs.replace('市','').replace('省','')
		else:
			sims = fuzz.ratio(list(data), list(addrs))  # partial_ratio
		s_dict = {'address': addrs, 'similarity': sims}
		if s_dict['similarity'] == 100:
			return [s_dict]
		small_stupid_match.append(s_dict)
	return small_stupid_match

def stupid_stroke_sims(s1, s2):
	union_s = set(s1) & set(s2)
	diff_s1 = set(s1) - union_s
	diff_s2 = set(s2) - union_s
	stroke_s1, stroke_s2 = 0, 0
	for s in diff_s1:
		unicode_ = ord(s)
		if 13312 <= unicode_ <= 64045:
			stroke_s1 += int(stroke_lib[unicode_ - 13312])
		elif 131072 <= unicode_ <= 194998:
			stroke_s1 += int(stroke_lib[unicode_ - 13312])
	for s in diff_s2:
		unicode_ = ord(s)
		if 13312 <= unicode_ <= 64045:
			stroke_s2 += int(stroke_lib[unicode_ - 13312])
		elif 131072 <= unicode_ <= 194998:
			stroke_s2 += int(stroke_lib[unicode_ - 13312])
	return 100 - abs(stroke_s1 - stroke_s2) - 2*abs(len(s1) - len(s2))

def stupid_revise_split(data):
	if len(data)==0:
		return ''
	addrs_match = stupid_match_single(data)
	addrs_match = sorted(addrs_match, key=lambda x: x['similarity'], reverse=True)

	candidates = heapq.nlargest(min(150,len(addrs_match)), addrs_match, key=lambda x: x['similarity'])
	# print('\n original data: \n', orig_data, '\n revised data: \n',candidates[0] + tail)
	# print(candidates)
	# print(candidates[0])
	candidates2 = []
	for can in candidates:
		thresh = THRESH - int(len(data) >= 10) + int(len(data) < 5) + int(len(data) < 4)
		if can['similarity'] >= thresh and can['similarity'] >= candidates[0]['similarity']:
			new_can = can
			new_can['stroke_sims'] = stupid_stroke_sims(new_can['address'], data)
			candidates2.append(new_can)
	candidates2 = sorted(candidates2, key= lambda x: x['stroke_sims'], reverse=True)
	
	if len(candidates2) == 0:
		return data
	
	candidates3 = []
	for can in candidates2:
		if can['stroke_sims'] >= candidates2[0]['stroke_sims']:
			new_can = can
			new_can['len'] = len(can['address'])
			candidates3.append(new_can)
	candidates3 = sorted(candidates3, key=lambda x: x['len'], reverse=True)
	
	return candidates3[0]['address']

def stupid_revise(orig_data):
	orig_time = time()
	data, tail = re_prep(orig_data)
	result = stupid_revise_split(data)
	if len(result) > 0:
		if len(tail) > 0 and result[-1] == tail[0] and result[-1] =='区' :
			result = result[:-1]
		final = result + tail
	else:
		final = orig_data
	final = final.replace(' ','')
	print('timing cosuming:', time() - orig_time)
	return final

def test_stupid():
	punc = "[\.\!\/_,$%^*(+\"\']+|[+——！\-\-()，。？、~@#￥%……&*（）]+"
	# bad_case_dir = '../address_classify/bad_case.txt'
	bad_case_dir = 'address_line_result_name.txt'
	with open(bad_case_dir, 'r', encoding='utf-8') as f:
		bad_case = f.readlines()
	bad_case = [re.sub(punc, '', x.replace('\n', '')) for x in bad_case]
	
	pattern = '(.*行政区|.*自治区|.*省)?(.*?[市])?(.*?[区|县|盟|州])?(.*[镇|乡|街道|街|道])?(.*[村|委员会|委会|市|场|区|所|团|局])?(.*?路)?(\d+号)?'
	#                       1            1，2,3           2，3                   3,4                   4
	
	recount = 0
	al = 0
	print('begin to test...', len(bad_case))
	for index in range(len(bad_case)):
		line = bad_case[index].split()
		label = line[2]
		data_ = re.split(pattern, label)
		data_label = ''
		for ii in range(len(data_)):
			if data_[ii] is not None:
				if ii < 5:
					data_label += data_[ii]
		
		recog = line[3]
		data_ = re.split(pattern, recog)
		data_recog = ''
		for ii in range(len(data_)):
			if data_[ii] is not None:
				if ii < 5:
					data_recog += data_[ii]
		
		if data_recog == data_label or len(data_label) == 0 or len(data_recog) == 0:
			print('so stupid ...')
			continue
		
		revise = stupid_revise(data_recog)
		al += 1
		line = str(al) + ':' + str(recount) + '\n' + data_label + '\n' + data_recog + '\n' + revise + '\n'
		print(line)
		with open(METHOD + '_log_8.19_1.txt', 'a', encoding='utf-8') as f:
			f.write(line)
		if revise == data_label:
			print('Bingo +++++++++++++++++++++++++++++++++++++++++')
			recount += 1
		
		print('revise:', recount, 'in :', al)
	
	print('all revise:', recount)


if __name__=='__main__':
	st_time = time()
	#test_stupid()
	test_list = ['三县','辽宁省鞍山市岫岩满族自治县岫岩镇一街道（锦丝路农场二层住宅）','福建原泉州市惠安县螺城镇','南通市狼山镇街道陆洪社区','镇辽市科尔沁区','宝安区观澜街道新城社区', '杭集镇锦都扬州','常熟世茂•世纪中心一搜秀活力城3号1066','厦辽宁省铁岭市铁岭经济开发区柳条沟9分场']
	for tl in test_list:
		print(stupid_revise(tl))
	print('all_time:',time()-st_time)

import os
import re
import sys

import cv2
import numpy as np

import csv

input_file="bs.csv"
if len(sys.argv)>=2:
	input_file=sys.argv[1]

with open(input_file) as f:
	reader = csv.reader(f)
	lines = [row for row in reader]
	for data in lines:
		name = data[8]
		name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

		if "[タイトル項目]" in data[2]:
			continue

		if name=="":
			continue

		print("ex_map.append(['"+name+"','"+data[1]+"','"+data[7]+":"+data[8]+"'])")

f.close()

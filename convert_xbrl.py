import os

import cv2
import numpy as np

from xbrl2bspl import Xbrl2BsPl

path = "081220180510431993.zip"

f = open(path)
xbrl2bspl=Xbrl2BsPl()
result=xbrl2bspl.convert(f.read())

print "BS:"
if(result["bs"]):
	key_sorted=sorted(result["bs"])
	for key in key_sorted:
		print "{0:60s}".format(key) + " : " + str(result["bs"][key])

print ""

print "PL:"
if(result["pl"]):
	key_sorted=sorted(result["pl"])
	for key in key_sorted:
		print "{0:60s}".format(key) + " : " + str(result["pl"][key])


import os

from xbrl2bspl import Xbrl2BsPl

path = "test_data/081220200508407632.zip"

f = open(path)
xbrl2bspl=Xbrl2BsPl()
result=xbrl2bspl.convert(f.read())

print "BS:"
if(result["bs"]):
	key_sorted=sorted(result["bs"])
	for key in key_sorted:
		if result["bs"][key]!=0:
			print "{0:60s}".format(key) + " : " + str(result["bs"][key])

print ""

print "PL:"
if(result["pl"]):
	key_sorted=sorted(result["pl"])
	for key in key_sorted:
		if result["pl"][key]!=0:
			print "{0:60s}".format(key) + " : " + str(result["pl"][key])

print ""

print "CF:"
if(result["cf"]):
	key_sorted=sorted(result["cf"])
	for key in key_sorted:
		if result["cf"][key]!=0:
			print "{0:60s}".format(key) + " : " + str(result["cf"][key])

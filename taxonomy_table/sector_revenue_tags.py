# EDINETの勘定科目リスト（1f_AccountList.xls）の業種別のシートから、損益計算書の売上高にあたる項目の候補を抜き出す
# xbrl2bspl.py の SECTOR_PC_FALLBACK は、この出力から業種ごとの売上高（合計）を選んだもの
# 使い方：pip install xlrd && python sector_revenue_tags.py 1f_AccountList.xls
# 出力の * は「合計」の項目
import re
import sys

import xlrd

book = xlrd.open_workbook(sys.argv[1] if len(sys.argv) >= 2 else "1f_AccountList.xls")
for sheet in book.sheets()[2:]:
	in_pl = False
	found = []
	for r in range(sheet.nrows):
		row = sheet.row_values(r)
		if str(row[0]).startswith("損益計算書"):
			in_pl = True
			continue
		if in_pl and str(row[0]).endswith("科目一覧"):
			break
		if not in_pl or row[9] != "xbrli:monetaryItemType":
			continue
		label, element = row[1], row[8]
		if re.search(r"(売上高|営業収益|経常収益|完成工事高|業収益|事業収益)$", label) and not re.search(r"(NOI|NOE|EI|EL|SGA)$", element):
			found.append(label + ":" + element + ("*" if "合計" in str(row[5]) else ""))
	print(sheet.name, " | ".join(found))

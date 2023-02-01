#!-*- coding:utf-8 -*-
#!/usr/bin/env python

import re
import sys
import urllib

import zipfile
if sys.version_info.major == 2:
  import StringIO
else:
  from io import BytesIO

try:
  from taxonomy import XbrlTaxonomy
except:
  from .taxonomy import XbrlTaxonomy

class Xbrl2BsPl():
  def read_text(self,zf,f):
    if sys.version_info.major == 2:
      text=zf.read(f)
    else:
      text=zf.open(f, 'r').read().decode("utf-8")
    return text

  def convert(self,content):
    # Zipファイルを開く
    try:
      if sys.version_info.major == 2:
        zf = zipfile.ZipFile(StringIO.StringIO(content),'r')
      else:
        zf = zipfile.ZipFile(BytesIO(content),'r')
    except zipfile.BadZipfile:
      return None

    analyze_success=False
    fields_pl=None
    fields_bs=None
    fields_cf=None
    fields_pc=None

    for f in zf.namelist():
      it_pl = re.finditer("-.*sm-.*\.htm", f, re.DOTALL)
      for m in it_pl:
        text=self.read_text(zf,f)
        fields_pl=self.read_pl(text)

    for f in zf.namelist():
      it_cf = re.finditer("-.*cf[0-9]+-", f, re.DOTALL)
      for m in it_cf:
        text=self.read_text(zf,f)
        fields_cf=self.read_cf(text)

    for f in zf.namelist():
      it_pc = re.findall("-.*pc[0-9]+-", f, re.DOTALL)
      if len(it_pc)==0:
        it_pc = re.findall("-.*pl[0-9]+-", f, re.DOTALL)
      for m in it_pc:
        text=self.read_text(zf,f)
        fields_pc=self.read_pc(text)

    acbs_exist=False
    for f in zf.namelist():
      it_bs = re.finditer("-.*acbs[0-9]+-", f, re.DOTALL)
      for m in it_bs:
        acbs_exist=True # 連結財務諸表が存在する

    for f in zf.namelist():
      if(acbs_exist):
        it_bs = re.finditer("-.*acbs[0-9]+-", f, re.DOTALL)        
      else:
        it_bs = re.finditer("-.*bs[0-9]+-", f, re.DOTALL)
      for m in it_bs:
        text=self.read_text(zf,f)

        fields_bs=self.read_bs(text)
        if(not fields_bs):
          continue
        analyze_success=True

      if(analyze_success):
        break #breakしないと個別財務諸表を読んでしまう

    fields={}
    fields["bs"]=fields_bs
    fields["pl"]=fields_pl
    fields["cf"]=fields_cf
    fields["pc"]=fields_pc
    return fields

  def read_pl_core(self,text,target_date):
    fields={}
    treat_reat_or_specifics_without_per_share="[a-zA-OQ-Z]*"
    fields["net_sales"]=self.get_value("売上高","tse-ed-t:NetSales"+treat_reat_or_specifics_without_per_share,text,target_date)
    if(fields["net_sales"]==0):
      fields["net_sales"]=self.get_value("売上高","tse-ed-t:OperatingRevenues"+treat_reat_or_specifics_without_per_share,text,target_date)
    fields["operation_income"]=self.get_value("営業利益","tse-ed-t:OperatingIncome"+treat_reat_or_specifics_without_per_share,text,target_date)
    fields["ordinary_income"]=self.get_value("経常利益","tse-ed-t:OrdinaryIncome"+treat_reat_or_specifics_without_per_share,text,target_date)
    fields["net_income"]=self.get_value("当期純利益","tse-ed-t:ProfitAttributableToOwnersOfParent"+treat_reat_or_specifics_without_per_share,text,target_date)
    if(fields["net_income"]==0):
      fields["net_income"]=self.get_value("当期純利益","tse-ed-t:NetIncome"+treat_reat_or_specifics_without_per_share,text,target_date)
    fields["net_income_per_share"]=self.get_value("1株当たり当期純利益","tse-ed-t:NetIncomePerShare"+treat_reat_or_specifics_without_per_share,text,target_date,True)
    if(fields["net_income_per_share"]==0):
      fields["net_income_per_share"]=self.get_value("1株当たり当期純利益","tse-ed-t:NetIncomePerUnit"+treat_reat_or_specifics_without_per_share,text,target_date,True)
    return fields

  def read_dividend_per_share_accumulated(self,text,target_date,q2):
    current_accumulated_duration_dividend_per_share=0
    current_accumulated_duration_dividend_per_share=current_accumulated_duration_dividend_per_share+self.get_value("配当","tse-ed-t:DividendPerShare",text,target_date+"_FirstQuarterMember_NonConsolidatedMember_ResultMember",True)
    current_accumulated_duration_dividend_per_share=current_accumulated_duration_dividend_per_share+self.get_value("配当","tse-ed-t:DividendPerShare",text,target_date+"_SecondQuarterMember_NonConsolidatedMember_ResultMember",True)
    if(not q2):
      current_accumulated_duration_dividend_per_share=current_accumulated_duration_dividend_per_share+self.get_value("配当","tse-ed-t:DividendPerShare",text,target_date+"_ThirdQuarterMember_NonConsolidatedMember_ResultMember",True)
      current_accumulated_duration_dividend_per_share=current_accumulated_duration_dividend_per_share+self.get_value("配当","tse-ed-t:DividendPerShare",text,target_date+"_YearEndMember_NonConsolidatedMember_ResultMember",True)
    return current_accumulated_duration_dividend_per_share

  def read_dividend_per_share(self,text,target_date):
    dividend=self.get_value("配当","tse-ed-t:DividendPerShare",text,target_date,True)
    if(dividend==0):
      dividend=self.get_value("配当","tse-re-t:DistributionsPerUnitIncludingDistributionsInExcessOfProfitREIT",text,target_date,True)
    return dividend

  def read_pl(self,text):
    #連結の場合に個別業績を無視
    text=text.split("（参考）個別業績の概要")[0]

    #四半期決算
    fields=self.read_pl_core(text,"CurrentAccumulated[a-zA-Z_0-9]*")
    current_accumulated_duration_net_sales=fields["net_sales"]
    current_accumulated_duration_operation_income=fields["operation_income"]
    current_accumulated_duration_ordinary_income=fields["ordinary_income"]
    current_accumulated_duration_net_income=fields["net_income"]
    current_accumulated_duration_net_income_per_share=fields["net_income_per_share"]

    #通期決算
    if(current_accumulated_duration_net_sales==0):
      fields=self.read_pl_core(text,"CurrentYearDuration[a-zA-Z_0-9]*")
      current_accumulated_duration_net_sales=fields["net_sales"]
      current_accumulated_duration_operation_income=fields["operation_income"]
      current_accumulated_duration_ordinary_income=fields["ordinary_income"]
      current_accumulated_duration_net_income=fields["net_income"]
      current_accumulated_duration_net_income_per_share=fields["net_income_per_share"]

    #業績予想
    fields=self.read_pl_core(text,"CurrentYear[a-zA-Z_]*")
    current_year_duration_net_sales=fields["net_sales"]
    current_year_duration_operation_income=fields["operation_income"]
    current_year_duration_ordinary_income=fields["ordinary_income"]
    current_year_duration_net_income=fields["net_income"]
    current_year_duration_net_income_per_share=fields["net_income_per_share"]

    #来期中間予想
    fields=self.read_pl_core(text,"NextAccumulatedQ2Duration_ConsolidatedMember_ForecastMember")
    next_accumulated_duration_net_sales=fields["net_sales"]
    next_accumulated_duration_operation_income=fields["operation_income"]
    next_accumulated_duration_ordinary_income=fields["ordinary_income"]
    next_accumulated_duration_net_income=fields["net_income"]
    next_accumulated_duration_net_income_per_share=fields["net_income_per_share"]

    #来期予想
    fields=self.read_pl_core(text,"NextYear[a-zA-Z_]*")
    next_year_duration_net_sales=fields["net_sales"]
    next_year_duration_operation_income=fields["operation_income"]
    next_year_duration_ordinary_income=fields["ordinary_income"]
    next_year_duration_net_income=fields["net_income"]
    next_year_duration_net_income_per_share=fields["net_income_per_share"]

    #配当予想
    current_accumulated_duration_dividend_per_share=self.read_dividend_per_share_accumulated(text,"CurrentYearDuration",False)
    current_year_duration_dividend_per_share=self.read_dividend_per_share(text,"CurrentYearDuration_AnnualMember_NonConsolidatedMember_ForecastMember")

    next_accumulated_duration_dividend_per_share=self.read_dividend_per_share_accumulated(text,"NextYearDuration",True)
    next_year_duration_dividend_per_share=self.read_dividend_per_share(text,"NextYearDuration_AnnualMember_NonConsolidatedMember_ForecastMember")

    #REIT配当予想
    if(current_accumulated_duration_dividend_per_share==0):
      current_accumulated_duration_dividend_per_share=self.read_dividend_per_share(text,"CurrentYearDuration_NonConsolidatedMember_ResultMember")
    if(current_year_duration_dividend_per_share==0):
      current_year_duration_dividend_per_share=self.read_dividend_per_share(text,"CurrentYearDuration_NonConsolidatedMember_ResultMember")
    if(next_year_duration_dividend_per_share==0):
      next_year_duration_dividend_per_share=self.read_dividend_per_share(text,"NextYearDuration_NonConsolidatedMember_ForecastMember")

    net_sales_progress=0
    operation_income_progress=0
    ordinary_income_progress=0
    net_income_progress=0

    if(current_year_duration_net_sales!=0):
      net_sales_progress=1.0*current_accumulated_duration_net_sales/current_year_duration_net_sales
    if(current_year_duration_operation_income!=0):
      operation_income_progress=1.0*current_accumulated_duration_operation_income/current_year_duration_operation_income
    if(current_year_duration_ordinary_income!=0):
      ordinary_income_progress=1.0*current_accumulated_duration_ordinary_income/current_year_duration_ordinary_income
    if(current_year_duration_net_income!=0):
      net_income_progress=1.0*current_accumulated_duration_net_income/current_year_duration_net_income

    fields={}

    fields['current_accumulated_duration_net_sales']=current_accumulated_duration_net_sales
    fields['current_accumulated_duration_operation_income']=current_accumulated_duration_operation_income
    fields['current_accumulated_duration_ordinary_income']=current_accumulated_duration_ordinary_income
    fields['current_accumulated_duration_net_income']=current_accumulated_duration_net_income
    fields['current_accumulated_duration_net_income_per_share']=current_accumulated_duration_net_income_per_share
    fields['current_accumulated_duration_dividend_per_share']=current_accumulated_duration_dividend_per_share

    fields['current_year_duration_net_sales']=current_year_duration_net_sales
    fields['current_year_duration_operation_income']=current_year_duration_operation_income
    fields['current_year_duration_ordinary_income']=current_year_duration_ordinary_income
    fields['current_year_duration_net_income']=current_year_duration_net_income
    fields['current_year_duration_net_income_per_share']=current_year_duration_net_income_per_share
    fields['current_year_duration_dividend_per_share']=current_year_duration_dividend_per_share

    fields['next_accumulated_duration_net_sales']=next_accumulated_duration_net_sales
    fields['next_accumulated_duration_operation_income']=next_accumulated_duration_operation_income
    fields['next_accumulated_duration_ordinary_income']=next_accumulated_duration_ordinary_income
    fields['next_accumulated_duration_net_income']=next_accumulated_duration_net_income
    fields['next_accumulated_duration_net_income_per_share']=next_accumulated_duration_net_income_per_share
    fields['next_accumulated_duration_dividend_per_share']=next_accumulated_duration_dividend_per_share

    fields['next_year_duration_net_sales']=next_year_duration_net_sales
    fields['next_year_duration_operation_income']=next_year_duration_operation_income
    fields['next_year_duration_ordinary_income']=next_year_duration_ordinary_income
    fields['next_year_duration_net_income']=next_year_duration_net_income
    fields['next_year_duration_net_income_per_share']=next_year_duration_net_income_per_share
    fields['next_year_duration_dividend_per_share']=next_year_duration_dividend_per_share

    fields['net_sales_progress']=net_sales_progress
    fields['operation_income_progress']=operation_income_progress
    fields['ordinary_income_progress']=ordinary_income_progress
    fields['net_income_progress']=net_income_progress

    ex_map = XbrlTaxonomy.pl_taxonomy()
    for i in range(0,len(ex_map)):
      v=self.get_value(ex_map[i][1],ex_map[i][2],text,"CurrentAccumulated[a-zA-Z_0-9]*",yen_unit=True)
      if v==0:
        v=self.get_value(ex_map[i][1],ex_map[i][2],text,"CurrentYearInstant_NonConsolidatedMember_ResultMember",yen_unit=True)
      if v==0:
        v=self.get_value(ex_map[i][1],ex_map[i][2],text,"CurrentYearDuration_NonConsolidatedMember_ResultMember",yen_unit=True)
      fields[ex_map[i][0]]=v
      
    return fields

  def read_bs(self,text):
    fields={}

    ex_map = XbrlTaxonomy.bs_taxonomy()
    for i in range(0,len(ex_map)):
      fields[ex_map[i][0]]=self.get_value(ex_map[i][1],ex_map[i][2],text)

    if(fields["notes_and_accounts_receivable_trade"]==0):
      fields["notes_and_accounts_receivable_trade"]=fields["notes_and_accounts_receivable_trade"]+self.get_value("売掛金","jppfs_cor:AccountsReceivableTrade",text)
      fields["notes_and_accounts_receivable_trade"]=fields["notes_and_accounts_receivable_trade"]+self.get_value("受取手形","jppfs_cor:NotesReceivableTrade",text)

    return fields

  def read_cf(self,text):
    fields={}

    ex_map = XbrlTaxonomy.cf_taxonomy()
    for i in range(0,len(ex_map)):
      fields[ex_map[i][0]]=self.get_value(ex_map[i][1],ex_map[i][2],text,"Current[a-zA-Z_]*")

    return fields

  def read_pc(self,text):
    fields={}

    ex_map = XbrlTaxonomy.pc_taxonomy()
    for i in range(0,len(ex_map)):
      fields[ex_map[i][0]]=self.get_value(ex_map[i][1],ex_map[i][2],text,"Current[a-zA-Z_]*")

    return fields

  def get_value(self,jap,item,line,context=None,yen_unit=False):
    if(not context):
      context="Current[a-zA-Z_]*"
    item=item.replace("tse-ed-t","tse-[a-zA-Z]*-t") #reit対応
    term1 = "contextRef=\""+context+"\""
    term2 = "name=\""+item+"\""
    it1 = re.finditer("<ix:[^<>]*"+term1+"[^<>]*?"+term2+"[^<>]*?>([ 0-9,\.]+)<", line, re.DOTALL)
    it2 = re.finditer("<ix:[^<>]*"+term2+"[^<>]*?"+term1+"[^<>]*?>([ 0-9,\.]+)<", line, re.DOTALL)
    debug = False
    #debug = item=="jppfs_cor:NetCashProvidedByUsedInFinancingActivities"
    value = self.get_value_adjust(it1,True,yen_unit,debug)
    if(value == 0):
      value = self.get_value_adjust(it2,True,yen_unit,debug)
    return value

  def get_value_adjust(self,it,treat_sign,yen_unit,debug):
    for m in it:
        if(debug):
          print(m.group(0))

        it2 = re.finditer("scale=\"([0-9]+)\"", m.group(0), re.DOTALL)
        scale=6
        for m2 in it2:
          scale=int(m2.group(1))

        sign=1
        if(treat_sign):
          it3 = re.finditer("sign=\"-\"", m.group(0), re.DOTALL)
          for m3 in it3:
            sign=-1

        it4 = re.finditer("decimals=\"([0-9]+)\"", m.group(0), re.DOTALL)
        decimals=6  #百万円単位に統一する
        if(yen_unit):
          decimals=0  #配当は円単位に統一する
        #for m2 in it4:
        #  decimals=int(m2.group(1))

        value=m.group(1)
        if(debug):
          print(value)
        value=value.replace(",","")
        value=value.replace(" ","")
        if(value.find(".")!=-1):
          return float(value)*(10**scale)/(10**decimals)*sign
        value_fixed=int(value)*(10**scale)/(10**decimals)*sign
        if(debug):
          print(scale)
          print(decimals)
          print(value_fixed)
        return value_fixed

    return 0

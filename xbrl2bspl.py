#!-*- coding:utf-8 -*-
#!/usr/bin/env python

import re
import sys
import urllib

import zipfile
import StringIO

class Xbrl2BsPl():
  def convert(self,content):
    # Zipファイルを開く
    try:
      zf = zipfile.ZipFile(StringIO.StringIO(content),'r')
    except zipfile.BadZipfile:
      return None

    analyze_success=False
    fields_pl=None
    fields_bs=None

    for f in zf.namelist():
      it_pl = re.finditer("-.*sm-.*\.htm", f, re.DOTALL)
      for m in it_pl:
        text=zf.read(f)
        fields_pl=self.read_pl(text)

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
        text=zf.read(f)

        fields_bs=self.read_bs(text)
        if(not fields_bs):
          continue
        analyze_success=True

      if(analyze_success):
        break #breakしないと個別財務諸表を読んでしまう

    fields={}
    fields["bs"]=fields_bs
    fields["pl"]=fields_pl
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

    return fields

  def read_bs(self,text):
    fields={}
    fields["cash_and_deposits"]=self.get_value("現金及び預金","jppfs_cor:CashAndDeposits",text)
    fields["notes_and_accounts_receivable_trade"]=self.get_value("受取手形及び売掛金","jppfs_cor:NotesAndAccountsReceivableTrade",text)
    if(fields["notes_and_accounts_receivable_trade"]==0):
      fields["notes_and_accounts_receivable_trade"]=fields["notes_and_accounts_receivable_trade"]+self.get_value("売掛金","jppfs_cor:AccountsReceivableTrade",text)
      fields["notes_and_accounts_receivable_trade"]=fields["notes_and_accounts_receivable_trade"]+self.get_value("受取手形","jppfs_cor:NotesReceivableTrade",text)
    fields["short_term_investment_securities"]=self.get_value("有価証券","jppfs_cor:ShortTermInvestmentSecurities",text)
    fields["investment_securities"]=self.get_value("投資有価証券","jppfs_cor:InvestmentSecurities",text)
    fields["land"]=self.get_value("土地","jppfs_cor:Land",text)
    fields["buildings_and_structures"]=self.get_value("建物及び構築物","jppfs_cor:BuildingsAndStructures",text)
    fields["buildings_and_structures_net"]=self.get_value("建物及び構築物（純額）","jppfs_cor:BuildingsAndStructuresNet",text)
    fields["allowance_for_doubtful_accounts_ioa_by_group"]=self.get_value("貸倒引当金","jppfs_cor:AllowanceForDoubtfulAccountsIOAByGroup",text)
    fields["deferred_tax_assets_ca"]=self.get_value("繰延税金資産","jppfs_cor:DeferredTaxAssetsCA",text)
    fields["deferred_tax_liabilities_ncl"]=self.get_value("繰延税金負債","jppfs_cor:DeferredTaxLiabilitiesNCL",text)
    fields["current_assets"]=self.get_value("流動資産合計","jppfs_cor:CurrentAssets",text)
    fields["assets"]=self.get_value("資産合計","jppfs_cor:Assets",text)
    fields["liabilities"]=self.get_value("負債合計","jppfs_cor:Liabilities",text)
    fields["net_assets"]=self.get_value("純資産合計","jppfs_cor:NetAssets",text)
    fields["liabilities_and_net_assets"]=self.get_value("負債純資産合計","jppfs_cor:LiabilitiesAndNetAssets",text)
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
    value = self.get_value_adjust(it1,True,yen_unit,debug)
    if(value == 0):
      value = self.get_value_adjust(it2,True,yen_unit,debug)
    return value

  def get_value_adjust(self,it,treat_sign,yen_unit,debug):
    for m in it:
        if(debug):
          print m.group(0)

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
          print value
        value=value.replace(",","")
        value=value.replace(" ","")
        if(value.find(".")!=-1):
          return float(value)*(10**scale)/(10**decimals)*sign
        value_fixed=int(value)*(10**scale)/(10**decimals)*sign
        if(debug):
          print scale
          print decimals
          print value_fixed
        return value_fixed

    return 0

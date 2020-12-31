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

  @staticmethod
  def expression_map():
    ex_map=[]

    ex_map.append(['cash_and_deposits','現金及び預金','jppfs_cor:CashAndDeposits'])
    ex_map.append(['notes_and_accounts_receivable_trade','受取手形及び売掛金','jppfs_cor:NotesAndAccountsReceivableTrade'])
    ex_map.append(['allowance_for_doubtful_accounts_notes_and_accounts_receivable_trade','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsNotesAndAccountsReceivableTrade'])
    ex_map.append(['notes_and_accounts_receivable_trade_net','受取手形及び売掛金（純額）','jppfs_cor:NotesAndAccountsReceivableTradeNet'])
    ex_map.append(['notes_receivable_trade','受取手形','jppfs_cor:NotesReceivableTrade'])
    ex_map.append(['allowance_for_doubtful_accounts_notes_receivable_trade','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsNotesReceivableTrade'])
    ex_map.append(['notes_receivable_trade_net','受取手形（純額）','jppfs_cor:NotesReceivableTradeNet'])
    ex_map.append(['accounts_receivable_trade','売掛金','jppfs_cor:AccountsReceivableTrade'])
    ex_map.append(['allowance_for_doubtful_accounts_accounts_receivable_trade','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsAccountsReceivableTrade'])
    ex_map.append(['accounts_receivable_trade_net','売掛金（純額）','jppfs_cor:AccountsReceivableTradeNet'])
    ex_map.append(['accounts_receivable_from_subsidiaries_and_affiliates_trade','関係会社売掛金','jppfs_cor:AccountsReceivableFromSubsidiariesAndAffiliatesTrade'])
    ex_map.append(['accounts_receivable_installment','割賦売掛金','jppfs_cor:AccountsReceivableInstallment'])
    ex_map.append(['accounts_receivable_development_business','開発事業未収入金','jppfs_cor:AccountsReceivableDevelopmentBusiness'])
    ex_map.append(['accounts_receivable_real_estate_business','不動産事業未収入金','jppfs_cor:AccountsReceivableRealEstateBusiness'])
    ex_map.append(['accounts_receivable_completed_operation','完成業務未収入金','jppfs_cor:AccountsReceivableCompletedOperation'])
    ex_map.append(['accounts_receivable_due_from_franchised_stores','加盟店貸勘定','jppfs_cor:AccountsReceivableDueFromFranchisedStores'])
    ex_map.append(['notes_and_operating_accounts_receivable_c_a','受取手形及び営業未収入金','jppfs_cor:NotesAndOperatingAccountsReceivableCA'])
    ex_map.append(['operating_accounts_receivable_c_a','営業未収入金','jppfs_cor:OperatingAccountsReceivableCA'])
    ex_map.append(['electronically_recorded_monetary_claims_operating_c_a','電子記録債権','jppfs_cor:ElectronicallyRecordedMonetaryClaimsOperatingCA'])
    ex_map.append(['operating_loans_c_a','営業貸付金','jppfs_cor:OperatingLoansCA'])
    ex_map.append(['short_term_investment_securities','有価証券','jppfs_cor:ShortTermInvestmentSecurities'])
    ex_map.append(['stocks_of_parent_company_c_a','親会社株式','jppfs_cor:StocksOfParentCompanyCA'])
    ex_map.append(['money_held_in_trust_c_a','金銭の信託','jppfs_cor:MoneyHeldInTrustCA'])
    ex_map.append(['operational_investment_securities_c_a','営業投資有価証券','jppfs_cor:OperationalInvestmentSecuritiesCA'])
    ex_map.append(['inventories','たな卸資産','jppfs_cor:Inventories'])
    ex_map.append(['merchandise','商品','jppfs_cor:Merchandise'])
    ex_map.append(['goods_in_transit','未着商品','jppfs_cor:GoodsInTransit'])
    ex_map.append(['finished_goods','製品','jppfs_cor:FinishedGoods'])
    ex_map.append(['by_product','副産物','jppfs_cor:ByProduct'])
    ex_map.append(['merchandise_and_finished_goods','商品及び製品','jppfs_cor:MerchandiseAndFinishedGoods'])
    ex_map.append(['semi_finished_goods','半製品','jppfs_cor:SemiFinishedGoods'])
    ex_map.append(['raw_materials','原材料','jppfs_cor:RawMaterials'])
    ex_map.append(['raw_materials_and_supplies','原材料及び貯蔵品','jppfs_cor:RawMaterialsAndSupplies'])
    ex_map.append(['raw_materials_in_transit','未着原材料','jppfs_cor:RawMaterialsInTransit'])
    ex_map.append(['work_in_process','仕掛品','jppfs_cor:WorkInProcess'])
    ex_map.append(['partly_finished_work','半成工事','jppfs_cor:PartlyFinishedWork'])
    ex_map.append(['supplies','貯蔵品','jppfs_cor:Supplies'])
    ex_map.append(['real_estate_for_sale','販売用不動産','jppfs_cor:RealEstateForSale'])
    ex_map.append(['real_estate_for_sale_in_process','仕掛販売用不動産','jppfs_cor:RealEstateForSaleInProcess'])
    ex_map.append(['development_projects_in_progress','開発事業等支出金','jppfs_cor:DevelopmentProjectsInProgress'])
    ex_map.append(['costs_on_real_estate_business','不動産事業支出金','jppfs_cor:CostsOnRealEstateBusiness'])
    ex_map.append(['costs_on_uncompleted_services','未成業務支出金','jppfs_cor:CostsOnUncompletedServices'])
    ex_map.append(['land_and_buildings_for_sale_in_lots','分譲土地建物','jppfs_cor:LandAndBuildingsForSaleInLots'])
    ex_map.append(['land_for_sale_in_lots','分譲土地','jppfs_cor:LandForSaleInLots'])
    ex_map.append(['other_inventories','その他のたな卸資産','jppfs_cor:OtherInventories'])
    ex_map.append(['advance_payments_trade','前渡金','jppfs_cor:AdvancePaymentsTrade'])
    ex_map.append(['advance_payments_other','前払金','jppfs_cor:AdvancePaymentsOther'])
    ex_map.append(['prepaid_expenses','前払費用','jppfs_cor:PrepaidExpenses'])
    ex_map.append(['deferred_tax_assets_c_a','繰延税金資産','jppfs_cor:DeferredTaxAssetsCA'])
    ex_map.append(['accrued_income','未収収益','jppfs_cor:AccruedIncome'])
    ex_map.append(['accrued_interest','未収利息','jppfs_cor:AccruedInterest'])
    ex_map.append(['short_term_claims_on_shareholders_directors_or_employees','株主、役員又は従業員に対する短期債権','jppfs_cor:ShortTermClaimsOnShareholdersDirectorsOrEmployees'])
    ex_map.append(['allowance_for_doubtful_accounts_short_term_claims_on_shareholders_directors_or_employees','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsShortTermClaimsOnShareholdersDirectorsOrEmployees'])
    ex_map.append(['short_term_claims_on_shareholders_directors_or_employees_net','株主、役員又は従業員に対する短期債権（純額）','jppfs_cor:ShortTermClaimsOnShareholdersDirectorsOrEmployeesNet'])
    ex_map.append(['short_term_loans_receivable','短期貸付金','jppfs_cor:ShortTermLoansReceivable'])
    ex_map.append(['allowance_for_doubtful_accounts_short_term_loans','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsShortTermLoans'])
    ex_map.append(['short_term_loans_receivable_net','短期貸付金（純額）','jppfs_cor:ShortTermLoansReceivableNet'])
    ex_map.append(['short_term_loans_receivable_to_subsidiaries_and_affiliates','関係会社短期貸付金','jppfs_cor:ShortTermLoansReceivableToSubsidiariesAndAffiliates'])
    ex_map.append(['allowance_for_doubtful_accounts_short_term_loans_receivable_from_subsidiaries_and_affiliates','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsShortTermLoansReceivableFromSubsidiariesAndAffiliates'])
    ex_map.append(['short_term_loans_receivable_to_subsidiaries_and_affiliates_net','関係会社短期貸付金（純額）','jppfs_cor:ShortTermLoansReceivableToSubsidiariesAndAffiliatesNet'])
    ex_map.append(['accounts_receivable_other','未収入金','jppfs_cor:AccountsReceivableOther'])
    ex_map.append(['accounts_receivable_other_from_subsidiaries_and_affiliates','関係会社未収入金','jppfs_cor:AccountsReceivableOtherFromSubsidiariesAndAffiliates'])
    ex_map.append(['consumption_taxes_receivable','未収消費税等','jppfs_cor:ConsumptionTaxesReceivable'])
    ex_map.append(['income_taxes_receivable','未収還付法人税等','jppfs_cor:IncomeTaxesReceivable'])
    ex_map.append(['non_operating_notes_receivable','営業外受取手形','jppfs_cor:NonOperatingNotesReceivable'])
    ex_map.append(['electronically_recorded_monetary_claims_non_operating_c_a','営業外電子記録債権','jppfs_cor:ElectronicallyRecordedMonetaryClaimsNonOperatingCA'])
    ex_map.append(['current_portion_of_long_term_loans_receivable','1年内回収予定の長期貸付金','jppfs_cor:CurrentPortionOfLongTermLoansReceivable'])
    ex_map.append(['current_portion_of_long_term_loans_receivable_from_subsidiaries_and_affiliates','1年内回収予定の関係会社長期貸付金','jppfs_cor:CurrentPortionOfLongTermLoansReceivableFromSubsidiariesAndAffiliates'])
    ex_map.append(['current_portion_of_guarantee_deposits','1年内回収予定の差入保証金','jppfs_cor:CurrentPortionOfGuaranteeDeposits'])
    ex_map.append(['other_accounts_receivable','その他の未収入金','jppfs_cor:OtherAccountsReceivable'])
    ex_map.append(['deposit_paid_in_subsidiaries_and_affiliates','関係会社預け金','jppfs_cor:DepositPaidInSubsidiariesAndAffiliates'])
    ex_map.append(['short_term_receivables_from_subsidiaries_and_affiliates','関係会社短期債権','jppfs_cor:ShortTermReceivablesFromSubsidiariesAndAffiliates'])
    ex_map.append(['beneficiary_right_of_accounts_receivable_in_trust','金銭債権信託受益権','jppfs_cor:BeneficiaryRightOfAccountsReceivableInTrust'])
    ex_map.append(['guarantee_deposits_c_a','差入保証金','jppfs_cor:GuaranteeDepositsCA'])
    ex_map.append(['short_term_claims_on_employees','従業員に対する短期債権','jppfs_cor:ShortTermClaimsOnEmployees'])
    ex_map.append(['short_term_loans_to_employees','従業員に対する短期貸付金','jppfs_cor:ShortTermLoansToEmployees'])
    ex_map.append(['trust_beneficiary_right_c_a','信託受益権','jppfs_cor:TrustBeneficiaryRightCA'])
    ex_map.append(['advances_paid','立替金','jppfs_cor:AdvancesPaid'])
    ex_map.append(['suspense_payments','仮払金','jppfs_cor:SuspensePayments'])
    ex_map.append(['deposits_paid','預け金','jppfs_cor:DepositsPaid'])
    ex_map.append(['lease_receivables_c_a','リース債権','jppfs_cor:LeaseReceivablesCA'])
    ex_map.append(['allowance_for_doubtful_accounts_lease_receivables_c_a','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsLeaseReceivablesCA'])
    ex_map.append(['lease_receivables_net_c_a','リース債権（純額）','jppfs_cor:LeaseReceivablesNetCA'])
    ex_map.append(['lease_investment_assets_c_a','リース投資資産','jppfs_cor:LeaseInvestmentAssetsCA'])
    ex_map.append(['allowance_for_doubtful_accounts_lease_investment_assets_c_a','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsLeaseInvestmentAssetsCA'])
    ex_map.append(['lease_investment_assets_net_c_a','リース投資資産（純額）','jppfs_cor:LeaseInvestmentAssetsNetCA'])
    ex_map.append(['lease_receivables_and_investment_assets_c_a','リース債権及びリース投資資産','jppfs_cor:LeaseReceivablesAndInvestmentAssetsCA'])
    ex_map.append(['allowance_for_doubtful_accounts_lease_receivables_and_investment_assets_c_a','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsLeaseReceivablesAndInvestmentAssetsCA'])
    ex_map.append(['lease_receivables_and_investment_assets_net_c_a','リース債権及びリース投資資産（純額）','jppfs_cor:LeaseReceivablesAndInvestmentAssetsNetCA'])
    ex_map.append(['derivatives_c_a','デリバティブ債権','jppfs_cor:DerivativesCA'])
    ex_map.append(['forward_exchange_contracts_c_a','為替予約','jppfs_cor:ForwardExchangeContractsCA'])
    ex_map.append(['interest_rate_swap_assets_c_a','金利スワップ資産','jppfs_cor:InterestRateSwapAssetsCA'])
    ex_map.append(['interest_rate_swap_c_a','金利スワップ','jppfs_cor:InterestRateSwapCA'])
    ex_map.append(['purchased_currency_option_c_a','買建通貨オプション','jppfs_cor:PurchasedCurrencyOptionCA'])
    ex_map.append(['currency_option_c_a','通貨オプション','jppfs_cor:CurrencyOptionCA'])
    ex_map.append(['option_c_a','オプション資産','jppfs_cor:OptionCA'])
    ex_map.append(['prepaid_pension_cost_c_a','前払年金費用','jppfs_cor:PrepaidPensionCostCA'])
    ex_map.append(['allowance_for_doubtful_accounts_c_a','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsCA'])
    ex_map.append(['accounts_receivable_installment_sales_credit_guarantee_c_a','信用保証割賦売掛金','jppfs_cor:AccountsReceivableInstallmentSalesCreditGuaranteeCA'])
    ex_map.append(['securities_in_deposit_c_a','寄託有価証券','jppfs_cor:SecuritiesInDepositCA'])
    ex_map.append(['commercial_notes_c_a','商業手形','jppfs_cor:CommercialNotesCA'])
    ex_map.append(['loans_on_margin_transaction_c_a','貸借取引貸付金','jppfs_cor:LoansOnMarginTransactionCA'])
    ex_map.append(['general_loans_c_a','一般貸付金','jppfs_cor:GeneralLoansCA'])
    ex_map.append(['bond_financing_c_a','公社債貸付金','jppfs_cor:BondFinancingCA'])
    ex_map.append(['securities_lent_c_a','貸付有価証券','jppfs_cor:SecuritiesLentCA'])
    ex_map.append(['collateral_money_for_securities_borrowed_c_a','借入有価証券代り金','jppfs_cor:CollateralMoneyForSecuritiesBorrowedCA'])
    ex_map.append(['purchased_receivables_c_a','買取債権','jppfs_cor:PurchasedReceivablesCA'])
    ex_map.append(['other_c_a','その他','jppfs_cor:OtherCA'])
    ex_map.append(['current_assets','流動資産','jppfs_cor:CurrentAssets'])
    ex_map.append(['buildings','建物','jppfs_cor:Buildings'])
    ex_map.append(['accumulated_depreciation_buildings','減価償却累計額','jppfs_cor:AccumulatedDepreciationBuildings'])
    ex_map.append(['accumulated_impairment_loss_buildings','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossBuildings'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_buildings','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossBuildings'])
    ex_map.append(['buildings_net','建物（純額）','jppfs_cor:BuildingsNet'])
    ex_map.append(['buildings_and_accompanying_facilities','建物附属設備','jppfs_cor:BuildingsAndAccompanyingFacilities'])
    ex_map.append(['accumulated_depreciation_buildings_and_accompanying_facilities','減価償却累計額','jppfs_cor:AccumulatedDepreciationBuildingsAndAccompanyingFacilities'])
    ex_map.append(['accumulated_impairment_loss_buildings_and_accompanying_facilities','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossBuildingsAndAccompanyingFacilities'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_buildings_and_accompanying_facilities','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossBuildingsAndAccompanyingFacilities'])
    ex_map.append(['buildings_and_accompanying_facilities_net','建物附属設備（純額）','jppfs_cor:BuildingsAndAccompanyingFacilitiesNet'])
    ex_map.append(['structures','構築物','jppfs_cor:Structures'])
    ex_map.append(['accumulated_depreciation_structures','減価償却累計額','jppfs_cor:AccumulatedDepreciationStructures'])
    ex_map.append(['accumulated_impairment_loss_structures','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossStructures'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_structures','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossStructures'])
    ex_map.append(['structures_net','構築物（純額）','jppfs_cor:StructuresNet'])
    ex_map.append(['buildings_and_structures','建物及び構築物','jppfs_cor:BuildingsAndStructures'])
    ex_map.append(['accumulated_depreciation_buildings_and_structures','減価償却累計額','jppfs_cor:AccumulatedDepreciationBuildingsAndStructures'])
    ex_map.append(['accumulated_impairment_loss_buildings_and_structures','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossBuildingsAndStructures'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_buildings_and_structures','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossBuildingsAndStructures'])
    ex_map.append(['buildings_and_structures_net','建物及び構築物（純額）','jppfs_cor:BuildingsAndStructuresNet'])
    ex_map.append(['machinery_and_equipment','機械及び装置','jppfs_cor:MachineryAndEquipment'])
    ex_map.append(['accumulated_depreciation_machinery_and_equipment','減価償却累計額','jppfs_cor:AccumulatedDepreciationMachineryAndEquipment'])
    ex_map.append(['accumulated_impairment_loss_machinery_and_equipment','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossMachineryAndEquipment'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_machinery_and_equipment','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossMachineryAndEquipment'])
    ex_map.append(['machinery_and_equipment_net','機械及び装置（純額）','jppfs_cor:MachineryAndEquipmentNet'])
    ex_map.append(['vessels','船舶','jppfs_cor:Vessels'])
    ex_map.append(['accumulated_depreciation_vessels','減価償却累計額','jppfs_cor:AccumulatedDepreciationVessels'])
    ex_map.append(['accumulated_impairment_loss_vessels','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossVessels'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_vessels','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossVessels'])
    ex_map.append(['vessels_net','船舶（純額）','jppfs_cor:VesselsNet'])
    ex_map.append(['vehicles','車両運搬具','jppfs_cor:Vehicles'])
    ex_map.append(['accumulated_depreciation_vehicles','減価償却累計額','jppfs_cor:AccumulatedDepreciationVehicles'])
    ex_map.append(['accumulated_impairment_loss_vehicles','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossVehicles'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_vehicles','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossVehicles'])
    ex_map.append(['vehicles_net','車両運搬具（純額）','jppfs_cor:VehiclesNet'])
    ex_map.append(['tools_furniture_and_fixtures','工具、器具及び備品','jppfs_cor:ToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_depreciation_tools_furniture_and_fixtures','減価償却累計額','jppfs_cor:AccumulatedDepreciationToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_impairment_loss_tools_furniture_and_fixtures','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_tools_furniture_and_fixtures','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossToolsFurnitureAndFixtures'])
    ex_map.append(['tools_furniture_and_fixtures_net','工具、器具及び備品（純額）','jppfs_cor:ToolsFurnitureAndFixturesNet'])
    ex_map.append(['machinery_equipment_and_vehicles','機械装置及び運搬具','jppfs_cor:MachineryEquipmentAndVehicles'])
    ex_map.append(['accumulated_depreciation_machinery_equipment_and_vehicles','減価償却累計額','jppfs_cor:AccumulatedDepreciationMachineryEquipmentAndVehicles'])
    ex_map.append(['accumulated_impairment_loss_machinery_equipment_and_vehicles','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossMachineryEquipmentAndVehicles'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_machinery_equipment_and_vehicles','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossMachineryEquipmentAndVehicles'])
    ex_map.append(['machinery_equipment_and_vehicles_net','機械装置及び運搬具（純額）','jppfs_cor:MachineryEquipmentAndVehiclesNet'])
    ex_map.append(['vehicles_tools_furniture_and_fixtures','車両運搬具及び工具器具備品','jppfs_cor:VehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_depreciation_vehicles_tools_furniture_and_fixtures','減価償却累計額','jppfs_cor:AccumulatedDepreciationVehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_impairment_loss_vehicles_tools_furniture_and_fixtures','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossVehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_vehicles_tools_furniture_and_fixtures','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossVehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['vehicles_tools_furniture_and_fixtures_net','車両運搬具及び工具器具備品（純額）','jppfs_cor:VehiclesToolsFurnitureAndFixturesNet'])
    ex_map.append(['machinery_vehicles_tools_furniture_and_fixtures','機械、運搬具及び工具器具備品','jppfs_cor:MachineryVehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_depreciation_machinery_vehicles_tools_furniture_and_fixtures','減価償却累計額','jppfs_cor:AccumulatedDepreciationMachineryVehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_impairment_loss_machinery_vehicles_tools_furniture_and_fixtures','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossMachineryVehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_machinery_vehicles_tools_furniture_and_fixtures','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossMachineryVehiclesToolsFurnitureAndFixtures'])
    ex_map.append(['machinery_vehicles_tools_furniture_and_fixtures_net','機械、運搬具及び工具器具備品（純額）','jppfs_cor:MachineryVehiclesToolsFurnitureAndFixturesNet'])
    ex_map.append(['land','土地','jppfs_cor:Land'])
    ex_map.append(['lease_assets_p_p_e','リース資産','jppfs_cor:LeaseAssetsPPE'])
    ex_map.append(['accumulated_depreciation_lease_assets_p_p_e','減価償却累計額','jppfs_cor:AccumulatedDepreciationLeaseAssetsPPE'])
    ex_map.append(['accumulated_impairment_loss_lease_assets_p_p_e','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossLeaseAssetsPPE'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_lease_assets_p_p_e','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossLeaseAssetsPPE'])
    ex_map.append(['lease_assets_net_p_p_e','リース資産（純額）','jppfs_cor:LeaseAssetsNetPPE'])
    ex_map.append(['construction_in_progress','建設仮勘定','jppfs_cor:ConstructionInProgress'])
    ex_map.append(['aircraft','航空機','jppfs_cor:Aircraft'])
    ex_map.append(['accumulated_depreciation_aircraft','減価償却累計額','jppfs_cor:AccumulatedDepreciationAircraft'])
    ex_map.append(['aircraft_net','航空機（純額）','jppfs_cor:AircraftNet'])
    ex_map.append(['mountain_forests','山林','jppfs_cor:MountainForests'])
    ex_map.append(['assets_for_rent','貸与資産','jppfs_cor:AssetsForRent'])
    ex_map.append(['accumulated_depreciation_assets_for_rent','減価償却累計額','jppfs_cor:AccumulatedDepreciationAssetsForRent'])
    ex_map.append(['assets_for_rent_net','貸与資産（純額）','jppfs_cor:AssetsForRentNet'])
    ex_map.append(['real_estate_for_rent','賃貸不動産','jppfs_cor:RealEstateForRent'])
    ex_map.append(['accumulated_depreciation_real_estate_for_rent','減価償却累計額','jppfs_cor:AccumulatedDepreciationRealEstateForRent'])
    ex_map.append(['real_estate_for_rent_net','賃貸不動産（純額）','jppfs_cor:RealEstateForRentNet'])
    ex_map.append(['trees_p_p_e','立木','jppfs_cor:TreesPPE'])
    ex_map.append(['other_facilities_p_p_e','その他の設備','jppfs_cor:OtherFacilitiesPPE'])
    ex_map.append(['golf_courses','コース勘定','jppfs_cor:GolfCourses'])
    ex_map.append(['docks_and_building_berths_v_e_s','ドック船台','jppfs_cor:DocksAndBuildingBerthsVES'])
    ex_map.append(['accumulated_depreciation_docks_and_building_berths_v_e_s','減価償却累計額','jppfs_cor:AccumulatedDepreciationDocksAndBuildingBerthsVES'])
    ex_map.append(['accumulated_impairment_loss_docks_and_building_berths','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossDocksAndBuildingBerths'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_docks_and_building_berths','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossDocksAndBuildingBerths'])
    ex_map.append(['docks_and_building_berths_net_v_e_s','ドック船台（純額）','jppfs_cor:DocksAndBuildingBerthsNetVES'])
    ex_map.append(['other_p_p_e','その他','jppfs_cor:OtherPPE'])
    ex_map.append(['accumulated_depreciation_other_p_p_e','減価償却累計額','jppfs_cor:AccumulatedDepreciationOtherPPE'])
    ex_map.append(['accumulated_impairment_loss_other_p_p_e','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossOtherPPE'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_other_p_p_e','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossOtherPPE'])
    ex_map.append(['other_net_p_p_e','その他（純額）','jppfs_cor:OtherNetPPE'])
    ex_map.append(['accumulated_depreciation_p_p_e_by_group','減価償却累計額','jppfs_cor:AccumulatedDepreciationPPEByGroup'])
    ex_map.append(['accumulated_impairment_loss_p_p_e_by_group','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossPPEByGroup'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_p_p_e_by_group','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossPPEByGroup'])
    ex_map.append(['property_plant_and_equipment','有形固定資産','jppfs_cor:PropertyPlantAndEquipment'])
    ex_map.append(['patent_right','特許権','jppfs_cor:PatentRight'])
    ex_map.append(['leasehold_right','借地権','jppfs_cor:LeaseholdRight'])
    ex_map.append(['right_of_trademark','商標権','jppfs_cor:RightOfTrademark'])
    ex_map.append(['utility_model_right','実用新案権','jppfs_cor:UtilityModelRight'])
    ex_map.append(['design_right','意匠権','jppfs_cor:DesignRight'])
    ex_map.append(['mining_right','鉱業権','jppfs_cor:MiningRight'])
    ex_map.append(['fishery_right','漁業権','jppfs_cor:FisheryRight'])
    ex_map.append(['software','ソフトウエア','jppfs_cor:Software'])
    ex_map.append(['software_in_progress','ソフトウエア仮勘定','jppfs_cor:SoftwareInProgress'])
    ex_map.append(['goodwill','のれん','jppfs_cor:Goodwill'])
    ex_map.append(['lease_assets_i_a','リース資産','jppfs_cor:LeaseAssetsIA'])
    ex_map.append(['right_to_operate_public_facilities','公共施設等運営権','jppfs_cor:RightToOperatePublicFacilities'])
    ex_map.append(['in_process_research_and_development_i_a','仕掛研究開発','jppfs_cor:InProcessResearchAndDevelopmentIA'])
    ex_map.append(['right_of_using_facilities_i_a','施設利用権','jppfs_cor:RightOfUsingFacilitiesIA'])
    ex_map.append(['telephone_subscription_right','電話加入権','jppfs_cor:TelephoneSubscriptionRight'])
    ex_map.append(['right_of_using_electric_supply_facilities','電気供給施設利用権','jppfs_cor:RightOfUsingElectricSupplyFacilities'])
    ex_map.append(['right_of_using_telecommunication_facilities','電気通信施設利用権','jppfs_cor:RightOfUsingTelecommunicationFacilities'])
    ex_map.append(['right_of_using_telephone_and_telegraph_facilities','電信電話専用施設利用権','jppfs_cor:RightOfUsingTelephoneAndTelegraphFacilities'])
    ex_map.append(['right_of_using_public_facilities','公共施設利用権','jppfs_cor:RightOfUsingPublicFacilities'])
    ex_map.append(['right_of_using_water_facilities','水道施設利用権','jppfs_cor:RightOfUsingWaterFacilities'])
    ex_map.append(['right_of_using_other_facilities','その他の施設利用権','jppfs_cor:RightOfUsingOtherFacilities'])
    ex_map.append(['industrial_property','工業所有権','jppfs_cor:IndustrialProperty'])
    ex_map.append(['house_leasehold_right','借家権','jppfs_cor:HouseLeaseholdRight'])
    ex_map.append(['right_of_using_patent','特許実施権','jppfs_cor:RightOfUsingPatent'])
    ex_map.append(['water_right','水利権','jppfs_cor:WaterRight'])
    ex_map.append(['copyright_publishing','版権','jppfs_cor:CopyrightPublishing'])
    ex_map.append(['copyright','著作権','jppfs_cor:Copyright'])
    ex_map.append(['other_i_a','その他','jppfs_cor:OtherIA'])
    ex_map.append(['intangible_assets','無形固定資産','jppfs_cor:IntangibleAssets'])
    ex_map.append(['investment_securities','投資有価証券','jppfs_cor:InvestmentSecurities'])
    ex_map.append(['stocks_of_subsidiaries_and_affiliates','関係会社株式','jppfs_cor:StocksOfSubsidiariesAndAffiliates'])
    ex_map.append(['bonds_of_subsidiaries_and_affiliates','関係会社社債','jppfs_cor:BondsOfSubsidiariesAndAffiliates'])
    ex_map.append(['investments_in_other_securities_of_subsidiaries_and_affiliates','その他の関係会社有価証券','jppfs_cor:InvestmentsInOtherSecuritiesOfSubsidiariesAndAffiliates'])
    ex_map.append(['operational_investment_securities_i_o_a','営業投資有価証券','jppfs_cor:OperationalInvestmentSecuritiesIOA'])
    ex_map.append(['investments_in_capital','出資金','jppfs_cor:InvestmentsInCapital'])
    ex_map.append(['investments_in_capital_of_subsidiaries_and_affiliates','関係会社出資金','jppfs_cor:InvestmentsInCapitalOfSubsidiariesAndAffiliates'])
    ex_map.append(['operating_investments_in_capital','営業出資金','jppfs_cor:OperatingInvestmentsInCapital'])
    ex_map.append(['investments_in_silent_partnership','匿名組合出資金','jppfs_cor:InvestmentsInSilentPartnership'])
    ex_map.append(['long_term_loans_receivable','長期貸付金','jppfs_cor:LongTermLoansReceivable'])
    ex_map.append(['allowance_for_doubtful_accounts_long_term_loans_receivable','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsLongTermLoansReceivable'])
    ex_map.append(['long_term_loans_receivable_net','長期貸付金（純額）','jppfs_cor:LongTermLoansReceivableNet'])
    ex_map.append(['long_term_loans_receivable_from_subsidiaries_and_affiliates','関係会社長期貸付金','jppfs_cor:LongTermLoansReceivableFromSubsidiariesAndAffiliates'])
    ex_map.append(['allowance_for_doubtful_accounts_long_term_loans_receivable_from_subsidiaries_and_affiliates','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsLongTermLoansReceivableFromSubsidiariesAndAffiliates'])
    ex_map.append(['long_term_loans_receivable_from_subsidiaries_and_affiliates_net','関係会社長期貸付金（純額）','jppfs_cor:LongTermLoansReceivableFromSubsidiariesAndAffiliatesNet'])
    ex_map.append(['long_term_loans_receivable_from_shareholders_directors_or_employees','株主、役員又は従業員に対する長期貸付金','jppfs_cor:LongTermLoansReceivableFromShareholdersDirectorsOrEmployees'])
    ex_map.append(['allowance_for_doubtful_accounts_long_term_loans_receivable_from_shareholders_directors_or_employees','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsLongTermLoansReceivableFromShareholdersDirectorsOrEmployees'])
    ex_map.append(['long_term_loans_receivable_from_shareholders_directors_or_employees_net','株主、役員又は従業員に対する長期貸付金（純額）','jppfs_cor:LongTermLoansReceivableFromShareholdersDirectorsOrEmployeesNet'])
    ex_map.append(['long_term_loans_receivable_from_employees','従業員に対する長期貸付金','jppfs_cor:LongTermLoansReceivableFromEmployees'])
    ex_map.append(['allowance_for_doubtful_accounts_long_term_loans_receivable_from_employees','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsLongTermLoansReceivableFromEmployees'])
    ex_map.append(['long_term_loans_receivable_from_employees_net','従業員に対する長期貸付金（純額）','jppfs_cor:LongTermLoansReceivableFromEmployeesNet'])
    ex_map.append(['long_term_loans_receivable_from_directors_and_employees','役員及び従業員に対する長期貸付金','jppfs_cor:LongTermLoansReceivableFromDirectorsAndEmployees'])
    ex_map.append(['long_term_loans_receivable_from_directors','役員に対する長期貸付金','jppfs_cor:LongTermLoansReceivableFromDirectors'])
    ex_map.append(['stocks_of_parent_company_i_o_a','親会社株式','jppfs_cor:StocksOfParentCompanyIOA'])
    ex_map.append(['claims_provable_in_bankruptcy_claims_provable_in_rehabilitation_and_other','破産更生債権等','jppfs_cor:ClaimsProvableInBankruptcyClaimsProvableInRehabilitationAndOther'])
    ex_map.append(['allowance_for_doubtful_accounts_claims_in_bankruptcy_reorganization_claims_and_other','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsClaimsInBankruptcyReorganizationClaimsAndOther'])
    ex_map.append(['claims_provable_in_bankruptcy_claims_provable_in_rehabilitation_and_other_net','破産更生債権等（純額）','jppfs_cor:ClaimsProvableInBankruptcyClaimsProvableInRehabilitationAndOtherNet'])
    ex_map.append(['long_term_prepaid_expenses','長期前払費用','jppfs_cor:LongTermPrepaidExpenses'])
    ex_map.append(['long_term_prepaid_consumption_taxes','長期前払消費税等','jppfs_cor:LongTermPrepaidConsumptionTaxes'])
    ex_map.append(['prepaid_pension_cost_i_o_a','前払年金費用','jppfs_cor:PrepaidPensionCostIOA'])
    ex_map.append(['net_defined_benefit_asset','退職給付に係る資産','jppfs_cor:NetDefinedBenefitAsset'])
    ex_map.append(['deferred_tax_assets_i_o_a','繰延税金資産','jppfs_cor:DeferredTaxAssetsIOA'])
    ex_map.append(['deferred_tax_assets_for_land_revaluation','再評価に係る繰延税金資産','jppfs_cor:DeferredTaxAssetsForLandRevaluation'])
    ex_map.append(['real_estate_for_investment','投資不動産','jppfs_cor:RealEstateForInvestment'])
    ex_map.append(['accumulated_depreciation_real_estate_for_investment','減価償却累計額','jppfs_cor:AccumulatedDepreciationRealEstateForInvestment'])
    ex_map.append(['accumulated_impairment_loss_real_estate_for_investment','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossRealEstateForInvestment'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_real_estate_for_investment','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossRealEstateForInvestment'])
    ex_map.append(['real_estate_for_investment_net','投資不動産（純額）','jppfs_cor:RealEstateForInvestmentNet'])
    ex_map.append(['beneficiary_right_of_real_estate_in_trust','不動産信託受益権','jppfs_cor:BeneficiaryRightOfRealEstateInTrust'])
    ex_map.append(['land_in_trust','信託土地','jppfs_cor:LandInTrust'])
    ex_map.append(['buildings_in_trust','信託建物','jppfs_cor:BuildingsInTrust'])
    ex_map.append(['lease_investment_assets_i_o_a','リース投資資産','jppfs_cor:LeaseInvestmentAssetsIOA'])
    ex_map.append(['derivatives_i_o_a','デリバティブ債権','jppfs_cor:DerivativesIOA'])
    ex_map.append(['forward_exchange_contracts_i_o_a','為替予約','jppfs_cor:ForwardExchangeContractsIOA'])
    ex_map.append(['interest_rate_swap_assets_i_o_a','金利スワップ資産','jppfs_cor:InterestRateSwapAssetsIOA'])
    ex_map.append(['interest_rate_swap_i_o_a','金利スワップ','jppfs_cor:InterestRateSwapIOA'])
    ex_map.append(['purchased_currency_option_i_o_a','買建通貨オプション','jppfs_cor:PurchasedCurrencyOptionIOA'])
    ex_map.append(['currency_option_i_o_a','通貨オプション','jppfs_cor:CurrencyOptionIOA'])
    ex_map.append(['option_i_o_a','オプション資産','jppfs_cor:OptionIOA'])
    ex_map.append(['long_term_deposits','長期預け金','jppfs_cor:LongTermDeposits'])
    ex_map.append(['long_term_time_deposits','長期預金','jppfs_cor:LongTermTimeDeposits'])
    ex_map.append(['insurance_funds','保険積立金','jppfs_cor:InsuranceFunds'])
    ex_map.append(['life_insurance_funds','生命保険積立金','jppfs_cor:LifeInsuranceFunds'])
    ex_map.append(['group_life_insurance','団体生命保険金','jppfs_cor:GroupLifeInsurance'])
    ex_map.append(['membership','会員権','jppfs_cor:Membership'])
    ex_map.append(['golf_club_membership','ゴルフ会員権','jppfs_cor:GolfClubMembership'])
    ex_map.append(['facility_membership','施設利用会員権','jppfs_cor:FacilityMembership'])
    ex_map.append(['guarantee_deposits_i_o_a','差入保証金','jppfs_cor:GuaranteeDepositsIOA'])
    ex_map.append(['long_term_accounts_receivable_from_subsidiaries_and_affiliates','関係会社長期未収入金','jppfs_cor:LongTermAccountsReceivableFromSubsidiariesAndAffiliates'])
    ex_map.append(['lease_deposits_i_o_a','敷金','jppfs_cor:LeaseDepositsIOA'])
    ex_map.append(['lease_and_guarantee_deposits','敷金及び保証金','jppfs_cor:LeaseAndGuaranteeDeposits'])
    ex_map.append(['bad_debts','固定化営業債権','jppfs_cor:BadDebts'])
    ex_map.append(['business_insurance_funds','事業保険積立金','jppfs_cor:BusinessInsuranceFunds'])
    ex_map.append(['business_insurance','事業保険金','jppfs_cor:BusinessInsurance'])
    ex_map.append(['admission_fee_i_o_a','入会金','jppfs_cor:AdmissionFeeIOA'])
    ex_map.append(['deposits_on_admission','入会保証金','jppfs_cor:DepositsOnAdmission'])
    ex_map.append(['trust_beneficiary_right_i_o_a','信託受益権','jppfs_cor:TrustBeneficiaryRightIOA'])
    ex_map.append(['long_term_non_operating_accounts_receivable','長期営業外未収入金','jppfs_cor:LongTermNonOperatingAccountsReceivable'])
    ex_map.append(['long_term_accounts_receivable_other','長期未収入金','jppfs_cor:LongTermAccountsReceivableOther'])
    ex_map.append(['construction_assistance_fund_receivables','建設協力金','jppfs_cor:ConstructionAssistanceFundReceivables'])
    ex_map.append(['deposits_for_stores_in_preparation','店舗賃借仮勘定','jppfs_cor:DepositsForStoresInPreparation'])
    ex_map.append(['fund_for_retirement_benefits_for_directors_i_o_a','役員退職積立金','jppfs_cor:FundForRetirementBenefitsForDirectorsIOA'])
    ex_map.append(['insurance_funds_for_directors','役員に対する保険積立金','jppfs_cor:InsuranceFundsForDirectors'])
    ex_map.append(['long_term_investments','長期投資','jppfs_cor:LongTermInvestments'])
    ex_map.append(['other_i_o_a','その他','jppfs_cor:OtherIOA'])
    ex_map.append(['allowance_for_doubtful_accounts_i_o_a_by_group','貸倒引当金','jppfs_cor:AllowanceForDoubtfulAccountsIOAByGroup'])
    ex_map.append(['allowance_for_investment_loss','投資損失引当金','jppfs_cor:AllowanceForInvestmentLoss'])
    ex_map.append(['investments_and_other_assets_gross','投資その他の資産','jppfs_cor:InvestmentsAndOtherAssetsGross'])
    ex_map.append(['accumulated_depreciation_i_o_a_by_group','減価償却累計額','jppfs_cor:AccumulatedDepreciationIOAByGroup'])
    ex_map.append(['accumulated_impairment_loss_i_o_a_by_group','減損損失累計額','jppfs_cor:AccumulatedImpairmentLossIOAByGroup'])
    ex_map.append(['accumulated_depreciation_and_impairment_loss_i_o_a_by_group','減価償却累計額及び減損損失累計額','jppfs_cor:AccumulatedDepreciationAndImpairmentLossIOAByGroup'])
    ex_map.append(['investments_and_other_assets','投資その他の資産','jppfs_cor:InvestmentsAndOtherAssets'])
    ex_map.append(['noncurrent_assets','固定資産','jppfs_cor:NoncurrentAssets'])
    ex_map.append(['deferred_organization_expenses_d_a','創立費','jppfs_cor:DeferredOrganizationExpensesDA'])
    ex_map.append(['business_commencement_expenses_d_a','開業費','jppfs_cor:BusinessCommencementExpensesDA'])
    ex_map.append(['stock_issuance_cost_d_a','株式交付費','jppfs_cor:StockIssuanceCostDA'])
    ex_map.append(['bond_issuance_cost_d_a','社債発行費','jppfs_cor:BondIssuanceCostDA'])
    ex_map.append(['development_expenses_d_a','開発費','jppfs_cor:DevelopmentExpensesDA'])
    ex_map.append(['other_d_a','その他','jppfs_cor:OtherDA'])
    ex_map.append(['deferred_assets','繰延資産','jppfs_cor:DeferredAssets'])
    ex_map.append(['assets','資産','jppfs_cor:Assets'])
    ex_map.append(['notes_and_accounts_payable_trade','支払手形及び買掛金','jppfs_cor:NotesAndAccountsPayableTrade'])
    ex_map.append(['notes_payable_trade','支払手形','jppfs_cor:NotesPayableTrade'])
    ex_map.append(['accounts_payable_trade','買掛金','jppfs_cor:AccountsPayableTrade'])
    ex_map.append(['operating_accounts_payable','営業未払金','jppfs_cor:OperatingAccountsPayable'])
    ex_map.append(['notes_and_operating_accounts_payable_trade','支払手形及び営業未払金','jppfs_cor:NotesAndOperatingAccountsPayableTrade'])
    ex_map.append(['electronically_recorded_obligations_operating_c_l','電子記録債務','jppfs_cor:ElectronicallyRecordedObligationsOperatingCL'])
    ex_map.append(['accounts_payable_operating_specific','業務未払金','jppfs_cor:AccountsPayableOperatingSpecific'])
    ex_map.append(['accounts_payable_consignment','受託販売未払金','jppfs_cor:AccountsPayableConsignment'])
    ex_map.append(['accounts_payable_real_estate','不動産事業未払金','jppfs_cor:AccountsPayableRealEstate'])
    ex_map.append(['due_to_franchised_stores','加盟店借勘定','jppfs_cor:DueToFranchisedStores'])
    ex_map.append(['gift_certificates','商品券','jppfs_cor:GiftCertificates'])
    ex_map.append(['advances_received_on_uncompleted_contracts','未成業務受入金','jppfs_cor:AdvancesReceivedOnUncompletedContracts'])
    ex_map.append(['deposit_received_real_estate','不動産事業受入金','jppfs_cor:DepositReceivedRealEstate'])
    ex_map.append(['accounts_payable_other_and_accrued_expenses','未払金及び未払費用','jppfs_cor:AccountsPayableOtherAndAccruedExpenses'])
    ex_map.append(['accrued_expenses','未払費用','jppfs_cor:AccruedExpenses'])
    ex_map.append(['deferred_tax_liabilities_c_l','繰延税金負債','jppfs_cor:DeferredTaxLiabilitiesCL'])
    ex_map.append(['advances_received','前受金','jppfs_cor:AdvancesReceived'])
    ex_map.append(['deferred_contribution_for_construction','前受工事負担金','jppfs_cor:DeferredContributionForConstruction'])
    ex_map.append(['unearned_revenue','前受収益','jppfs_cor:UnearnedRevenue'])
    ex_map.append(['lease_obligations_c_l','リース債務','jppfs_cor:LeaseObligationsCL'])
    ex_map.append(['asset_retirement_obligations_c_l','資産除去債務','jppfs_cor:AssetRetirementObligationsCL'])
    ex_map.append(['liabilities_related_to_right_to_operate_public_facilities_c_l','公共施設等運営権に係る負債','jppfs_cor:LiabilitiesRelatedToRightToOperatePublicFacilitiesCL'])
    ex_map.append(['derivatives_liabilities_c_l','デリバティブ債務','jppfs_cor:DerivativesLiabilitiesCL'])
    ex_map.append(['forward_exchange_contracts_c_l','為替予約','jppfs_cor:ForwardExchangeContractsCL'])
    ex_map.append(['interest_rate_swap_liabilities_c_l','金利スワップ負債','jppfs_cor:InterestRateSwapLiabilitiesCL'])
    ex_map.append(['interest_rate_swap_c_l','金利スワップ','jppfs_cor:InterestRateSwapCL'])
    ex_map.append(['sold_currency_option_c_l','売建通貨オプション','jppfs_cor:SoldCurrencyOptionCL'])
    ex_map.append(['currency_option_c_l','通貨オプション','jppfs_cor:CurrencyOptionCL'])
    ex_map.append(['option_c_l','オプション負債','jppfs_cor:OptionCL'])
    ex_map.append(['provision_for_product_warranties','製品保証引当金','jppfs_cor:ProvisionForProductWarranties'])
    ex_map.append(['provision_for_bonuses','賞与引当金','jppfs_cor:ProvisionForBonuses'])
    ex_map.append(['provision_for_repairs','修繕引当金','jppfs_cor:ProvisionForRepairs'])
    ex_map.append(['provision_for_directors_bonuses','役員賞与引当金','jppfs_cor:ProvisionForDirectorsBonuses'])
    ex_map.append(['provision_for_loss_on_guarantees_c_l','債務保証損失引当金','jppfs_cor:ProvisionForLossOnGuaranteesCL'])
    ex_map.append(['provision_for_point_card_certificates_c_l','ポイント引当金','jppfs_cor:ProvisionForPointCardCertificatesCL'])
    ex_map.append(['provision_for_shareholder_benefit_program_c_l','株主優待引当金','jppfs_cor:ProvisionForShareholderBenefitProgramCL'])
    ex_map.append(['provision_for_sales_rebates','売上割戻引当金','jppfs_cor:ProvisionForSalesRebates'])
    ex_map.append(['provision_for_loss_on_construction_contracts','工事損失引当金','jppfs_cor:ProvisionForLossOnConstructionContracts'])
    ex_map.append(['provision_for_warranties_for_completed_construction','完成工事補償引当金','jppfs_cor:ProvisionForWarrantiesForCompletedConstruction'])
    ex_map.append(['provision_for_loss_on_store_closing','店舗閉鎖損失引当金','jppfs_cor:ProvisionForLossOnStoreClosing'])
    ex_map.append(['provision_for_sales_promotion_expenses','販売促進引当金','jppfs_cor:ProvisionForSalesPromotionExpenses'])
    ex_map.append(['provision_for_sales_returns','返品調整引当金','jppfs_cor:ProvisionForSalesReturns'])
    ex_map.append(['provision_for_loss_on_order_received_c_l','受注損失引当金','jppfs_cor:ProvisionForLossOnOrderReceivedCL'])
    ex_map.append(['provision_for_loss_on_liquidation_of_subsidiaries_and_affiliates_c_l','関係会社整理損失引当金','jppfs_cor:ProvisionForLossOnLiquidationOfSubsidiariesAndAffiliatesCL'])
    ex_map.append(['provision_for_loss_on_business_liquidation_c_l','事業整理損失引当金','jppfs_cor:ProvisionForLossOnBusinessLiquidationCL'])
    ex_map.append(['provision_for_loss_on_business_of_subsidiaries_and_affiliates_c_l','関係会社事業損失引当金','jppfs_cor:ProvisionForLossOnBusinessOfSubsidiariesAndAffiliatesCL'])
    ex_map.append(['provision_for_business_structure_improvement_c_l','事業構造改善引当金','jppfs_cor:ProvisionForBusinessStructureImprovementCL'])
    ex_map.append(['provision_for_environmental_measures_c_l','環境対策引当金','jppfs_cor:ProvisionForEnvironmentalMeasuresCL'])
    ex_map.append(['provision_for_loss_on_litigation_c_l','訴訟損失引当金','jppfs_cor:ProvisionForLossOnLitigationCL'])
    ex_map.append(['provision_for_loss_on_interest_repayment_c_l','利息返還損失引当金','jppfs_cor:ProvisionForLossOnInterestRepaymentCL'])
    ex_map.append(['provision_for_contingent_loss_c_l','偶発損失引当金','jppfs_cor:ProvisionForContingentLossCL'])
    ex_map.append(['provision_for_guarantee_for_loans_c_l','ローン保証引当金','jppfs_cor:ProvisionForGuaranteeForLoansCL'])
    ex_map.append(['provision_for_loss_on_disaster_c_l','災害損失引当金','jppfs_cor:ProvisionForLossOnDisasterCL'])
    ex_map.append(['provision_for_loss_on_construction_contracts_v_e_s','受注工事損失引当金','jppfs_cor:ProvisionForLossOnConstructionContractsVES'])
    ex_map.append(['provision_for_construction_warranties_for_vessel_v_e_s','船舶保証工事引当金','jppfs_cor:ProvisionForConstructionWarrantiesForVesselVES'])
    ex_map.append(['provision_for_construction_warranties_v_e_s','保証工事引当金','jppfs_cor:ProvisionForConstructionWarrantiesVES'])
    ex_map.append(['other_provision_c_l','その他の引当金','jppfs_cor:OtherProvisionCL'])
    ex_map.append(['provision_c_l','引当金','jppfs_cor:ProvisionCL'])
    ex_map.append(['accounts_payable_other','未払金','jppfs_cor:AccountsPayableOther'])
    ex_map.append(['income_taxes_payable','未払法人税等','jppfs_cor:IncomeTaxesPayable'])
    ex_map.append(['accrued_business_office_taxes','未払事業所税','jppfs_cor:AccruedBusinessOfficeTaxes'])
    ex_map.append(['accrued_consumption_taxes','未払消費税等','jppfs_cor:AccruedConsumptionTaxes'])
    ex_map.append(['accrued_taxes','未払税金','jppfs_cor:AccruedTaxes'])
    ex_map.append(['accrued_alcohol_tax','未払酒税','jppfs_cor:AccruedAlcoholTax'])
    ex_map.append(['deposits_received','預り金','jppfs_cor:DepositsReceived'])
    ex_map.append(['deposits_received_from_subsidiaries_and_affiliates','関係会社預り金','jppfs_cor:DepositsReceivedFromSubsidiariesAndAffiliates'])
    ex_map.append(['accrued_agency_commission','未払代理店手数料','jppfs_cor:AccruedAgencyCommission'])
    ex_map.append(['current_portion_of_guarantee_deposits_received','1年内返還予定の預り保証金','jppfs_cor:CurrentPortionOfGuaranteeDepositsReceived'])
    ex_map.append(['notes_payable_facilities','設備関係支払手形','jppfs_cor:NotesPayableFacilities'])
    ex_map.append(['accounts_payable_facilities','設備関係未払金','jppfs_cor:AccountsPayableFacilities'])
    ex_map.append(['notes_payable_non_operating','営業外支払手形','jppfs_cor:NotesPayableNonOperating'])
    ex_map.append(['electronically_recorded_obligations_non_operating_c_l','営業外電子記録債務','jppfs_cor:ElectronicallyRecordedObligationsNonOperatingCL'])
    ex_map.append(['short_term_bonds_payable','短期社債','jppfs_cor:ShortTermBondsPayable'])
    ex_map.append(['short_term_loans_payable','短期借入金','jppfs_cor:ShortTermLoansPayable'])
    ex_map.append(['short_term_loans_payable_to_subsidiaries_and_affiliates','関係会社短期借入金','jppfs_cor:ShortTermLoansPayableToSubsidiariesAndAffiliates'])
    ex_map.append(['commercial_papers_liabilities','コマーシャル・ペーパー','jppfs_cor:CommercialPapersLiabilities'])
    ex_map.append(['current_portion_of_bonds','1年内償還予定の社債','jppfs_cor:CurrentPortionOfBonds'])
    ex_map.append(['current_portion_of_long_term_loans_payable','1年内返済予定の長期借入金','jppfs_cor:CurrentPortionOfLongTermLoansPayable'])
    ex_map.append(['current_portion_of_long_term_loans_payable_to_subsidiaries_and_affiliates','1年内返済予定の関係会社長期借入金','jppfs_cor:CurrentPortionOfLongTermLoansPayableToSubsidiariesAndAffiliates'])
    ex_map.append(['current_portion_of_convertible_bonds','1年内償還予定の転換社債','jppfs_cor:CurrentPortionOfConvertibleBonds'])
    ex_map.append(['current_portion_of_bonds_with_subscription_rights_to_shares','1年内償還予定の新株予約権付社債','jppfs_cor:CurrentPortionOfBondsWithSubscriptionRightsToShares'])
    ex_map.append(['current_portion_of_other_noncurrent_liabilities','1年内期限到来予定のその他の固定負債','jppfs_cor:CurrentPortionOfOtherNoncurrentLiabilities'])
    ex_map.append(['suspense_receipt','仮受金','jppfs_cor:SuspenseReceipt'])
    ex_map.append(['suspense_receipt_of_consumption_taxes','仮受消費税等','jppfs_cor:SuspenseReceiptOfConsumptionTaxes'])
    ex_map.append(['accrued_bonuses','未払賞与','jppfs_cor:AccruedBonuses'])
    ex_map.append(['directors_compensation_payable','未払役員報酬','jppfs_cor:DirectorsCompensationPayable'])
    ex_map.append(['dividends_payable','未払配当金','jppfs_cor:DividendsPayable'])
    ex_map.append(['short_term_loans_payable_to_shareholders_directors_or_employees','株主、役員又は従業員からの短期借入金','jppfs_cor:ShortTermLoansPayableToShareholdersDirectorsOrEmployees'])
    ex_map.append(['deposits_received_from_shareholders_directors_or_employees','株主、役員又は従業員からの預り金','jppfs_cor:DepositsReceivedFromShareholdersDirectorsOrEmployees'])
    ex_map.append(['deposits_received_from_employees','従業員預り金','jppfs_cor:DepositsReceivedFromEmployees'])
    ex_map.append(['special_suspense_account_for_reduction_entry','圧縮未決算特別勘定','jppfs_cor:SpecialSuspenseAccountForReductionEntry'])
    ex_map.append(['accumulated_impairment_loss_on_leased_assets_c_l','リース資産減損勘定','jppfs_cor:AccumulatedImpairmentLossOnLeasedAssetsCL'])
    ex_map.append(['liabilities_from_application_of_equity_method_c_l','持分法適用に伴う負債','jppfs_cor:LiabilitiesFromApplicationOfEquityMethodCL'])
    ex_map.append(['provision_incurred_from_a_business_combination_c_l','企業結合に係る特定勘定','jppfs_cor:ProvisionIncurredFromABusinessCombinationCL'])
    ex_map.append(['stock_special_account_caused_by_restructuring_c_l','組織再編により生じた株式の特別勘定','jppfs_cor:StockSpecialAccountCausedByRestructuringCL'])
    ex_map.append(['deferred_installment_income_c_l','割賦利益繰延','jppfs_cor:DeferredInstallmentIncomeCL'])
    ex_map.append(['securities_borrowed_c_l','借入有価証券','jppfs_cor:SecuritiesBorrowedCL'])
    ex_map.append(['accounts_payable_credit_guarantee_c_l','信用保証買掛金','jppfs_cor:AccountsPayableCreditGuaranteeCL'])
    ex_map.append(['collateral_money_received_for_loan_transactions_c_l','貸借取引担保金','jppfs_cor:CollateralMoneyReceivedForLoanTransactionsCL'])
    ex_map.append(['collateral_money_received_for_securities_lent_c_l','貸付有価証券代り金','jppfs_cor:CollateralMoneyReceivedForSecuritiesLentCL'])
    ex_map.append(['other_c_l','その他','jppfs_cor:OtherCL'])
    ex_map.append(['current_liabilities','流動負債','jppfs_cor:CurrentLiabilities'])
    ex_map.append(['bonds_payable','社債','jppfs_cor:BondsPayable'])
    ex_map.append(['convertible_bonds','転換社債','jppfs_cor:ConvertibleBonds'])
    ex_map.append(['convertible_bond_type_bonds_with_subscription_rights_to_shares','転換社債型新株予約権付社債','jppfs_cor:ConvertibleBondTypeBondsWithSubscriptionRightsToShares'])
    ex_map.append(['bonds_with_subscription_rights_to_shares_n_c_l','新株予約権付社債','jppfs_cor:BondsWithSubscriptionRightsToSharesNCL'])
    ex_map.append(['long_term_loans_payable','長期借入金','jppfs_cor:LongTermLoansPayable'])
    ex_map.append(['long_term_loans_payable_to_shareholders_directors_or_employees','株主、役員又は従業員からの長期借入金','jppfs_cor:LongTermLoansPayableToShareholdersDirectorsOrEmployees'])
    ex_map.append(['long_term_loans_payable_to_subsidiaries_and_affiliates','関係会社長期借入金','jppfs_cor:LongTermLoansPayableToSubsidiariesAndAffiliates'])
    ex_map.append(['provision_for_retirement_benefits','退職給付引当金','jppfs_cor:ProvisionForRetirementBenefits'])
    ex_map.append(['provision_for_directors_retirement_benefits','役員退職慰労引当金','jppfs_cor:ProvisionForDirectorsRetirementBenefits'])
    ex_map.append(['provision_for_loss_on_guarantees','債務保証損失引当金','jppfs_cor:ProvisionForLossOnGuarantees'])
    ex_map.append(['provision_for_point_card_certificates_n_c_l','ポイント引当金','jppfs_cor:ProvisionForPointCardCertificatesNCL'])
    ex_map.append(['provision_for_special_repairs','特別修繕引当金','jppfs_cor:ProvisionForSpecialRepairs'])
    ex_map.append(['provision_for_repairs_n_c_l','修繕引当金','jppfs_cor:ProvisionForRepairsNCL'])
    ex_map.append(['provision_for_product_warranties_n_c_l','製品保証引当金','jppfs_cor:ProvisionForProductWarrantiesNCL'])
    ex_map.append(['provision_for_loss_on_liquidation_of_subsidiaries_and_affiliates_n_c_l','関係会社整理損失引当金','jppfs_cor:ProvisionForLossOnLiquidationOfSubsidiariesAndAffiliatesNCL'])
    ex_map.append(['provision_for_loss_on_business_liquidation_n_c_l','事業整理損失引当金','jppfs_cor:ProvisionForLossOnBusinessLiquidationNCL'])
    ex_map.append(['provision_for_loss_on_business_of_subsidiaries_and_affiliates_n_c_l','関係会社事業損失引当金','jppfs_cor:ProvisionForLossOnBusinessOfSubsidiariesAndAffiliatesNCL'])
    ex_map.append(['provision_for_business_structure_improvement_n_c_l','事業構造改善引当金','jppfs_cor:ProvisionForBusinessStructureImprovementNCL'])
    ex_map.append(['provision_for_environmental_measures_n_c_l','環境対策引当金','jppfs_cor:ProvisionForEnvironmentalMeasuresNCL'])
    ex_map.append(['provision_for_loss_on_litigation_n_c_l','訴訟損失引当金','jppfs_cor:ProvisionForLossOnLitigationNCL'])
    ex_map.append(['provision_for_loss_on_interest_repayment_n_c_l','利息返還損失引当金','jppfs_cor:ProvisionForLossOnInterestRepaymentNCL'])
    ex_map.append(['provision_for_contingent_loss_n_c_l','偶発損失引当金','jppfs_cor:ProvisionForContingentLossNCL'])
    ex_map.append(['provision_for_loss_on_disaster_n_c_l','災害損失引当金','jppfs_cor:ProvisionForLossOnDisasterNCL'])
    ex_map.append(['other_provision_n_c_l','その他の引当金','jppfs_cor:OtherProvisionNCL'])
    ex_map.append(['provision_n_c_l','引当金','jppfs_cor:ProvisionNCL'])
    ex_map.append(['net_defined_benefit_liability','退職給付に係る負債','jppfs_cor:NetDefinedBenefitLiability'])
    ex_map.append(['negative_goodwill','負ののれん','jppfs_cor:NegativeGoodwill'])
    ex_map.append(['lease_obligations_n_c_l','リース債務','jppfs_cor:LeaseObligationsNCL'])
    ex_map.append(['asset_retirement_obligations_n_c_l','資産除去債務','jppfs_cor:AssetRetirementObligationsNCL'])
    ex_map.append(['liabilities_related_to_right_to_operate_public_facilities_n_c_l','公共施設等運営権に係る負債','jppfs_cor:LiabilitiesRelatedToRightToOperatePublicFacilitiesNCL'])
    ex_map.append(['guarantee_deposits_received_n_c_l','受入保証金','jppfs_cor:GuaranteeDepositsReceivedNCL'])
    ex_map.append(['long_term_deposits_received','長期預り金','jppfs_cor:LongTermDepositsReceived'])
    ex_map.append(['deposits_received_from_members','会員預り金','jppfs_cor:DepositsReceivedFromMembers'])
    ex_map.append(['long_term_accounts_payable_installment_purchase','長期割賦未払金','jppfs_cor:LongTermAccountsPayableInstallmentPurchase'])
    ex_map.append(['lease_and_guarantee_deposits_received','受入敷金保証金','jppfs_cor:LeaseAndGuaranteeDepositsReceived'])
    ex_map.append(['long_term_notes_payable_facilities','長期設備関係支払手形','jppfs_cor:LongTermNotesPayableFacilities'])
    ex_map.append(['long_term_accounts_payable_facilities','長期設備関係未払金','jppfs_cor:LongTermAccountsPayableFacilities'])
    ex_map.append(['long_term_advances_received','長期前受金','jppfs_cor:LongTermAdvancesReceived'])
    ex_map.append(['long_term_deferred_contribution_for_construction','長期前受工事負担金','jppfs_cor:LongTermDeferredContributionForConstruction'])
    ex_map.append(['long_term_lease_deposited','長期預り敷金','jppfs_cor:LongTermLeaseDeposited'])
    ex_map.append(['long_term_lease_and_guarantee_deposited','長期預り敷金保証金','jppfs_cor:LongTermLeaseAndGuaranteeDeposited'])
    ex_map.append(['long_term_guarantee_deposited','長期預り保証金','jppfs_cor:LongTermGuaranteeDeposited'])
    ex_map.append(['reserve_for_contract_of_insurance','保険契約準備金','jppfs_cor:ReserveForContractOfInsurance'])
    ex_map.append(['long_term_accounts_payable_other','長期未払金','jppfs_cor:LongTermAccountsPayableOther'])
    ex_map.append(['long_term_unearned_revenue','長期前受収益','jppfs_cor:LongTermUnearnedRevenue'])
    ex_map.append(['derivatives_liabilities_n_c_l','デリバティブ債務','jppfs_cor:DerivativesLiabilitiesNCL'])
    ex_map.append(['forward_exchange_contracts_n_c_l','為替予約','jppfs_cor:ForwardExchangeContractsNCL'])
    ex_map.append(['interest_rate_swap_liabilities_n_c_l','金利スワップ負債','jppfs_cor:InterestRateSwapLiabilitiesNCL'])
    ex_map.append(['interest_rate_swap_n_c_l','金利スワップ','jppfs_cor:InterestRateSwapNCL'])
    ex_map.append(['sold_currency_option_n_c_l','売建通貨オプション','jppfs_cor:SoldCurrencyOptionNCL'])
    ex_map.append(['currency_option_n_c_l','通貨オプション','jppfs_cor:CurrencyOptionNCL'])
    ex_map.append(['option_n_c_l','オプション負債','jppfs_cor:OptionNCL'])
    ex_map.append(['accumulated_impairment_loss_on_long_term_leased_assets_n_c_l','長期リース資産減損勘定','jppfs_cor:AccumulatedImpairmentLossOnLongTermLeasedAssetsNCL'])
    ex_map.append(['deferred_tax_liabilities_n_c_l','繰延税金負債','jppfs_cor:DeferredTaxLiabilitiesNCL'])
    ex_map.append(['deferred_tax_liabilities_for_land_revaluation','再評価に係る繰延税金負債','jppfs_cor:DeferredTaxLiabilitiesForLandRevaluation'])
    ex_map.append(['liabilities_from_application_of_equity_method_n_c_l','持分法適用に伴う負債','jppfs_cor:LiabilitiesFromApplicationOfEquityMethodNCL'])
    ex_map.append(['provision_incurred_from_a_business_combination_n_c_l','企業結合に係る特定勘定','jppfs_cor:ProvisionIncurredFromABusinessCombinationNCL'])
    ex_map.append(['stock_special_account_caused_by_restructuring_n_c_l','組織再編により生じた株式の特別勘定','jppfs_cor:StockSpecialAccountCausedByRestructuringNCL'])
    ex_map.append(['other_n_c_l','その他','jppfs_cor:OtherNCL'])
    ex_map.append(['noncurrent_liabilities','固定負債','jppfs_cor:NoncurrentLiabilities'])
    ex_map.append(['reserves_under_the_special_laws1','特別法上の準備金','jppfs_cor:ReservesUnderTheSpecialLaws1'])
    ex_map.append(['reserves_under_the_special_laws2','特別法上の引当金','jppfs_cor:ReservesUnderTheSpecialLaws2'])
    ex_map.append(['liabilities','負債','jppfs_cor:Liabilities'])
    ex_map.append(['capital_stock','資本金','jppfs_cor:CapitalStock'])
    ex_map.append(['deposit_for_subscriptions_to_shares','新株式申込証拠金','jppfs_cor:DepositForSubscriptionsToShares'])
    ex_map.append(['legal_capital_surplus','資本準備金','jppfs_cor:LegalCapitalSurplus'])
    ex_map.append(['other_capital_surplus','その他資本剰余金','jppfs_cor:OtherCapitalSurplus'])
    ex_map.append(['capital_surplus','資本剰余金','jppfs_cor:CapitalSurplus'])
    ex_map.append(['legal_retained_earnings','利益準備金','jppfs_cor:LegalRetainedEarnings'])
    ex_map.append(['reserve_for_bond_sinking_fund','減債積立金','jppfs_cor:ReserveForBondSinkingFund'])
    ex_map.append(['reserve_for_interim_dividends','中間配当積立金','jppfs_cor:ReserveForInterimDividends'])
    ex_map.append(['reserve_for_dividend_equalization','配当平均積立金','jppfs_cor:ReserveForDividendEqualization'])
    ex_map.append(['reserve_for_business_expansion','事業拡張積立金','jppfs_cor:ReserveForBusinessExpansion'])
    ex_map.append(['reserve_for_private_insurance','自家保険積立金','jppfs_cor:ReserveForPrivateInsurance'])
    ex_map.append(['reserve_for_advanced_depreciation_of_noncurrent_assets','固定資産圧縮積立金','jppfs_cor:ReserveForAdvancedDepreciationOfNoncurrentAssets'])
    ex_map.append(['reserve_for_special_account_for_advanced_depreciation_of_noncurrent_assets','固定資産圧縮特別勘定積立金','jppfs_cor:ReserveForSpecialAccountForAdvancedDepreciationOfNoncurrentAssets'])
    ex_map.append(['reserve_for_special_depreciation','特別償却準備金','jppfs_cor:ReserveForSpecialDepreciation'])
    ex_map.append(['reserve_for_software_programs','プログラム等準備金','jppfs_cor:ReserveForSoftwarePrograms'])
    ex_map.append(['reserve_for_overseas_investment_loss','海外投資等損失準備金','jppfs_cor:ReserveForOverseasInvestmentLoss'])
    ex_map.append(['reserve_for_research_and_development','研究開発積立金','jppfs_cor:ReserveForResearchAndDevelopment'])
    ex_map.append(['reserve_for_dividends1','配当積立金','jppfs_cor:ReserveForDividends1'])
    ex_map.append(['reserve_for_dividends2','配当準備金','jppfs_cor:ReserveForDividends2'])
    ex_map.append(['reserve_for_dividends3','配当準備積立金','jppfs_cor:ReserveForDividends3'])
    ex_map.append(['reserve_for_dividends4','配当引当積立金','jppfs_cor:ReserveForDividends4'])
    ex_map.append(['reserve_for_retirement_allowance1','退職給与積立金','jppfs_cor:ReserveForRetirementAllowance1'])
    ex_map.append(['reserve_for_retirement_allowance2','退職積立金','jppfs_cor:ReserveForRetirementAllowance2'])
    ex_map.append(['reserve_for_retirement_allowance3','退職手当積立金','jppfs_cor:ReserveForRetirementAllowance3'])
    ex_map.append(['reserve_for_retirement_allowance4','退職慰労積立金','jppfs_cor:ReserveForRetirementAllowance4'])
    ex_map.append(['reserve_for_directors_retirement_allowance','役員退職積立金','jppfs_cor:ReserveForDirectorsRetirementAllowance'])
    ex_map.append(['reserve_for_reduction_entry1','圧縮記帳積立金','jppfs_cor:ReserveForReductionEntry1'])
    ex_map.append(['reserve_for_reduction_entry2','圧縮積立金','jppfs_cor:ReserveForReductionEntry2'])
    ex_map.append(['reserve_for_reduction_entry_of_land','土地圧縮積立金','jppfs_cor:ReserveForReductionEntryOfLand'])
    ex_map.append(['reserve_for_reduction_entry_of_buildings','建物圧縮積立金','jppfs_cor:ReserveForReductionEntryOfBuildings'])
    ex_map.append(['reserve_for_reduction_entry_of_real_estate','不動産圧縮積立金','jppfs_cor:ReserveForReductionEntryOfRealEstate'])
    ex_map.append(['reserve_for_reduction_entry_of_assets','資産圧縮積立金','jppfs_cor:ReserveForReductionEntryOfAssets'])
    ex_map.append(['reserve_for_reduction_entry_of_depreciable_assets','償却資産圧縮積立金','jppfs_cor:ReserveForReductionEntryOfDepreciableAssets'])
    ex_map.append(['reserve_for_reduction_entry_of_replaced_property','買換資産圧縮積立金','jppfs_cor:ReserveForReductionEntryOfReplacedProperty'])
    ex_map.append(['reserve_for_property_replacement','買換資産積立金','jppfs_cor:ReserveForPropertyReplacement'])
    ex_map.append(['reserve_for_special_depreciation_general','特別償却積立金','jppfs_cor:ReserveForSpecialDepreciationGeneral'])
    ex_map.append(['special_reserve','特別積立金','jppfs_cor:SpecialReserve'])
    ex_map.append(['voluntary_retained_earnings','任意積立金','jppfs_cor:VoluntaryRetainedEarnings'])
    ex_map.append(['general_reserve','別途積立金','jppfs_cor:GeneralReserve'])
    ex_map.append(['retained_earnings_brought_forward','繰越利益剰余金','jppfs_cor:RetainedEarningsBroughtForward'])
    ex_map.append(['other_retained_earnings','その他利益剰余金','jppfs_cor:OtherRetainedEarnings'])
    ex_map.append(['retained_earnings','利益剰余金','jppfs_cor:RetainedEarnings'])
    ex_map.append(['treasury_stock','自己株式','jppfs_cor:TreasuryStock'])
    ex_map.append(['deposit_for_subscriptions_to_treasury_stock','自己株式申込証拠金','jppfs_cor:DepositForSubscriptionsToTreasuryStock'])
    ex_map.append(['shareholders_equity','株主資本','jppfs_cor:ShareholdersEquity'])
    ex_map.append(['valuation_difference_on_available_for_sale_securities','その他有価証券評価差額金','jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities'])
    ex_map.append(['deferred_gains_or_losses_on_hedges','繰延ヘッジ損益','jppfs_cor:DeferredGainsOrLossesOnHedges'])
    ex_map.append(['revaluation_reserve_for_land','土地再評価差額金','jppfs_cor:RevaluationReserveForLand'])
    ex_map.append(['foreign_currency_translation_adjustment','為替換算調整勘定','jppfs_cor:ForeignCurrencyTranslationAdjustment'])
    ex_map.append(['remeasurements_of_defined_benefit_plans','退職給付に係る調整累計額','jppfs_cor:RemeasurementsOfDefinedBenefitPlans'])
    ex_map.append(['valuation_and_translation_adjustments','評価・換算差額等','jppfs_cor:ValuationAndTranslationAdjustments'])
    ex_map.append(['subscription_rights_to_shares','新株予約権','jppfs_cor:SubscriptionRightsToShares'])
    ex_map.append(['treasury_subscription_rights_to_shares','自己新株予約権','jppfs_cor:TreasurySubscriptionRightsToShares'])
    ex_map.append(['non_controlling_interests','非支配株主持分','jppfs_cor:NonControllingInterests'])
    ex_map.append(['net_assets','純資産','jppfs_cor:NetAssets'])
    ex_map.append(['liabilities_and_net_assets','負債純資産','jppfs_cor:LiabilitiesAndNetAssets'])

    return ex_map

  def read_bs(self,text):
    fields={}

    ex_map = Xbrl2BsPl.expression_map()
    for i in range(0,len(ex_map)):
      fields[ex_map[i][0]]=self.get_value(ex_map[i][1],ex_map[i][2],text)

    if(fields["notes_and_accounts_receivable_trade"]==0):
      fields["notes_and_accounts_receivable_trade"]=fields["notes_and_accounts_receivable_trade"]+self.get_value("売掛金","jppfs_cor:AccountsReceivableTrade",text)
      fields["notes_and_accounts_receivable_trade"]=fields["notes_and_accounts_receivable_trade"]+self.get_value("受取手形","jppfs_cor:NotesReceivableTrade",text)

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

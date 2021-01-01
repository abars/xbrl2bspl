# XBRL to BS and PL

Convert XBRL to Balance Sheet and Profit and Loss statement.

# Requirement

Python 2.7

# Supported File Format

XBRL of Tokyo Stock Exchange Disclosure

# Usage

```python
from xbrl2bspl import Xbrl2BsPl

path = "081220180510431993.zip"
f = open(path)
xbrl2bspl=Xbrl2BsPl()
result=xbrl2bspl.convert(f.read())
print result
```

# Output

```python
BS:
accounts_payable_other                                       : 266
accrued_consumption_taxes                                    : 62
allowance_for_doubtful_accounts_c_a                          : -5
allowance_for_doubtful_accounts_i_o_a_by_group               : -16
asset_retirement_obligations_n_c_l                           : 127
assets                                                       : 24351
buildings_and_structures_net                                 : 1880
capital_stock                                                : 2346
capital_surplus                                              : 8127
cash_and_deposits                                            : 10514
current_assets                                               : 13298
current_liabilities                                          : 2046
guarantee_deposits_i_o_a                                     : 585
income_taxes_payable                                         : 186
intangible_assets                                            : 304
investment_securities                                        : 1209
investments_and_other_assets                                 : 2132
land                                                         : 6480
liabilities                                                  : 3187
liabilities_and_net_assets                                   : 24351
long_term_accounts_payable_other                             : 167
long_term_loans_payable                                      : 50
long_term_loans_receivable                                   : 4
merchandise                                                  : 1741
net_assets                                                   : 21164
net_defined_benefit_liability                                : 175
noncurrent_assets                                            : 11053
noncurrent_liabilities                                       : 1140
notes_and_accounts_payable_trade                             : 773
notes_and_accounts_receivable_trade                          : 885
other_c_a                                                    : 120
other_c_l                                                    : 172
other_i_o_a                                                  : 243
other_n_c_l                                                  : 619
other_net_p_p_e                                              : 255
property_plant_and_equipment                                 : 8616
provision_for_bonuses                                        : 188
provision_for_directors_bonuses                              : 18
raw_materials_and_supplies                                   : 41
retained_earnings                                            : 12703
shareholders_equity                                          : 20932
short_term_loans_payable                                     : 380
treasury_stock                                               : -2244
valuation_and_translation_adjustments                        : 232
valuation_difference_on_available_for_sale_securities        : 232

PL:
average_number_of_shares                                     : 18166222
current_accumulated_duration_dividend_per_share              : 14.0
current_accumulated_duration_net_income                      : 700
current_accumulated_duration_net_income_per_share            : 38.56
current_accumulated_duration_net_sales                       : 10630
current_accumulated_duration_operation_income                : 1027
current_accumulated_duration_ordinary_income                 : 1066
current_year_duration_net_income                             : 700
current_year_duration_net_income_per_share                   : 38.56
current_year_duration_net_sales                              : 10630
current_year_duration_operation_income                       : 1027
current_year_duration_ordinary_income                        : 1066
net_income_progress                                          : 1.0
net_sales_progress                                           : 1.0
number_of_issued_and_outstanding_shares_at_the_end_of_fiscal_year_including_treasury_stock : 24771561
number_of_treasury_stock_at_the_end_of_fiscal_year           : 6716108
operation_income_progress                                    : 1.0
ordinary_income_progress                                     : 1.0

CF:
cash_and_cash_equivalents                                    : 10014
cash_dividends_paid_fin_c_f                                  : -364
collection_of_loans_receivable_inv_c_f                       : 2
decrease_increase_in_inventories_ope_c_f                     : 102
decrease_increase_in_notes_and_accounts_receivable_trade_ope_c_f : 372
depreciation_and_amortization_on_other_ope_c_f               : 8
depreciation_and_amortization_ope_c_f                        : 422
income_before_income_taxes                                   : 1040
income_taxes_paid_ope_c_f                                    : -448
increase_decrease_in_allowance_for_doubtful_accounts_ope_c_f : 6
increase_decrease_in_net_defined_benefit_liability_ope_c_f   : -4
increase_decrease_in_notes_and_accounts_payable_trade_ope_c_f : -124
increase_decrease_in_provision_for_bonuses_ope_c_f           : -60
increase_decrease_in_provision_for_directors_bonuses_ope_c_f : -7
interest_and_dividends_income_ope_c_f                        : -45
interest_and_dividends_income_received_ope_c_f_inv_c_f       : 45
interest_expenses_ope_c_f                                    : 3
interest_expenses_paid_ope_c_f_fin_c_f                       : -3
loss_on_retirement_of_noncurrent_assets_ope_c_f              : 25
net_cash_provided_by_used_in_financing_activities            : -446
net_cash_provided_by_used_in_investment_activities           : 144
net_cash_provided_by_used_in_operating_activities            : 1387
net_increase_decrease_in_cash_and_cash_equivalents           : 1085
other_net_inv_c_f                                            : -26
other_net_ope_c_f                                            : 29
payments_for_guarantee_deposits_inv_c_f                      : -32
payments_into_time_deposits_inv_c_f                          : -1500
proceeds_from_collection_of_guarantee_deposits_inv_c_f       : 29
proceeds_from_long_term_loans_payable_fin_c_f                : 50
proceeds_from_withdrawal_of_time_deposits_inv_c_f            : 2000
purchase_of_intangible_assets_inv_c_f                        : -4
purchase_of_investment_securities_inv_c_f                    : -2
purchase_of_property_plant_and_equipment_inv_c_f             : -321
purchase_of_treasury_stock_fin_c_f                           : -102
repayment_of_long_term_loans_payable_fin_c_f                 : -30
subtotal_ope_c_f                                             : 1794
```

# Example Code

python convert_xbrl.py

# Fields

http://tdnet-search.appspot.com/?mode=about

# Demo

http://tdnet-search.appspot.com/?mode=analyze

# Architecture

http://blog.livedoor.jp/abars/archives/52373311.html
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
asset_retirement_obligations_n_c_l                           : 119
assets                                                       : 23574
buildings_and_structures_net                                 : 1789
capital_stock                                                : 2346
capital_surplus                                              : 8127
cash_and_deposits                                            : 9968
current_assets                                               : 12558
current_liabilities                                          : 1686
guarantee_deposits_i_o_a                                     : 565
income_taxes_payable                                         : 46
intangible_assets                                            : 294
investment_securities                                        : 1249
investments_and_other_assets                                 : 2218
land                                                         : 6480
liabilities                                                  : 2805
liabilities_and_net_assets                                   : 23574
long_term_accounts_payable_other                             : 167
long_term_loans_payable                                      : 50
long_term_loans_receivable                                   : 3
merchandise                                                  : 1626
net_assets                                                   : 20768
net_defined_benefit_liability                                : 180
noncurrent_assets                                            : 11015
noncurrent_liabilities                                       : 1119
notes_and_accounts_payable_trade                             : 701
notes_and_accounts_receivable_trade                          : 792
other_c_a                                                    : 153
other_c_l                                                    : 411
other_i_o_a                                                  : 240
other_n_c_l                                                  : 602
other_net_p_p_e                                              : 233
property_plant_and_equipment                                 : 8503
provision_for_bonuses                                        : 136
provision_for_directors_bonuses                              : 9
raw_materials_and_supplies                                   : 22
retained_earnings                                            : 12280
shareholders_equity                                          : 20509
short_term_loans_payable                                     : 380
valuation_and_translation_adjustments                        : 259
valuation_difference_on_available_for_sale_securities        : 259

PL:
current_accumulated_duration_net_sales                       : 3872
current_year_duration_dividend_per_share                     : 7.0
current_year_duration_net_income                             : 20
current_year_duration_net_income_per_share                   : 1.11
current_year_duration_net_sales                              : 8200
current_year_duration_operation_income                       : 70
current_year_duration_ordinary_income                        : 150
net_sales_progress                                           : 0.472195121951

CF:
cash_and_cash_equivalents                                    : 9968
collection_of_loans_receivable_inv_c_f                       : 1
decrease_increase_in_inventories_ope_c_f                     : 134
decrease_increase_in_notes_and_accounts_receivable_trade_ope_c_f : 92
depreciation_and_amortization_on_other_ope_c_f               : 5
depreciation_and_amortization_ope_c_f                        : 208
increase_decrease_in_allowance_for_doubtful_accounts_ope_c_f : 3
increase_decrease_in_net_defined_benefit_liability_ope_c_f   : 4
interest_and_dividends_income_received_ope_c_f_inv_c_f       : 23
interest_expenses_ope_c_f                                    : 1
loss_on_retirement_of_noncurrent_assets_ope_c_f              : 41
net_cash_provided_by_used_in_investment_activities           : 353
proceeds_from_collection_of_guarantee_deposits_inv_c_f       : 17
proceeds_from_withdrawal_of_time_deposits_inv_c_f            : 500
```

# Example Code

python convert_xbrl.py

# Fields

http://tdnet-search.appspot.com/?mode=about

# Demo

http://tdnet-search.appspot.com/?mode=analyze

# Architecture

http://blog.livedoor.jp/abars/archives/52373311.html
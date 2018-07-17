# XBRL to BS and PL

Convert XBRL to Balance Sheet and Profit and Loss statement.

# Requirement

Python2.7

# Usgae

from xbrl2bspl import Xbrl2BsPl

path = "081220180510431993.zip"
f = open(path)
xbrl2bs=Xbrl2BsPl()
result=xbrl2bs.convert(f.read())
print result

# Output

BS:
allowance_for_doubtful_accounts_ioa_by_group                 : -133
assets                                                       : 71672
buildings_and_structures                                     : 28980
buildings_and_structures_net                                 : 11148
cash_and_deposits                                            : 10298
current_assets                                               : 22202
deferred_tax_assets_ca                                       : 380
deferred_tax_liabilities_ncl                                 : 2453
investment_securities                                        : 19687
land                                                         : 13321
liabilities                                                  : 16209
liabilities_and_net_assets                                   : 71672
net_assets                                                   : 55462
notes_and_accounts_receivable_trade                          : 7616
short_term_investment_securities                             : 200

PL:
current_accumulated_duration_dividend_per_share              : 23.0
current_accumulated_duration_net_income                      : 1971
current_accumulated_duration_net_income_per_share            : 74.7
current_accumulated_duration_net_sales                       : 33937
current_accumulated_duration_operation_income                : 2779
current_accumulated_duration_ordinary_income                 : 3187
current_year_duration_dividend_per_share                     : 0
current_year_duration_net_income                             : 1971
current_year_duration_net_income_per_share                   : 74.7
current_year_duration_net_sales                              : 33937
current_year_duration_operation_income                       : 2779
current_year_duration_ordinary_income                        : 3187
net_income_progress                                          : 1.0
net_sales_progress                                           : 1.0
next_accumulated_duration_dividend_per_share                 : 0
next_accumulated_duration_net_income                         : 0
next_accumulated_duration_net_income_per_share               : 0
next_accumulated_duration_net_sales                          : 0
next_accumulated_duration_operation_income                   : 0
next_accumulated_duration_ordinary_income                    : 0
next_year_duration_dividend_per_share                        : 23.0
next_year_duration_net_income                                : 1990
next_year_duration_net_income_per_share                      : 75.38
next_year_duration_net_sales                                 : 34810
next_year_duration_operation_income                          : 2810
next_year_duration_ordinary_income                           : 3190
operation_income_progress                                    : 1.0
ordinary_income_progress                                     : 1.0

# Example

python convert_xbrl.py

# Demo

http://tdnet-search.appspot.com/?mode=analyze

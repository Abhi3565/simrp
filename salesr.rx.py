nf = workbook.add_format({'num_format': '0'}) # all amount
text_format = workbook.add_format({'bold': True,'color': 'red', 'font_size': 16})   # heading 
bold2 = workbook.add_format({'bold': True, 'bg_color': 'black','color': 'white', 'font_size': 12})   # heading row
bold4 = workbook.add_format({'num_format': '0','bold': True, 'bg_color': 'green','color': 'yellow'})  # total month wise and catagories wise
bold5 = workbook.add_format({'num_format': '0','bold': True, 'bg_color': 'red','color': 'white'})  # final total
itype = workbook.add_format({'bold': True, 'bg_color': 'orange','color': 'black'})    # Item type
itype1 = workbook.add_format({'bold': True, 'bg_color': 'orange','color': 'white'})    # Item type1
cat = workbook.add_format({'bold': True, 'color': 'purple'})     # catagories

from datetime import datetime
import time
start_time = time.time()
todate = datetime.now().strftime('%Y-%m-%d')
  # sheet tital and dates 
sheet = workbook.add_worksheet( "Sales Report" )
sheet.write(0, 2, "Report :", text_format)
sheet.write(0, 3, "Sales Report",text_format)
sheet.write(1, 0, "Start: " + str(o.fromdate), bold)
sheet.write(1, 1, "To: " + str(todate), bold)
sheet.set_column(0, 1,25)

import datetime
import calendar
import logging
_logger = logging.getLogger(__name__)
from collections import defaultdict
import pandas as pd
from .item import ITEM_TYPE_LIST

item_name_dict = dict(ITEM_TYPE_LIST)
selected_date = o.fromdate
# Calculate the financial year start date
if selected_date.month >= 4:  # If the selected date is in April or later
    financial_year_start = datetime.datetime(selected_date.year, 4, 1)
else:
    financial_year_start = datetime.datetime(selected_date.year - 1, 4, 1)
# Calculate the financial year end date
financial_year_end = financial_year_start + pd.DateOffset(years=1) - pd.DateOffset(days=1)
all_months = pd.date_range(financial_year_start, financial_year_end, freq='MS').strftime('%b%Y').tolist()
# inv is a list of objects
inv = self.env['simrp.invoice'].search([
    ('invdate', '>=', financial_year_start),
    ('invdate', '<=', financial_year_end),
    ('invamt', '!=', 0),
    ( 'state','=','i' )
])
inv = sorted(inv, key=lambda x: x.invdate)
monthly_data = {}
monthly_totals = {}
month_order = []
overall_total = 0
itemtype_totals =  {}

for month_year in all_months:
    monthly_data[month_year] = {'item_categories': {}}
for invoice in inv:
    inv_date = invoice.invdate
    month_year = inv_date.strftime('%b%Y')
    if month_year not in monthly_data:
        monthly_data[month_year] = {'item_categories': {}}
        month_order.append(month_year)
     # item type find 
    itemtype = invoice.tempitem_.category.type
    if isinstance(itemtype, bool):
        if itemtype is False:
            itemtype = invoice.saleorder_.item_.category.type
    else:
        if isinstance(itemtype, str) and itemtype.upper() == "FALSE":
           itemtype = invoice.saleorder_.item_.category.type
    # print('itemtype',itemtype)
    itemtype_name = item_name_dict.get(itemtype, itemtype)
    print('itemtype_name',itemtype_name)
    itemtype = itemtype_name
        # item catagories find 
    itemcategory = invoice.tempitem_.category.name
    if isinstance(itemcategory, bool):
        if itemcategory is False:
            itemcategory = invoice.saleorder_.item_.category.name
    else:
        if isinstance(itemcategory, str) and itemcategory.upper() == "FALSE":
           itemcategory = invoice.saleorder_.item_.category.name    
    if itemtype not in monthly_data[month_year]['item_categories']:
        monthly_data[month_year]['item_categories'][itemtype] = defaultdict(float)
        overall_total += invoice.invamt
      # item type wise total month   
        if itemtype not in itemtype_totals:
           itemtype_totals[itemtype] = defaultdict(float)
    # fiter data dictionary with total
    monthly_data[month_year]['item_categories'][itemtype][itemcategory] += invoice.invamt
     # item type wise total month  
    itemtype_totals[itemtype][month_year] += invoice.invamt
    # month wise total
    monthly_totals[month_year] = monthly_totals.get(month_year, 0) + invoice.invamt
# first table start       ////////////////////////////////////////////////////////////////////   first   //////////////////////////////////////////////
row = 4  # starting from the second row
sheet.write(row, 1, 'itemtype',bold2)
col = 2
all_month_years = sorted(set(month for data in itemtype_totals.values() for month in data.keys()),
                        key=lambda x: (int(x[3:]), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(x[:3])))

# print(all_month_years)
for month_year in all_month_years:
    sheet.write(row, col, month_year,bold2)
    col += 1
sheet.write(row, col, 'Total',bold2)
# Write data to the sheet
row += 1  # starting from the second row
for itemtype, month_data in itemtype_totals.items():
    sheet.write(row, 1, itemtype,itype1)
    col = 2
    total_amt = 0
    for month_year in all_month_years:
        value = month_data.get(month_year, 0)  # If the value is None, use 0
        total_amt += value
        sheet.write(row, col, value,nf)
        col += 1
    sheet.write(row, col, total_amt,bold4)  # Total column
    row += 1
sheet.write(row, 1, 'Monthly Total',bold4)
grand = 0  # Initialize grand total outside the outer loop
for col in range(1, len(all_month_years) + 1):
    total_amt = 0
    for month_data in itemtype_totals.values():
        month_year = all_month_years[col - 1]  # Get the corresponding month_year
        total_amt += month_data.get(month_year, 0)
    sheet.write(row, col+1, total_amt,bold4)
    grand += total_amt  # Accumulate the total_amt for the grand total
    sheet.write(row, col+2,round(grand),bold5)
row += 4
# second table start                      ////////////////////////////////////////////////  second //////////////////////////////////////////////////////
sheet.write(row, 0, "Item Type", bold2)
sheet.write(row, 1, "Category", bold2)
month_years = list(monthly_data.keys())
unique_combinations = set()
for item_data in monthly_data.values():
    for item_type, item_categories in item_data['item_categories'].items():
        for category in item_categories.keys():
            unique_combinations.add((item_type, category))
for col, month_year in enumerate(month_years, start=2):
    sheet.write(row, col, month_year, bold2)
    sheet.set_column(row,col,15)
sheet.write(row, col+1, "Catagories Total", bold2)  
row += 1 
sheet.set_column(row,1,15)
 # same name display one by one code start
def custom_sort_key(item):
    try:
        return str(item[0])  
    except (TypeError, IndexError):
        return item  
try:
    unique_combinations = sorted(unique_combinations, key=custom_sort_key)
except Exception as e:
    print(f"Error sorting unique_combinations: {e}")
    # same name display one by one code end
item_types_written = set()  # Keep track of item_types already written
finaltotal=0
import math
for item_type, category in unique_combinations:
    if item_type not in item_types_written:
        sheet.write(row, 0, item_type, itype)
        item_types_written.add(item_type)
    sheet.write(row, 1, category, cat)
    sheet.write(row + 1, 1, "", bold4)
    total11=0
    for col, month_year in enumerate(month_years, start=2):
        amount = monthly_data.get(month_year, {}).get('item_categories', {}).get(item_type, {}).get(category, 0.0)
        sheet.write(row, col,amount, nf)
        total11 = total11+amount
    finaltotal=finaltotal + total11
    sheet.set_column(row,col + 1,25)
    sheet.write(row, col + 1, total11, bold4)
    row += 1 
for col, month_year in enumerate(month_years, start=2):
    sheet.write(row, col, monthly_totals.get(month_year, 0), bold4)
sheet.write(row, col + 1, finaltotal, bold5)
sheet.write(row, 0, "Monthly Total", bold4)
workbook.close()
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time taken: {elapsed_time} seconds")

#Open the excel file, the first sheet in the specified location

import xlrd
file_location = "C:\Users\Mohammad Navid\Documents\GitHub\Gerrymandering\abel-network-files"
workbook = xlrd.open_workbook(file_location)
sheet = workbook.sheet_by_index(0)

#find the number of rows and columns on the document

number_of_rows = sheet.nrows
number_of_columns = sheet.ncols

#take i as the number of rows and loop through the column of your desired data 

for i in range (0, number_of_rows):
    geocode = sheet.cell_value(i, 9)
    US_Total = sheet.cell_value(i, 5)
    US_Dem = sheet.cell_value(i, 7)
    US_Rep = sheet.cell_value(i, 6)
#store the info in voting data dictionary
    voting_data[i] = {geocode:{US Total:US_Total, US Dem:US_Dem, US Rep:US_Rep}}

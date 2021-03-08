import pandas as pd
import xlwt
tmp_excel=pd.read_excel('/home/john/下载/总分.xlsx')
tmp_excel=tmp_excel.sort_values('班级')
xls=xlwt.Workbook()
for group_name,group_value in tmp_excel.groupby(by=['班级']):
    sheet=xls.add_sheet(str(group_name))
    for col in range(len(tmp_excel.columns)):
        sheet.write(0, col,tmp_excel.columns[col])
    for row in range(group_value.shape[0]):
        for col in range(group_value.shape[1]):
            sheet.write(row+1,col,str(group_value.iloc[row][col]))
    sheet.header_str = bytes("("+str(group_name)+")",'utf8')
    sheet.footer_str = bytes("("+str(group_name)+")",'utf8')
xls.save('/home/john/下载/总分01.xlsx')
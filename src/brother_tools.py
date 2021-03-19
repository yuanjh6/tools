import pandas as pd
import xlwt
# python -c "import sys; print(sys.getdefaultencoding())"

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
    # sheet.set_header_str( "高三(".encode('utf-8').decode('utf-8').encode('utf-8'))
    # sheet.set_footer_str( "高三(".encode('utf-8').decode('utf-8').encode('utf-8'))

    # sheet.header_str = u"高三(".encode('utf-8').decode('utf-8').encode('utf-8') #+ str(group_name).encode('utf8') + ")".encode('utf8')
    # sheet.footer_str = u"高三(".encode('utf-8').decode('utf-8').encode('utf-8') #+ str(group_name).encode('utf8') + ")".encode('utf8')
    sheet.header_str = bytes("高三("+str(group_name)+")",encoding='utf8')
    sheet.footer_str = bytes("高三("+str(group_name)+")",encoding='utf8')
    # sheet.header_str = ("高三(" + str(group_name) + ")").encode('utf8')
    # sheet.footer_str = ("高三(" + str(group_name) + ")").encode('utf8')
    # sheet.set_header_str((u"高三("+str(group_name)+")").encode('utf8'))
    # sheet.set_footer_str((u"高三("+str(group_name)+")").encode('utf8'))
xls.save('/home/john/下载/总分01.xls')
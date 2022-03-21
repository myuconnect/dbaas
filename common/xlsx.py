#from com.mmc.common.utility import Utility
from com.mmc.common.singleton import Singleton
from datetime import datetime
import xlsxwriter

class Xlsx(object, metaclass=Singleton):
	def __init__(self):
		"""
		Color name	RGB color code
		==========================		
		black		#000000
		blue		#0000FF
		brown		#800000
		cyan		#00FFFF
		gray		#808080
		green		#008000
		lime		#00FF00
		magenta		#FF00FF
		navy		#000080
		orange		#FF6600
		pink		#FF00FF
		purple		#800080
		red			#FF0000
		silver		#C0C0C0
		white		#FFFFFF
		yellow		#FFFF00
		"""
		pass
	def genXlsx(self):

		myFileName = "P:\\app\\data\\temp.xlsx"
		myWorkBook = xlsxwriter.Workbook(myFileName)
		try:
			print(myWorkBook)
			# defualt font and size
			myWorkBook.formats[0].set_font_size(11)

			myWorkSheet = myWorkBook.add_worksheet()
			"""
			# change font size
			format = myWorkBook.add_format()
			format.set_font_size(10)
			"""
			# define format
			red = myWorkBook.add_format({'color' : 'red'})
			blue = myWorkBook.add_format({'color' : 'blue'})
			green = myWorkBook.add_format({'color' : 'green'})
			bold = myWorkBook.add_format({'bold' : True})
			header_format = myWorkBook.add_format({'bold' : True, 'font_color' : 'dark blue', 'font_size' : 24, 'align' : 'center', 'border' : True})

			cell_mrge_format = myWorkBook.add_format({'align': 'center', 'valign' : 'vcenter', 'border' : 1})

			myWorkSheet.merge_range('B2:I3',"", cell_mrge_format)
			myWorkSheet.write_string('B2', 'Mongo Audit Report - {date_range}'.format(date_range = "09/01/2019 to 09/06/2019"), header_format)

			mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'dark blue', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})			
			myWorkSheet.write_string("B4","Region :",mySubHeaderFormat)
			myWorkSheet.write_string("B5", "Start Date :",mySubHeaderFormat)
			myWorkSheet.write_string("B6", "End Date :",mySubHeaderFormat)


			column_heading_format_str = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'blue'})
			column_heading_format_date = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'blue'})
			column_heading_format_ts = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'blue'})

			myWorkSheet.set_column(8,1, 20)
			myWorkSheet.write_string('B8',"TimeStamp",column_heading_format_ts)
			myWorkSheet.set_column(8,2, 20)
			myWorkSheet.write_string('C8',"Action",column_heading_format_str)
			myWorkSheet.set_column(8,3, 30)
			myWorkSheet.write_string('D8',"Users",column_heading_format_str)
			myWorkSheet.set_column(8,4, 30)
			myWorkSheet.write_string('E8',"Roles",column_heading_format_str)
			myWorkSheet.set_column(8,5, 20)
			myWorkSheet.write_string('F8',"Parameter",column_heading_format_str)
			myWorkSheet.set_column(8,6, 20)
			myWorkSheet.write_string('G8',"Status",column_heading_format_str)
			myWorkSheet.set_column(8,7, 20)
			myWorkSheet.write_string('H8',"Closed By",column_heading_format_str)
			myWorkSheet.set_column(8,8, 20)
			myWorkSheet.write_string('I8',"Closed Date",column_heading_format_date)

			data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True })
			data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000' })
			data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True , 'num_format':'mm/dd/yyyy'})

			ts = datetime.strptime('2013-01-23 12:30:05.123','%Y-%m-%d %H:%M:%S.%f')

			for x in range(9,15):
				myWorkSheet.set_column(x,1, 25)
				myWorkSheet.write_datetime(x,1,ts,data_format_ts)
				myWorkSheet.set_column(x,2, 20)
				myWorkSheet.write_string(x,2,"shutdown",data_format_str)
				myWorkSheet.set_column(x,3, 30)
				myWorkSheet.write_string(x,3,"users: xx",data_format_str)
				myWorkSheet.set_column(x,4, 30)
				myWorkSheet.write_string(x,4,"roles : xx",data_format_str)
				myWorkSheet.set_column(x,5, 20)
				myWorkSheet.write_string(x,5,"Parameter",data_format_str)
				myWorkSheet.set_column(x,6, 20)
				myWorkSheet.write_string(x,6,"Status",data_format_str)
				myWorkSheet.set_column(x,7, 20)
				myWorkSheet.write_string(x,7,"Closed By",data_format_str)
				myWorkSheet.set_column(x,8, 20)
				myWorkSheet.write_string(x,8,"05/05/2019",data_format_date)
			
			myWorkBook.close()

		except Exception as error:
			myWorkBook.close()
		#myWorkSheet.write_string('B5')

if __name__ == "__main__":
	#test = Xlsx()
	#test.genXlsx()



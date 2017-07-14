import sys
from sets import Set
import re
import random
from collections import defaultdict

# MAXROWS = 10 # use this to limit the num of rows (-1 if no limit)
MAXROWS = -1 # use this to limit the num of rows (-1 if no limit)

# Number of total rows in month/ReductionPerMonth is
ReductionPerMonth = 5
TotalRows = 1783133
Month_count = [('01',190672),('02',146081),('03',152854),('04',142147),('05',133735),('06',141523),('07',141213),('08',144857),('09',128200),('10',154531),('11',138040),('12',169280)]
Month_name = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December'}

class attribute_selection(object):

	def __init__(self, attr_list_file, CSV_input, CSV_output):
		self.attr_list = set()
		self.index_list = set()

		self.month_map = defaultdict(int)
		for (month, count) in Month_count:
			self.month_map[month] = count

		# self.month_count = defaultdict(int)

		self.create_attr_list(attr_list_file)
		self.generate(CSV_input, CSV_output)

		# totalCount = 0
		# for month in self.month_count:
		# 	count = self.month_count[month]
		# 	totalCount = totalCount + count
		# 	print month, count
		# print 'totalCount = ', totalCount

		# for i in self.index_list:
		# 	print 'i=',i

	def create_attr_list(self, attr_list_file):
		'''
		get the attribute list from attr_list_file
		'''
		l = attr_list_file.readline()
		while l:
			line = l.strip()
			if line:
				self.attr_list.add(line)

			l = attr_list_file.readline()

	def generate(self, CSV_input, CSV_output):
		'''
		Read the first line for attribute info,
		and re-generate CSV line by line with only attributes in the list
		'''
		index = 0
		l = CSV_input.readline().strip()
		l = re.sub(r"\"[^\"]*\"", "", l)
		# this is the first line: each item is the name of attributes
		whole_attr_list = l.split(",")
		for i in range(len(whole_attr_list)):
			# check if this is valid attribute
			attr = whole_attr_list[i]
			if attr in self.attr_list:
				self.index_list.add(i)

		l = CSV_input.readline()
		current_month = ''
		month_reservoir = []
		month_row = 0
		while l:
			line = l.strip()
			line = re.sub(r"\"[^\"]*\"", "", line)
			if line:
				whole_attr_list = line.split(",")

				date = whole_attr_list[1]
				# this is "Created Date" attribute. we only need month
				# e.g., 01/01/2009 12:00 AM making it to 'January'
				date_list = date.split("/")
				month = date_list[0]
				# If new month, update new new month information and writeout
				if month != current_month:
					current_month = month
					max_month_rows = self.month_map[month]/ReductionPerMonth
					month_name = Month_name[month]
					month_row = 0
					for row in month_reservoir:
						CSV_output.write(row + "\n")
					month_reservoir = []

				# Reservoir sampling. Put required rows into array
				# For the future rows, pick with probabilty max_month_rows/month_row
				# and replace any of the rows in month_reservoir with prob 1/max_month_rows
				# In the end, we should have a uniform random distribution of max_month_rows
				# in month_reservoir. Write them all to file.

				if (len(month_reservoir) >= max_month_rows):
					should_choose = random.random()
					# month_row will be >= max_month_rows, so division will be <= 1
					if (should_choose <= float(max_month_rows)/month_row):
						replace_row = random.randint(0, max_month_rows-1)
						month_reservoir[replace_row] = self.getRow(whole_attr_list, month_name)
				else:
					month_reservoir.append(self.getRow(whole_attr_list, month_name))

				month_row += 1

			index += 1

			if MAXROWS > 0 and index > MAXROWS:
				break

			l = CSV_input.readline()

		# December's output
		for row in month_reservoir:
			CSV_output.write(row + "\n")

		print 'index = ',index

	def getRow(self, whole_attr_list, month_name):
		output_list = []
		for i in range(len(whole_attr_list)):
			# check if this is valid attribute
			if i in self.index_list:
				# general attributes
				attr = whole_attr_list[i]
				# replace 'Unspecified' as ''
				if attr == 'Unspecified':
					attr = ''
				# date is month name
				if i == 1:
					attr = month_name
				output_list.append(attr)
		return ",".join(a for a in output_list)

def usage():
	print """
	Usage:
	python generate_CSV.py <raw-CSV-file> <attr-list-file> <new-CSV-file>
	where <raw-CSV-file> is the original CSV file downloaded from website,
		<attr-list-file> is the file with the list of attributes to
		be included in new CSV file, and
		<new-CSV-file> is generated CSV file.

	For example: python generate_CSV.py ../data/311_Service_Requests_2009.csv ../data/attr_list.txt ../data/new.CSV
	"""

if __name__ == "__main__":

	if len(sys.argv)!=4: # Expect exactly three arguments
		usage()
		sys.exit(2)

	try:
		CSV_input = file(sys.argv[1],"r")
		attr_list_file = file(sys.argv[2],"r")
	except IOError:
		sys.stderr.write("ERROR: Cannot read inputfile %s or %s.\n" % (sys.argv[1], sys.argv[2]))
		sys.exit(1)

	try:
		CSV_output = file(sys.argv[3],"w")
	except IOError:
		sys.stderr.write("ERROR: Cannot write outputfile %s.\n" % (sys.argv[3]))
		sys.exit(1)

	ge = attribute_selection(attr_list_file, CSV_input, CSV_output)

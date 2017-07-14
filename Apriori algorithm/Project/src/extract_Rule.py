import sys
from sets import Set
from collections import defaultdict

def getCandidate(L_previous):
	'''
	A Priori Algorithm candidate generation
	'''
	# get the list of all the large itemsets in L_{k-1}
	L_list = []
	for (l, value) in L_previous:
		L_list.append(l)

	# for l in L_list:
	# 	print ','.join(l)

	# STEP 1. Join
	L_join = [] # the list of all the itemsets after join
	# try any pair of two itemsets in L_list
	for i in range(0, len(L_list)):
		k = len(L_list[i])+1
		for j in range(i+1, len(L_list)):

			# try if first (k-2) items in L_list[i] are in L_list[j]
			joinValid = True # keeps true if only the last item is different
			for t in range(k-2):
				itemTuple1 = L_list[i][t] # itemTuple1 = (item1, colNo1)
				itemTuple2 = L_list[j][t]
				if itemTuple1 != itemTuple2:
					joinValid = False
					break

			# try the last element, they should be in different column
			if joinValid:
				t = k-2
				(item1, colNo1) = L_list[i][t]
				(item2, colNo2) = L_list[j][t]
				if colNo1 == colNo2: # same column
					joinValid = False

			if joinValid:
				# only the last item different between L_list[i] and L_list[j]
				# keep the first k-2 items, add two last-items to joined_list
				joined_list = []
				for t in range(k-2):
					itemTuple = L_list[i][t]
					joined_list.append(itemTuple)

				# order the last items by colNo
				t = k-2
				(item1, colNo1) = L_list[i][t]
				(item2, colNo2) = L_list[j][t]
				if colNo1 < colNo2:
					joined_list.append((item1, colNo1))
					joined_list.append((item2, colNo2))
				else:
					joined_list.append((item2, colNo2))
					joined_list.append((item1, colNo1))

				# no need to sort...
				# # sort by lexicographic order
				# joined_list = sorted(joined_list)

				# it cannot be in L_join already...
				# # store this itemset if not in L_join
				# if joined_list not in L_join:
				L_join.append(joined_list)

	# print ' *** Print L_join *** '
	# print L_previous
	# print L_join

	# STEP 2. prune
	L_k = []
	for l in L_join:
		# try if any (k-1) subset is in L_{k-1}
		ifValid = True
		for i in range(len(l)):
			# new_l contains k-1 items, and sorted
			new_l = list(l)
			del new_l[i]

			# new_l should be in L_{k-1}
			if new_l not in L_list:
				ifValid = False
				break

		if ifValid:
			# this is valid candidate
			L_k.append((l,0.0))

	return L_k

def getRules(itemset):
	'''
	Generates all possible rules LHS => RHS from attributes in item set
	such that there is exactly len(itemset)-1 attribute in the LHS and exactly one in
	RHS, where LHS is a set and LHS intersect RHS is empty. All the rules of
	smaller sizes must have been generated for a smaller k.
	'''
	rules = []
	for rhs in itemset:
		lhs = list(itemset)
		lhs.remove(rhs)
		rules.append([lhs, rhs])
	return rules

class extract_Rule(object):

	def __init__(self, min_sup, min_conf, CSV_file, output_file):
		self.min_sup = min_sup
		self.min_conf = min_conf
		# store each L_k is a list of (itemset-list,sup) tuples, and
		# each itemset-list is [(item1,colNo1),...]
		self.L_dict = defaultdict(list)
		self.rule_list = [] # each rule is ([LHS], RHS, confidence, support)
		self.allRows = []

		self.nRow = 0 # num of rows
		self.maxK = 0 # largest itemset

		self.extractItemsets(CSV_file)
		self.extractRules()

		self.writeFile(output_file)

	def extractItemsets(self, CSV_file):
		'''
		A priori algorithm to extract the large itemsets
		'''
		# get L1
		self.compute_L1(CSV_file)

		# start with k=2
		k = 2
		L_previous = self.L_dict[k-1]
		while(True):
			# L_previous = self.L_dict[k-1]
			# check if L_{k-1} is empty
			if len(L_previous)<=0:
				self.maxK = k-1
				break

			# get the candidate C_k (this is a list of (itemset-list,sup) tuples)
			C_k = getCandidate(L_previous)
			L_k = []

			# print "*** L_previous and C_k ***"
			# print L_previous
			# print C_k

			# compute the support of each candidate
			for row in self.allRows:
				# try each candidate if it's contained in this row
				for i in range(len(C_k)):
					(c, value) = C_k[i]
					# c is a list which contains (k-1) items: [(item1,colNo1),...]
					ifContained = True
					for item in c:
						# one attr in c is not in this row, break
						if item not in row:
							ifContained = False
							break
					# it's contained in this row, increase the count
					if ifContained:
						value = value + 1.0
						C_k[i] = (c, value)

			# after checking all the rows, get the support
			for (c, value) in C_k:
				value = value/self.nRow
				# print c, ";", value
				if value >= self.min_sup:
					L_k.append((c,value))

			# store L_k in L_dict[k] and update L_previous
			self.L_dict[k] = list(L_k)
			L_previous = list(L_k)

			k = k + 1

		# Remove the stored rows to try and save memory. No guarantee though.
		del self.allRows

	def compute_L1(self, CSV_file):
		'''
		Get all the rows from the dataset table
		and stored in self.L_dict[0].
		Also compute the first step L1 of A priori algorithm when k=1
		'''
		C1 = defaultdict(float) # store the count of (item, colNo)
		L1 = [] # L1 is the list of k=1 large itemsets, each is a (itemset-list,sup) tuple

		L0 = [] # L0 stores all the rows [row1, row2...], each row is [(item1, colNo1),...]
		nRow = 0
		for line in open(CSV_file):
			line = line.strip()
			nRow = nRow + 1 # count the number of rows
			whole_attr_list = line.split(",")

			row = []
			for i in range(len(whole_attr_list)):
				# store this value to
				attr = whole_attr_list[i]
				# ignore empty item
				if len(attr)<=0:
					continue

				# store this item to row
				row.append((attr, i))

				# count the (attr, i) pair
				C1[(attr, i)] = C1[(attr, i)] + 1.0

			# store the row only if it's non-empty
			if len(row)>0:
				L0.append(row)

		# compute the support for each item in C1, picking large items in L1
		for (attr, i) in C1:
			value = C1[(attr, i)]/nRow
			# print attr, ";", value
			if value >= self.min_sup:
				l = [(attr, i)]
				L1.append((l, value))

		# get the number of rows in the table
		self.nRow = nRow

		# store L1 in L_dict[1]
		self.L_dict[1] = L1

		# store L0 in self.allRows
		self.allRows = L0

	def extractRules(self):
		'''
		Generates all rules for all itemsets of >=2.
		Computes confidence for all rules
		'''
		# Rule is [[LHS], RHS, confidence, support] where LHS
		# is at least of size k-1
		k = 2 # Start with item set of size 2
		while (k <= self.maxK):
			k_sets = self.L_dict[k]
			for (itemset, sup) in k_sets:
				rules = getRules(itemset)
				# Add confidence and support
				for rule in rules:
					lhs = rule[0]
					rhs = rule[1]
					# Confidence is Support(LHS U RHS)/Support(LHS)
					conf = sup/self.getSupport(lhs)
					if (conf >= self.min_conf):
						self.rule_list.append((lhs, rhs, conf, sup))
			k += 1

	def getSupport(self, itemlist):
		'''
		Finds and returns the support of the itemset using L_dict
		Itemlist must be present as a smaller itemset
		'''
		k = len(itemlist)
		k_set = self.L_dict[k]
		for (itemset, sup) in k_set:
			same = True
			for item in itemlist:
				if item not in itemset:
					same = False
					break
			if (same):
				return sup

	def writeFile(self, output_file):
		'''
		Write the large itemsets and association rules into output file
		'''
		sup = self.min_sup*100
		output_file.write("==Large itemsets (min_sup=%.0f%%)\n" % sup)
		# make all L_k into one list
		all_itemsets = []
		for k in self.L_dict:
			all_itemsets.extend(self.L_dict[k])

		# sort by support
		sorted_itemsets = sorted(all_itemsets, key=lambda x: x[1], reverse=True)
		for (l, value) in sorted_itemsets:
			item_list = []
			for (item, colNo) in l:
				item_list.append(item)

			output_file.write("["+",".join(item_list)+"], "+str(value)+"\n")

		conf = self.min_conf*100
		output_file.write("\n\n==High-confidence association rules (min_conf=%.0f%%)\n" % conf)
		sorted_rules = sorted(self.rule_list, key=lambda x: x[2], reverse=True)
		for rule in sorted_rules:
			lhs = [x[0] for x in rule[0]]
			rhs = rule[1][0]
			output_file.write("[" + ",".join(lhs) + "] => [" + rhs + "]" +
								"(Conf: %.0f%%, Supp: %.0f%%)\n" % (rule[2]*100, rule[3]*100) )
		return

def usage():
	print """
	Usage:
	python extract_Rule.py <CSV-file> <min-sup> <min-conf> <output-file>
	where <CSV-file> is INTEGRATED-DATASET file,
		<min-sup> is the value of minimun support,
		<min-conf> is the value of minimun confidence,
		<output-file> is the output of the large itemsets and rules.

	For example: python extract_Rule.py ../data/new.CSV 0.01 0.1 output.txt
	"""

#if __name__ == "__main__":

	# if len(sys.argv)!=4: # Expect exactly three arguments
	#	usage()
	#	sys.exit(2)

	# try:
	# 	CSV_input = file(sys.argv[1],"r")
	# except IOError:
	# 	sys.stderr.write("ERROR: Cannot read inputfile %s.\n" % (sys.argv[1]))
	# 	sys.exit(1)
	CSV_file = sys.argv[1]

	try:
		output_file = file(sys.argv[4], "w")
	except IOError:
		sys.stderr.write("ERROR: Cannot write outputfile %s.\n" % (sys.argv[4]))
		sys.exit(1)
	min_sup = float(sys.argv[2])
	min_conf = float(sys.argv[3])

	ex = extract_Rule(min_sup, min_conf, CSV_file, output_file)

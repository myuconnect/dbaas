with open('p:\\test.conf', newline = '') as file:
   contentsGen = csv.reader(file, delimiter=' ')
   for line in contentsGen:
      if line and not line[0].startswith("#"):
         myLines = [elem_ for elem_ in line if elem_]
         print(myLines)
# https://realpython.com/introduction-to-python-generators/

# You’ll start by reading each line from the file with a generator expression:

file_name = "techcrunch.csv"
lines = (line for line in open(file_name))

# Then, you’ll use another generator expression in concert with the previous one to split each line into a list:

list_line = (s.rstrip().split(",") for s in lines)

#Here, you created the generator list_line, which iterates through the first generator lines. This is a common pattern to use when designing generator pipelines. Next, you’ll pull the column names out of techcrunch.csv. Since the column names tend to make up the first line in a CSV file, you can grab that with a short next() call:

cols = next(list_line)

#This call to next() advances the iterator over the list_line generator one time. Put it all together, and your code should look something like this:

file_name = "techcrunch.csv"
lines = (line for line in open(file_name))
list_line = (s.rstrip().split(",") for s in lines)
cols = next(list_line)

#To sum this up, you first create a generator expression lines to yield each line in a file. Next, you iterate through that generator within the definition of another generator expression called list_line, which turns each line into a list of values. Then, you advance the iteration of list_line just once with next() to get a list of the column names from your CSV file.

#Note: Watch out for trailing newlines! This code takes advantage of .rstrip() in the list_line generator expression to make sure there are no trailing newline characters, which can be present in CSV files.

#To help you filter and perform operations on the data, you’ll create dictionaries where the keys are the column names from the CSV:

company_dicts = (dict(zip(cols, data)) for data in list_line)

#This generator expression iterates through the lists produced by list_line. Then, it uses zip() and dict() to create the dictionary as specified above. Now, you’ll use a fourth generator to filter the funding round you want and pull raisedAmt as well:

funding = (
    int(company_dict["raisedAmt"])
    for company_dict in company_dicts
    if company_dict["round"] == "a"
)

#In this code snippet, your generator expression iterates through the results of company_dicts and takes the raisedAmt for any company_dict where the round key is A.

#Remember, you aren’t iterating through all these at once in the generator expression. In fact, you aren’t iterating through anything until you actually use a for loop or a function that works on iterables, like sum(). In fact, call sum() now to iterate through the generators:

total_series_a = sum(funding)



####Putting this all together, you’ll produce the following script:


file_name = "techcrunch.csv"
lines = (line for line in open(file_name))
list_line = (s.rstrip()split(",") for s in lines)
cols = next(list_line)
company_dicts = (dict(zip(cols, data)) for data in list_line)
funding = (
    int(company_dict["raisedAmt"])
    for company_dict in company_dicts
    if company_dict["round"] == "A"
)
total_series_a = sum(funding)
print(f"Total series A fundraising: ${total_series_a}")d




#### 
def readfile(file):
  with open(file, mode = 'r', encoding='utf8', newline='\r\n') as f:
    while True:
      data = f.read()
      if not data: 
        break
      yield data

for line in readfile('METADATA_DELETE.sql'):
  print(x)
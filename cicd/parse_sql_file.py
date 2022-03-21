"""
1. get inactivated users
2. scan thru all databases
3. check if any objects owned by users
4. if yes, lock the account else drop the user



# remove comments from sql file

1. 
sqlparse.format(sql, strip_comments=True).strip()

2. 
"""
import sqlparse

sql_example = """----------------------------------------------------------------------------------------------
--                                                                                           --
------------------------------------------------------------------------------------------------
ACCEPT target_db PROMPT Enter Target Database :

-- Get fix number.
ACCEPT fix_number PROMPT Enter Fix Number :

-- Log output.
spool &fix_number&target_db


-- Start time
SELECT 'START TIME : ' || TO_CHAR(sysdate, 'DD-MON-YYYY HH24:MI:SS') FROM sys.dual;

-- Where am I
set heading off
SELECT name FROM --test v$database;
select * from global_name;

-- Who am I
set heading on
SELECT USER FROM sys.dual;

set define off
set echo on


----------------------------------------------------------------------
--   EW deletion 
----------------------------------------------------------------------
delete from mapbmw.WRT_EUD_EWUploadDetail EUD
where to_char(EUD.eud_appropriatemonth,'yyyymm') = '201906'
; 


COMMIT;


set define on
set echo off

-- End time
SELECT 'END TIME  : ' || TO_CHAR(sysdate, 'DD-MON-YYYY HH24:MI:SS') FROM sys.dual;

spool off

-- Log output files to be sent back for verification

"""

new_sql = []

for statement in sqlparse.parse(sql_example):
    new_tockens = [stm for stm in statement.tokens if not isinstance(stm, sqlparse.sql.Comment)]
    new_statement = sqlparse.sql.TokenList(new_tockens)
    print("stmt ", new_statement)
    new_sql.append(new_statement.value)
    #new_sql.append(new_statement)
    #print(dir(new_statement))

print (sqlparse.format("\n".join(new_sql)))

for stmt in statements:



3.

def _removeComments(inputFileName, outputFileName):
    input = open(inputFileName, "r")
    output = open(outputFileName, "w")
    output.write(input.readline())
    for line in input:
        if not (line.lstrip().startswith("--") or line.lstrip().startswith("--") ):
            output.write(line)
    input.close()
    output.close()

def parseSqlFile(inFileName, parsedContents):
	"""
	we need dml, ddl and dcl content from this file
	loop each line
		begin from start of file
		remove comments
		get the sql along with object name
	end loop
	return seq, object_name, sql, sql category (ddl/dml/dcl)
	[{"seq" :1 , "object" : "schema.object", "op" : "sql operation op.obj i.e. create.table(insert/update/delete/create/alter/drop/truncate/gratn/revoke/rename)",  "sql" : "sql text", "category" : "dml/ddl/dcl"}]

	"""

def removeComments(fileContents):
	myRemoveKeyWordList = ["--","/*","*/","set","accept","spool","rem","prompt"]
	# we need to identify prompt and pass the input ???
	myNewFileContents = []
	myBlockCnt = 0
	myIgnoreComment = False
	multiLineComment = False
	for line in fileContents:
		print('parsing line >>> ', line)
		# checking if line starts with create procedure/function/package body
		#myStoredObjStartKwList = ["create or replace procedure","create or replace function","create or replace package","create or replace trigger","create table","create view","create type","create materialized view"]
		myStoredObjStartKwList = ["create or replace"]
		# this is create object line, we would ignore removing comments till we find end for this create
		if isTextStartWithKW(line, myStoredObjStartKwList):
			print("found kw for creating stored obj")
			myIgnoreComment = True
		elif isTextStartWithKW(line, ["begin"]):
			print("found kw 'begin'")
			myIgnoreComment = True
			myBlockCnt = myBlockCnt + 1;
		elif isTextStartWithKW(line.replace(" ", "").lower(), ["end;"]):
			print("found kw 'end'")
			myBlockCnt = myBlockCnt - 1;
			if myBlockCnt == 0:
				myIgnoreComment = False
		#
		# checking for multi line comment where it starts with /* and does not end with */ (this is multi line comment)
		if not myIgnoreComment:
			if isTextStartWithKW(line, ["/*"]) and not(line.endswith("*/")):
				print("found multi line comment (start) outside of ignore comment")
				multiLineComment = True
			if multiLineComment and line.endswith("*/"):
				print("found multi line comment (end) outside of ignore comment")
				multiLineComment = False
		if myIgnoreComment:
			# we are ignoring comment which is part of object
			if line and myNewFileContents.append(line)
		elif not (myIgnoreComment) and not multiLineComment and not isTextStartWithKW(line, myRemoveKeyWordList):
			# this is not comment, adding to new content
			if line: myNewFileContents.append(line)
		"""
		elif not (myIgnoreComment) and not isTextStartWithKW(line, myRemoveKeyWordList) :
			# ignoreCommnet is False and we did not find this line starts with comment kw
			myNewFileContents.append(line)
		"""
		#
		print("ignore comment >>", myIgnoreComment, "block cnt >>> ", myBlockCnt, "line >>>", line, "new Content >>>" ,myNewFileContents)
	return myNewFileContents

def isTextStartWithKW(_text, myKWList):
	for keyWord in myKWList:
		if _text.lower().lstrip().replace(" ","").startswith(keyWord.lower().replace(" ","")):
			return True
	return False

def isTextEndsWithKW(_text, myKWList):
	for keyWord in myKWList:
		if _text.lower().lstrip().replace(" ","").endswith(keyWord.lower().replace(" ","")):
			return True
	return False

def getSqlType(contents):
	# checking for dml first
	if isTextStartWithKW(contents, ["insert","update","delete","merge"]):
		# this is dml
		return "dml"
	elif isTextStartWithKW(contents, ["create","alter","drop","truncate"]):
		return "ddl"
	elif isTextStartWithKW(contents, ["grant","revoke"]):
		return dcl

def getDMLObjDetail(sql):
	myPrasedContents = sql.replace("\r","").replace("\n","").lower().replace("delete from","delete").strip().split(" ")
	# returning dml type, dml object
	if myPrasedContents[0] in ["insert","merge"]:
		# only merge and isnert has into kw
		return ("dml", "table", myPrasedContents[0], myPrasedContents[2])
	elif  myPrasedContents[0] == "update":
		return ("dml", "table", myPrasedContents[0], myPrasedContents[1])
	elif  myPrasedContents[0] == "delete":
		return ("dml", "table", myPrasedContents[0], myPrasedContents[1])

def getDDLObjDetail(sql):
	myPrasedContents = sql.replace("\r","").replace("\n","").lower().replace("create or replace","create").replace("package body","package").strip().split(" ")
	# returning ddl type, ddl object
	return "".join([myPrasedContents[0]]), myPrasedContents[1], myPrasedContents[2]

def getDCLObjDetail(sql):
	myPrasedContents = sql.replace("\r","").replace("\n","").lower().strip().split(" ")
	# returning dcl type, dcl object
	return ("dcl", "", myPrasedContents[0], myPrasedContents[2])

def getObjDetail(contents):
	mySqlType = getSqlType(contents)
	if mySqlType == "dml":
		return getDMLObjDetail(contents)
	elif mySqlType == "ddl":
		return getDDLObjDetail(contents)
	elif mySqlType == "dcl":
		return getDCLObjDetail(contents)

def parseContents(contents):
	kwDML = ["insert","update","delete"]
	kwDDL = ["create","alter","drop","truncate"]
	kwDCL = ["grant","revoke"]
	kwSQL = ["insert",update]
	sqlStartLine = True
	mySql = []
	mySqlLists = []
	for line in contents:
		# adding this line to mySql
		mySql.append(line)

		if sqlStartLine:
			# this is begining of sql, retrieving sql type and overwriting value of mySql to start new sql capture
			sqlStartLine = False
			mySqlType, mySqlOp, mySqlObjType, mySqlObj = getObjDetail(line)
			isBeginFound = False
			isEndFound = False

		if mySqlType == "dml":
			if isTextEndsWithKW(sqlType, [";","/"]):
				# end of sql, would put all line in list into 1 sql
				myDMLSql = "\n".join(map(str, mySql))
				mySqlLists.append({"type" : mySqlType, "object" : mySqlObj, "objectType" : mySqlObjType, "op" : mySqlOp, "sql" : "\n".join(map(str, myDMLSql))})
				mySql = []

		elif mySqlType == "ddl":
			if ""join([mySqlObjType,".",mySqlOp]) in ["procedure.create","function.create","package.create","trigger.create"] 
				# we need a way to find the end of ddl
				if isTextStartWithKW(line,["begin"]):
					myBeginCount = myBeginCount + 1;
					# found begin, setting flag that begin is found
					isBeginFound = True
				if  isTextStartWithKW(line,["end;"]):
					myBeginCount = myBeginCount - 1;
					if myBeginCount == 0:
						isEndFound = True
				if isBeginFound and isEndFound:
					# this is end of ddl sql
					myDDLSql = "\n".join(map(str, mySql))
					mySqlLists.append({"object" : mySqlObj, "op" : mySqlOp, "sql" : "\n".join(map(str, myDDLSql))})
			else:
				# this is not procedure/function/trigger/package, we dont need to check for begin, we need ";"
				if isTextEndsWithKW(sqlType, [";","/"]):
					myDDLSql = "\n".join(map(str, mySql))
					mySqlLists.append({"object" : mySqlObj, "op" : mySqlOp, "sql" : "\n".join(map(str, myDDLSql))})
				mySql = []

		elif mySqlType == "dcl":
			if isTextEndsWithKW(sqlType, [";","/"]):
				# end of sql, would put all line in list into 1 sql
				myDCLSql = "\n".join(map(str, mySql))
				mySqlLists.append({"type" : mySqlType, "object" : mySqlObj, "objectType" : mySqlObjType, "op" : mySqlOp, "sql" : "\n".join(map(str, myDCLSql))})
				mySql = []
	return mySqlLists

###########
sql = """
REM creating table
create table temp(
  test varchar2(10)
  rem this is test
)
/

/* creating procedure */
-- today
create or replace procedure test as
 /*
 this is test
 */
 -- adding this to above line
begin
	dbms_output.put_line("1st block")
	begin
		dbms_output.put_line("1.1 block")
		begin
			dbms_output.put_line("1.1 block")
		end;
	end;
	# starting 2nd block
	begin 
		null;
	end;
		null;
	begin
		null;
	end;
end;
/
create or replace trigger as trg1
begin
  null
  # this is test
end;
/

"""
newSqlList = removeComments(sql.split("\n"))
myNewSql = "\n".join(map(str, newSqlList))
print("new sql >>> \n", myNewSql, "\n completed ...")






import itertools
import sqlparse

from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML


def is_subselect(parsed):
    if not parsed.is_group():
        return False
    for item in parsed.tokens:
        if item.ttype is DML and item.value.upper() == 'SELECT':
            return True
    return False


def extract_from_part(parsed):
    from_seen = False
    for item in parsed.tokens:
        if item.is_group():
            for x in extract_from_part(item):
                yield x
        if from_seen:
            if is_subselect(item):
                for x in extract_from_part(item):
                    yield x
            elif item.ttype is Keyword and item.value.upper() in ['ORDER', 'GROUP', 'BY', 'HAVING']:
                from_seen = False
                StopIteration
            else:
                yield item
        if item.ttype is Keyword and item.value.upper() == 'FROM':
            from_seen = True


def extract_table_identifiers(token_stream):
    for item in token_stream:
        if isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                value = identifier.value.replace('"', '').lower()
                yield value
        elif isinstance(item, Identifier):
            value = item.value.replace('"', '').lower()
            yield value


def extract_tables(sql):
    # let's handle multiple statements in one sql string
    extracted_tables = []
    statements = list(sqlparse.parse(sql))
    for statement in statements:
        if statement.get_type() != 'UNKNOWN':
            stream = extract_from_part(statement)
            extracted_tables.append(set(list(extract_table_identifiers(stream))))
    return list(itertools.chain(*extracted_tables))
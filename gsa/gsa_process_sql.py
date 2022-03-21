import csv, json, xlrd, os, smtplib, email.utils, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Password Status will categorize the content of Non Compliant/High Risk/At Risk
# sort based on Password Status
# skip when error occurs
# creat audit log and normal logging 
class Main(object):
	def __init__(self):
		print("Starting @ >>> ", time.ctime())
		self.SMTP_SERVER = "nasa1smtp.mmc.com"
		self.SUBJECT = "ACTION REQUIRED \"{riskType}\" - PASSWORD AUDIT COMPLIANCE REQUEST - Sql Server Account"
		self.DEFAULT_RECIPIENTS = ["Seshadri.Ranganathan@marsh.com", "Srinivasa.Boddu@marsh.com"]
		self.BCC_RECIPIENT = "Srinivasa.Boddu@marsh.com"
		self.SIGNATURE__ = """\
		<html>
			<body>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
				<p><span style="color: #1f497d;">NOTE : If you already have taken care of these account password resets, please reply back with the CO# or an email. This data may not reflect the RESETS that are done in the last 7 days.</span></p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
				<p><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Best Regards,</span></p>
				<p><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">&nbsp;</span></p>
				<p><strong><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Srini Boddu</span></strong><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">, Shared Services Manager for <a href="https://sharepoint.mrshmc.com/sites/ts1/gsd/GSD%20Organization%20Charts/Global%20GSD/Overview%20of%20Marsh%20IT%20Service%20Delivery%20for%20North%20America.pptx"><span style="color: #1f497d;">North America</span></a></span></p>
				<p><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Marsh | Global IT &amp; Operations | Global Service Delivery</span></p>
				<p><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">121 River Street, Hoboken, NJ, 07030, USA<br />Phone: +1 201-284-3653 | Mobile: +1 201-208-5432 | </span><span style="color: #1f497d;"><a href="mailto:srinivasa.boddu@marsh.com"><span style="font-size: 7.5pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">srinivasa.boddu@marsh.com</span></a></span></p>
				<p><u><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;"><a href="http://www.marsh.com/"><span style="color: #1f497d;">www.marsh.com</span></a></span></u></p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
			</body>
		</html>
		"""
		self.BODY_HEADER__ = """\
		<html>
			<body>
				<p>ATTN TEAM : The following accounts belonging to your group are NON COMPLIANT and will expire in <> days. Please RESET the passwords for these accounts immediately for COMPLIANCE.</p>
				<p>If for some reason, you are not able to RESET, please reach out to CISO team for getting an exception for extension. If you don&rsquo;t own these account, please reach out to Srini Boddu and Seshadri Ranganathan with the Ownership Change Request</p>
				<p>&nbsp;</p>
				<table style="width: 766.0pt; border-collapse: collapse;" width="1021">
				<tbody>
				<tr style="height: .2in;">
				<td style="width: 187.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="249">
				<p><strong><span style="color: white;">Server</span></strong></p>
				</td>
				<td style="width: 2.75in; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="264">
				<p><strong><span style="color: white;">Support Level 3</span></strong></p>
				</td>
				<td style="width: 157.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="209">
				<p><strong><span style="color: white;">server\\user</span></strong></p>
				</td>
				<td style="width: 103.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="137">
				<p><strong><span style="color: white;">Last PW Change</span></strong></p>
				</td>
				<td style="width: 121.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="161">
				<p><strong><span style="color: white;">Password Status</span></strong></p>
				</td>
				</tr>
				<tr style="height: .2in;">
			</body>
		</html>
		"""
		self.NON_COMPLIANT_BODY =  """\
		<html>
			<body>
				<p>ATTN TEAM : The following accounts belonging to your group are NON COMPLIANT. Please RESET the passwords for these accounts immediately for COMPLIANCE.</p>
				<p>If for some reason, you are not able to RESET, please reach out to CISO team for getting an exception for extension. If you don&rsquo;t own these account, please reach out to Srini Boddu and Seshadri Ranganathan with the Ownership Change Request</p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
				<p><span style="color: #1f497d;">NOTE : If you already have taken care of these account password resets, please reply back with the CO# or an email. This data may not reflect the RESETS that are done in the last 7 days.</span></p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>				
				<table style="width: 766.0pt; border-collapse: collapse;" width="1021">
					<tbody>
						<tr style="height: .2in;">
							<td style="width: 187.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="249">
								<p><strong><span style="color: white;">Server</span></strong></p>
							</td>
							<td style="width: 2.75in; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="264">
								<p><strong><span style="color: white;">Support Level 3</span></strong></p>
							</td>
							<td style="width: 157.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="209">
								<p><strong><span style="color: white;">server\\user</span></strong></p>
							</td>
							<td style="width: 103.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="137">
								<p><strong><span style="color: white;">Last PW Change</span></strong></p>
							</td>
							<td style="width: 121.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="161">
								<p><strong><span style="color: white;">Password Status</span></strong></p>
							</td>
						</tr>
						{content}
					</tbody>
				</table>
				<p>&nbsp;</p>
				<p><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Best Regards,</span></p>
				<p><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">&nbsp;</span></p>
				<p><strong><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Srini Boddu</span></strong><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">, Shared Services Manager for <a href="https://sharepoint.mrshmc.com/sites/ts1/gsd/GSD%20Organization%20Charts/Global%20GSD/Overview%20of%20Marsh%20IT%20Service%20Delivery%20for%20North%20America.pptx"><span style="color: #1f497d;">North America</span></a></span></p>
				<p><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Marsh | Global IT &amp; Operations | Global Service Delivery</span></p>
				<p><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">121 River Street, Hoboken, NJ, 07030, USA<br />Phone: +1 201-284-3653 | Mobile: +1 201-208-5432 | </span><span style="color: #1f497d;"><a href="mailto:srinivasa.boddu@marsh.com"><span style="font-size: 7.5pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">srinivasa.boddu@marsh.com</span></a></span></p>
				<p><u><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;"><a href="http://www.marsh.com/"><span style="color: #1f497d;">www.marsh.com</span></a></span></u></p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
			</body>
		</html>
		"""
		self.RISK_EMAIL_BODY = """\
		<html>
			<body>
				<p>ATTN TEAM : The following accounts belonging to your group are at {risk} and will expire in {days} days. Please RESET the passwords for these accounts immediately for COMPLIANCE.</p>
				<p>If for some reason, you are not able to RESET, please reach out to CISO team for getting an exception for extension. If you don&rsquo;t own these account, please reach out to Srini Boddu and Seshadri Ranganathan with the Ownership Change Request</p>
				<p>&nbsp;</p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
				<p><span style="color: #1f497d;">NOTE : If you already have taken care of these account password resets, please reply back with the CO# or an email. This data may not reflect the RESETS that are done in the last 7 days.</span></p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
				<table style="width: 766.0pt; border-collapse: collapse;" width="1021">
					<tbody>
						<tr style="height: .2in;">
							<td style="width: 187.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="249">
								<p><strong><span style="color: white;">Server</span></strong></p>
							</td>
							<td style="width: 2.75in; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="264">
								<p><strong><span style="color: white;">Support Level 3</span></strong></p>
							</td>
							<td style="width: 157.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="209">
								<p><strong><span style="color: white;">server\\user</span></strong></p>
							</td>
							<td style="width: 103.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="137">
								<p><strong><span style="color: white;">Last PW Change</span></strong></p>
							</td>
							<td style="width: 121.0pt; border: none; border-top: solid #31869B 1.0pt; background: #4BACC6; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="161">
								<p><strong><span style="color: white;">Password Status</span></strong></p>
							</td>
						</tr>
						{content}
					</tbody>
				</table>
				<p>&nbsp;</p>
				<p><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Best Regards,</span></p>
				<p><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">&nbsp;</span></p>
				<p><strong><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Srini Boddu</span></strong><span style="font-size: 9.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">, Shared Services Manager for <a href="https://sharepoint.mrshmc.com/sites/ts1/gsd/GSD%20Organization%20Charts/Global%20GSD/Overview%20of%20Marsh%20IT%20Service%20Delivery%20for%20North%20America.pptx"><span style="color: #1f497d;">North America</span></a></span></p>
				<p><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">Marsh | Global IT &amp; Operations | Global Service Delivery</span></p>
				<p><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">121 River Street, Hoboken, NJ, 07030, USA<br />Phone: +1 201-284-3653 | Mobile: +1 201-208-5432 | </span><span style="color: #1f497d;"><a href="mailto:srinivasa.boddu@marsh.com"><span style="font-size: 7.5pt; font-family: 'Verdana','sans-serif'; color: #1f497d;">srinivasa.boddu@marsh.com</span></a></span></p>
				<p><u><span style="font-size: 8.0pt; font-family: 'Verdana','sans-serif'; color: #1f497d;"><a href="http://www.marsh.com/"><span style="color: #1f497d;">www.marsh.com</span></a></span></u></p>
				<p><span style="color: #1f497d;">&nbsp;</span></p>
			</body>
		</html>
		"""
		self.EMAIL_BODY_CONTENT = """\
		<tr style="height: .2in;">
			<td style="width: 187.0pt; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="249">
				<p><span style="color: black;">{server}</span></p>
			</td>
			<td style="width: 2.75in; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="264">
				<p><strong><span style="color: black;">{supportLevel}</span></strong></p>
			</td>
			<td style="width: 157.0pt; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="209">
				<p><span style="color: black;">{user}</span></p>
			</td>
			<td style="width: 103.0pt; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="137">
				<p style="text-align: right;"><strong><span style="color: black;">{lastChange}</span></strong></p>
			</td>
			<td style="width: 121.0pt; padding: 0in 5.4pt 0in 5.4pt; height: .2in;" width="161">
				<p><span style="color: black;">{status}"</span></p>
			</td>
		</tr>
		"""
	def processData(self, data_, type_):
		if not data_:
			return

		myGrpData = []
		myEmptySupportData = []
		mySupportLevel = ""
		mySupportEmail = ""

		# will sort the data based on "Support Level 3"
		mySortedData = sorted(data_, key = lambda key: key["Support Level 3"], reverse = False)
		print("total {total} records found in {type}, processing >>>".format(total = str(len(mySortedData)), type = type_))

		if type_.lower() == "non-compliant":
			myEmailBody = self.NON_COMPLIANT_BODY
		else:
			myEmailBody = self.RISK_EMAIL_BODY
		
		myDays = []
		for elem in mySortedData:
			try:
				if not(elem["Support Level 3"]):
					print("Found empty 'Support Level 3' item, moving it to different container >>> ", str(elem))
					myEmptySupportData.append(elem)
					continue
				
				if not(mySupportLevel == elem["Support Level 3"]):
					if myGrpData:
						myData_ = ""
						myBody = ""
						mySupportEmailDL = ""
						print("Support Level 3 group >>> ", myGrpData[0]["Support Level 3"])
						print("Total records         >>> ",str(len(myGrpData)))
						myEmailDL = ""
						for line in myGrpData:
							if isinstance(line["Last PW Change"], float):
								myDateAsTuple = datetime(*xlrd.xldate_as_tuple(line["Last PW Change"],0))
								myLastPWChangeDate = datetime.strftime(myDateAsTuple,'%m/%d/%Y')	
							else:
								myLastPWChangeDate = line["Last PW Change"]	

							myEmailDL = line["Email DL"] # picking last email id from that group
							print("row >>>", line["Support Level 3"], ",", myEmailDL, ",", line["Email DL"], ",", line["Server"], ",", line["server\\user"], ",", line["Password Status"], ",", myLastPWChangeDate )

							# fixing emailDL issue
							#if not mySupportEmailDL:
							#	mySupportEmailDL = elem["Email DL"]

							myBody = "".join([myBody, self.EMAIL_BODY_CONTENT.format(server=line["Server"], supportLevel = line["Support Level 3"], user = line["server\\user"], lastChange = myLastPWChangeDate, status = line["Password Status"])])

						#myData_ = [myGrpData[item] for item in myGrpData]
						#print("data prepared to be sent via email >>>", myBody)
						print("")
						if myEmailDL:
							myRecepient = [myEmailDL]
						else:
							myRecepient = self.DEFAULT_RECIPIENTS

						if type_.lower() == "non-compliant":
							self.sendMail(myRecepient, self.SUBJECT.format(riskType = type_.upper()), self.NON_COMPLIANT_BODY.format(content = myBody))
						else:
							print("total num_days >>> ", str(int(min(myDays))))
							self.sendMail(myRecepient, self.SUBJECT.format(riskType = type_.upper()), self.RISK_EMAIL_BODY.format(risk = type_.upper(), days = str(int(min(myDays))), content = myBody))


						#self.sendMail(["anil.singh@marsh.com"], self.SUBJECT, self.BODY.format(content = myBody))
						myGrpData = []
						myDays = []
						#break

					mySupportLevel = elem["Support Level 3"]
					#mySupportEmail = elem["Email DL"]
					#print("need to send an email to {email} with data for support group >>> {group}".format(email = mySupportEmail, group = mySupportLevel))
				myGrpData.append(elem)
				myDays.append(elem["Date Avail"])

			except Exception as error:
				print("an error {err} occurred while sending email for group {grp} >>> {data} ".format(err = str(error), grp = elem["Support Level 3"], data = str(elem) ))


		print("Processing empty support level container ...")

		if myEmptySupportData:

			print("Found {total} empty support level group".format(total = str(len(myEmptySupportData))))
			myBody = ""
			mySupportEmailDL = ""

			for line in myEmptySupportData:
				if isinstance(line["Last PW Change"], float):
					myDateAsTuple = datetime(*xlrd.xldate_as_tuple(line["Last PW Change"],0))
					myLastPWChangeDate = datetime.strftime(myDateAsTuple,'%m/%d/%Y')	
				else:
					myLastPWChangeDate = line["Last PW Change"]	

				# addressing email DL
				if not mySupportEmailDL:
					mySupportEmailDL = line["Email DL"]

				myBody = "".join([myBody, self.EMAIL_BODY_CONTENT.format(server=line["Server"], supportLevel = "Empty Support Level", user = line["server\\user"], lastChange = myLastPWChangeDate, status = line["Password Status"])])

				print("data prepared to be sent via email >>>", myBody)
				if mySupportEmailDL:
					myRecepient = [mySupportEmailDL]
				else:
					myRecepient = self.DEFAULT_RECIPIENTS

				if type_.lower() == "non-compliant":
					self.sendMail(myRecepient, self.SUBJECT.format(riskType = type_.upper()), self.NON_COMPLIANT_BODY.format(content = myBody))
				else:
					self.sendMail(myRecepient, self.SUBJECT.format(riskType = type_.upper()), self.RISK_EMAIL_BODY.format(risk = type_.upper(), days = "nn", content = myBody))
		else:
			print("no data found in empty support level container")
	
	def main(self, fileName):
		myData = self.loadXlsFile(fileName)
		#myTempData = []
		#mySupportLevel = ""
		#mySupportEmail = ""

		print("Total records found >>>", len(myData))
		print("creating category based on Password status")
		print("data >>>", myData)
		myNonCompliantData = [data for data in myData if data["Password Status"].lower() == "non-compliant"]
		myAtRiskData = [data for data in myData if data["Password Status"].lower() == "high risk"]
		myHighRiskData = [data for data in myData if data["Password Status"].lower() == "very high risk"]

		self.processData(myNonCompliantData,"Non-compliant")
		self.processData(myAtRiskData,"HIGH Risk")
		self.processData(myHighRiskData, "VERY HIGH Risk")

	def loadXlsFile(self, xlsFileName):
		#workbook = xlrd.open_workbook('GSAPasswordList.xlsx')
		#workbook = xlrd.open_workbook('GSAPasswordList.csv', on_demand = True)
		workbook = xlrd.open_workbook(xlsFileName)
		worksheet = workbook.sheet_by_index(0)
		first_row = [] # The row where we stock the name of the column

		for col in range(worksheet.ncols):
			first_row.append( worksheet.cell_value(0,col) )
		print("columns", first_row)
		# transform the workbook to a list of dictionaries
		
		data = []
		
		for row in range(1, worksheet.nrows):
			elm = {}
			for col in range(worksheet.ncols):
				elm[first_row[col]]=worksheet.cell_value(row,col)
			data.append(elm)

		mySortedData = sorted(data, key = lambda key: key["Password Status"], reverse = False)
		print("length >>>", len(mySortedData))
		return mySortedData

	def sendMail(self, recipients, subject, body):
		# Create the message
		#pass
		print("above data will be emailed to --> ", str(recipients))

		#html
		msg = MIMEMultipart("alternative")
		myData = MIMEText(body, "html")
		#mySignature = MIMEText(self.SIGNATURE, "html")

		#msg.attach(myBody)
		msg.attach(myData)
		#msg.attach(mySignature)

		sender = email.utils.formataddr(('Author', 'srinivasa.boddu@marsh.com'))
		#recipients = ['anil.singh@marsh.com', 'Srinivasa.Boddu@marsh.com'] 
		msg['To'] = repr(recipients)
		msg['Subject'] = subject
		msg['Bcc'] = self.BCC_RECIPIENT

		server = smtplib.SMTP(self.SMTP_SERVER)
		server.set_debuglevel(True) # show communication with the server
		try:
			server.sendmail(sender, recipients, msg.as_string())
		finally:
			server.quit()

		#print("need to send an email to {email} with data for support group >>> {group}".format(email = mySupportEmail, group = mySupportLevel))

if __name__ == "__main__":
	import sys
	main = Main()

	print("executing {script} with total arguments {total}".format(script = sys.argv[0], total = len(sys.argv)))
	print("arguments >>> ", sys.argv)

	#file must be xlsx file
	main.main(sys.argv[1])




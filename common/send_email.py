# sending mail
if __name__ == "__main__":
	import email, smtplib
	from email import encoders
	from email.mime.base import MIMEBase
	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText

	smtp_server="nasa1smtp.mmc.com"
	subject = "An email with attachment from Python"
	body = "This is an email with attachment sent from Python"
	sender_email = email.utils.formataddr(('notification','nobody@marsh.com'))
	receiver_email = "anil.singh@marsh.com"
	html = """\
	<html>
		<body>
			<p>Attn: Team,<br>
				Pls see attached Mongo audit report for {date_raneg}, provide supporting doc (change order #) ?<br>
				<a href="http://www.realpython.com">Real Python</a> 
				has many great tutorials.
			</p>
		</body>
	</html>
	"""
	myBodyHeader = """\
		<p><strong>ATTN TEAM : </strong><span style="font-family: 'Calibri','sans-serif';">Pls complete following tasks for weekly &ldquo;Mongo Audit Report&rdquo;.</span></p>
		<ol>
			<li><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif';">Fill in following column details in this attached sheet </span></li>
		</ol>
		<table style="margin-left: 30.6pt; border-collapse: collapse;">
			<tbody>
				<tr>
					<td style="width: 170.6pt; border: none; border-bottom: solid white 2.25pt; background: black; padding: 0in 5.4pt 0in 5.4pt;" width="227">
						<p><strong><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Columns</span></strong></p>
					</td>
				</tr>
				<tr>
					<td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
						<p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Closed By (your network id)</span></p>
					</td>
				</tr>
				<tr>
					<td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
						<p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Closed Date (Today&rsquo;s Date)</span></p>
					</td>
				</tr>
				<tr>
					<td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
						<p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Comments </span></p>
					</td>
				</tr>
				<tr>
					<td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
						<p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Supporting Docs (Change Order #</span></p>
					</td>
				</tr>
			</tbody>
		</table>
		<ol start="2">
			<li><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif';">Send updated sheet to regional lead</span></li>
			<li><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif';">Upload &ldquo;updated sheet&rdquo; to &ldquo;Sharepoint Link&rdquo;</span></li>
		</ol>
			<p><strong><span style="font-size: 16.0pt; font-family: 'Times New Roman','serif';">&nbsp;</span></strong></p>
			<p><strong><span style="font-size: 14.0pt; font-family: 'Times New Roman','serif';">Audit Frame Work &ndash; Notification Service</span></strong></p>
	"""

	filename = "/opt/ansible/gsa_passwd/GSA_test.xlsx"  # In same directory as script

	# Open PDF file in binary mode
	with open(filename, "rb") as attachment:
		# Add file as application/octet-stream
		# Email client can usually download this automatically as attachment
		
		part = MIMEBase("application", "octet-stream")
		part.set_payload(attachment.read())

	# Encode file in ASCII characters to send by email    
	encoders.encode_base64(part)

	# Add header as key/value pair to attachment part
	part.add_header(
		"Content-Disposition",
		f"attachment; filename= {filename}",
	)

	# Add attachment to message and convert message to string
	message = MIMEMultipart()
	message["From"] = sender_email
	message["To"] = receiver_email
	message["Subject"] = subject
	message["Bcc"] = receiver_email  # Recommended for mass emails

	message.attach(part)
	message.attach(MIMEText(myBodyHeader, "html"))
	#text = message.as_string()

	#recipients = ['anil.singh@marsh.com', 'Srinivasa.Boddu@marsh.com'] 
	#msg['To'] = repr(recipients)
	#msg['Subject'] = subject
	#msg['Bcc'] = self.BCC_RECIPIENT

	server = smtplib.SMTP(smtp_server)
	server.set_debuglevel(True) # show communication with the server
	try:
		server.sendmail(sender_email, receiver_email, message.as_string())
	finally:
		server.quit()
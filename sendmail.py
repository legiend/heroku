import smtplib
from settings import *

#send email class
class SM(object):

	def __init__(self, sender, receivers, message, s_e_path, s_e_port):
		self.smtp = smtplib.SMTP(s_e_path, s_e_port)
		self.sender = sender
		self.receivers = receivers
		self.message = message

	#function which send email
	def send(self):	
		self.smtp.ehlo()	
		self.smtp.starttls()
		self.smtp.ehlo()
		self.smtp.login(smpt_email_send, smtp_email_pass)#log to google account
		self.smtp.sendmail(self.sender, self.receivers, self.message)
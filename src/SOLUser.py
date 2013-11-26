import os.path
import logging, pickle, urllib

class SOL_User:
	cookie_file = os.path.join('data', 'cookies.dat')
	username = ''
	password = ''
	
	def __init__(self, user, password):
		self.username = user
		self.password = password
		
	def makeHeaders(self):
		return  {'Content-type': 'application/x-www-form-urlencoded'}
		
	def makeBody(self):
		return urllib.urlencode({'theusername': self.username, 'thepassword': self.password, 'submit':'Login'}) 
	
	def GetHeaders(self, http, url = 'http://storiesonline.net/login'):
		
		if os.path.exists(self.cookie_file):
			logging.info('using cookie file - %s', self.cookie_file)
			f = open(self.cookie_file)
			headers = pickle.load(f)
			f.close()
		else:
			logging.info('No cookie file found - trying to login instead.')
			headers = self.makeHeaders()
			body = self.makeBody()
			
			response, content = http.request(url, 'POST', headers=headers, body=body)
			
			headers = {'Cookie': response['set-cookie']}
			f = open(self.cookie_file, "w")
			pickle.dump(headers, f)
			f.close()
			
		return headers
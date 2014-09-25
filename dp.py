# -*- coding: utf-8 -*-
import os
import StringIO
from PIL import Image, ImageDraw, ImageFont
import base64
import re
from random import randint, choice
from random import randrange
from settings import *

class dataProcessing(object):

	formFields = {
			"fam": u"Фамилия",
			"name": u"Имя",
			"login": u"Логин",
			"password": u"Пароль",
			"password2": u"Повторите пароль",
			"email": "email",
			"date": u"Дата рождения",
			"phone": u"Мобильный телефон",
			"capcha": "capcha",
			}

	regular = {
		"email": "\w+@\w+",
		"text": "\w",
		"phone": "[0-9]",
		"date": "^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$"
		}

	#generates check image
	def gen_capcha(self):
		key = ''.join( [choice('QWERTYUIOPLKJHGFDSAZXCVBNM1234567890') for i in xrange(5)] )
    
		img = Image.new('RGB', (100,30), 0xffffff)
		draw = ImageDraw.Draw(img)
	    
		for i in xrange(40):
			draw.line( [(randint(0,100),randint(0,30)),(randint(0,100),randint(0,30))] ,  randint(0, 0xffffff), 1)
	    
		font = ImageFont.truetype(img_Font_path, 32)
		draw.text( (0,0), key, 0, font)
	    
		f = StringIO.StringIO()
		img.save(f, "JPEG")
		raw = f.getvalue()
		return ["data:image/jpeg;base64," + base64.b64encode(raw), key]

	#check the data for validity
	def validate_data(self, arr, out=[]):
		dic = {}
		for el in arr.keys():
			if el not in out:
				if el in self.regular:
					res = re.search(self.regular[el], arr[el])
				else:
					res = re.search(self.regular["text"], arr[el])
				if not res:
					dic["error"] = "Incorrect field: " + self.formFields[el]#print wrong field
					return dic
		return dic

	#check does user log in or not
	def checkUser(self, request, session_store, log):
		request, sid = self.checkSession(request, session_store)
		if sid and log in request.session.keys():
			display = "log"
		else:
			display = "unlog"
		return display

	#get user information from DB
	def getUserData(self, request, session_store, redis):
		request, sid = self.checkSession(request, session_store)
		if hasattr(request, "session") and "email" in request.session:
			return redis.hgetall(request.session["email"])
		return {}

	#set user information to DB
	def setToRedis(self, data, redis):
		obj = redis.hgetall(data["email"])
		if obj:
			obj.update(data)
		else:
			obj = { "fam": data["fam"],
					"name": data["name"],
					"login": data["login"],
					"password": data["password"],
					"date": data["date"],
					"phone": data["phone"],
					"email": data["email"],
					"photo": data["photo"] if "photo" in data.keys() else "" 
			}

		redis.hmset(data["email"], obj)#save in DB user data/info

	#check cookie in session
	def checkSession(self, request, session_store):
		sid = request.cookies.get('tz_name')
		if sid is not None:
			request.session = session_store.get(sid)
		return [request, sid]

	#save changes to session
	def saveSession(self, request, session_store):
		if request.session.should_save:
			session_store.save(request.session)

	#check can user go on some page 
	def if_log(self, sid, request, l):
		isLog = False
		if sid and hasattr(request, "session"):
			isLog =  bool("email" in request.session.keys())
		return int(isLog) -int(l)#formula which determine where user can go

	#generate a unique name
	def nameGenerate(self, ext):
		name = str(randrange(10000000))+ext
		while os.path.isfile(img_path+name):#generate name before it will be unique in 'img_path'
			name = str(randrange(10000000))+ext
		return name
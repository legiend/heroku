# -*- coding: utf-8 -*-
import os
import redis
import re
import ast
import json
from random import randrange
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.utils import redirect
from werkzeug.contrib.sessions import SessionMiddleware, FilesystemSessionStore
from jinja2 import Environment, FileSystemLoader
from dp import dataProcessing
from sendmail import SM
from settings import *

class Portfolio(object):
	
	standartFields = (
		"fam", "name", "login", 
		"password", "email", "date", 
		"phone", "photo"
		)

	"""object initialization"""
	def __init__(self, config):
		self.redis = redis.Redis(config['redis_host'], config['redis_port'])
		self.template_path = os.path.join(os.path.dirname(__file__), 'templates')
		self.DP = dataProcessing()
		self.session_store = FilesystemSessionStore()
		self.dic = {} #dict for user info
		self.url_map = Map([
		    Rule('/', endpoint='index'),
		    Rule('/regestration.html', endpoint='regestration'),
		    Rule('/contacts.html', endpoint='contacts'),
		    Rule('/personal.html', endpoint='personal'),
		    Rule('/ask', endpoint='ask'),
		    Rule('/log_in', endpoint='log_in'),
		    Rule('/out', endpoint='out'),
		    Rule('/removePage', endpoint='removePage'),
		    Rule('/:any', endpoint="index")
		])

	def __call__(self, environ, start_response):
		return self.wsgi_app(environ, start_response)

	"""
		page load functions
	"""

	#main page
	def on_index(self, request):
		self.dic["title"] = u"Портфолио"
		return self.get_template("profile.html")

	#page with regestration form
	def on_regestration(self, request):
		request, sid = self.DP.checkSession(request, self.session_store)
		#check can user visit this page
		if self.DP.if_log(sid, request, False):
			return redirect('/')
		if sid is None:
			request.session = self.session_store.new()
		data = request.form

		if request.method == 'POST':
			self.dic = self.DP.validate_data(data)
			if self.redis.hgetall(data["email"]):
				self.dic["error"] = u"Такой email уже зарегестрирован"
			elif data["password"] != data["password2"] and "error" not in self.dic.keys():
				self.dic["error"] = u"Пароли не совпадают"
			elif 6 > len(data["password"]) or len(data["password"]) > 14:
				self.dic["error"] = u"Неудовлетворительная длина пароля"
			elif data["capcha"] != request.session['capcha']:
				self.dic["error"] = u"Неверно введена CAPCHA"

			self.dic.update(ast.literal_eval(json.dumps(data, separators=(',',':'))))
			
			#if TRUE save to DB
			if "error" not in self.dic.keys():
				self.DP.setToRedis(data, self.redis)
				request.session["email"] = data["email"]
				self.DP.saveSession(request, self.session_store)
				return redirect("/")
				
		image, request.session["capcha"] = self.DP.gen_capcha()#get capcha image and key

		self.dic["title"] = u"Регестрация"
		self.dic["image"] = image
		self.DP.saveSession(request, self.session_store)
		self.dic.update({"display": self.DP.checkUser(request, self.session_store, "email")})
		response = self.get_template("regestration.html")
		if sid is None:#if session not yet created
			response.set_cookie('tz_name', request.session.sid)
		return response

	#page with the ability to send email
	def on_contacts(self, request):
		self.dic["title"] = u"Контакты"
		return self.get_template("contacts.html")

	#page with personal information, wich user can change
	def on_personal(self, request):
		request, sid = self.decorator(request)
		#check can user visit this page
		if self.DP.if_log(sid, request, True):
			return redirect('/')
		if request.method == "POST":
			data = request.form
			if data["passwordcheck"] == self.dic["password"]:
				self.dic = self.DP.validate_data(data, ["password", "password2", "email"])#validate data, without fields in []
				if data["password"] != "":
					if data["password"] != data["password2"]:
						self.dic["error"] = u"Пароли не совпадают"
					elif data["password"] == data["password2"] and not re.search(self.DP.regular["text"], data["password"]):
						self.dic["error"] = u"Новый пароль не коректен"
					elif len(data["password"]) < 5 or len(data["password"]) > 15:
						self.dic["error"] = u"Пароль должен состоять из 6-14 символов"
				
				if "error" not in self.dic.keys():
					arr = {}
					if request.files["photo"].filename:
						#ext - file extension
						name, ext = os.path.splitext(request.files['photo'].filename)			
						name = self.DP.nameGenerate(ext)
						#save file to folder
						request.files['photo'].save(img_path+name)
						arr["photo"] = name
						#remove old picture
						if "photo" in self.dic.keys():
							if self.dic["photo"] != "" and os.path.isfile(img_path+self.dic["photo"]):
								os.remove(img_path+self.dic["photo"])
					#create dict for self.dic update
					for el in data.keys():
						if el in self.standartFields and data[el] != "":		
							if el == "password" and data["password"] != "":
								arr[el] = data[el]
							else:
								arr[el] = data[el]

					self.dic = self.DP.getUserData(request, self.session_store, self.redis)
					arr["email"] = self.dic["email"]
					return redirect("personal.html")
			else: 
				self.dic["error"] = u"Не верный действующий пароль"

		self.dic["title"] = u"Персональные данные"
		return self.get_template("personal.html")

	#function which send email from contscts page
	def on_ask(self, request):
		if request.method == "POST":
			#email sending object
			sm = SM(request.form["email"],
					smtp_email_where,
					"\nTheme: " + request.form["theme"] + "\n" + request.form["etext"],
					smtp_email_path,
					smtp_email_port
				)
			sm.send()
			return redirect("contacts.html")
		else:
			return redirect('/')
		
	"""
		utilits functions
	"""

	#function which allows log in account(ajax)
	def on_log_in(self, request):
		if request.method == "POST":
			if self.redis.hgetall(request.form["log_in"]):
				userData = self.redis.hgetall(request.form["log_in"])
				#if everything matches, back OK
				if request.form["password"] == userData["password"]:
					if not hasattr(request, "session"):
						request.session = self.session_store.new()
					request.session['email'] = userData["email"]
					response = Response(u"OK")
					response.set_cookie('tz_name', request.session.sid)
					self.DP.saveSession(request, self.session_store)
					return response
				else:
					return Response(u"Данные введены не верно")
			else:
				return Response(u"Данные введены не верно")
		else:
			return redirect('/')

	#function which allows log out from account
	def on_out(self, request):
		request, sid = self.DP.checkSession(request, self.session_store)
		if sid:
			self.session_store.delete(request.session)
		self.dic = {}
		response = Response()
		response.set_cookie('tz_name', '', expires=0)#remove cookie
		response.headers["Location"] = "/"
		response.headers["Cache-Control"] = "no-cache" #remove cache for FireFox
		response.status_code = 301 #redirect page
		return response
	
	#function which allow remove personal page
	def on_removePage(self, request):
		if request.method == "POST":
			response = Response()
			request, sid = self.DP.checkSession(request, self.session_store)
			if "email" in request.session:
				self.redis.delete(request.session["email"])#remove info from DB
				self.session_store.delete(request.session)#clear session
				if "photo" in self.dic.keys():# if TRUE, remove picture from folder
							if self.dic["photo"] != "":
								if os.path.isfile(img_path+self.dic["photo"]):
									os.remove(img_path+self.dic["photo"])
			response.set_cookie('tz_name', '', expires=0)#remove cookie
			return response
		else:
			return redirect('/')

	def get_template(self, template):
		jinja_env = Environment(loader=FileSystemLoader(self.template_path),
                                 autoescape=True)
		t = jinja_env.get_template(template)
		return Response(t.render(self.dic), mimetype='text/html')

	def wsgi_app(self, environ, start_response):
		request = Request(environ)
		
		self.dic = self.DP.getUserData(request, self.session_store, self.redis)#get user data from DB if he has session
		self.dic.update({"display": self.DP.checkUser(request, self.session_store, "email")})#how display header
		
		response = self.dispatch_request(request)
		return response(environ, start_response)
	
	def dispatch_request(self, request):
	    adapter = self.url_map.bind_to_environ(request.environ)
	    try:
	        endpoint, values = adapter.match()
	        return getattr(self, 'on_' + endpoint)(request, **values)
	    except HTTPException, e:
	        return getattr(self, 'on_index')(request)#redirect on main page for all links wich not in 'url_map'

	def decorator(self, request):
		return self.DP.checkSession(request, self.session_store)
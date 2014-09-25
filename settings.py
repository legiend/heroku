#run application
host = '127.0.0.1'
port = 5000
use_debugger = True
use_reloader = True

#Redis settings
redis_set = {
	"redis_host": 'localhost',
	"redis_port": 6379
	}

#static include
with_static=True


#images path
img_path = "static/images/"

#smtp email send
smpt_email_send = "legiend.r@gmail.com"
smtp_email_pass = "4444gggg4444"
smtp_email_where = "legiend@rambler.ru"
smtp_email_path = 'smtp.gmail.com'
smtp_email_port = 587


#capcha
img_Font_path = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'
# pretty printeds flask cheat sheets and quick reference
#https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/04-Database/flaskblog.py
#https://www.youtube.com/watch?v=23bpce-5s8I
#https://bootstrapious.com/p/bootstrap-sidebar
"""
pip install pysqlite3

from web_flask import db, User
user = User(username='John')
db.session.add(user)
db.session.commit()
results = User.query.all()
results[0].username

https://www.youtube.com/watch?v=8aTnmsDMldY
https://flask-login.readthedocs.io/en/latest/
https://bootstrap-flask.readthedocs.io/_/downloads/en/stable/pdf/
"""
from flask import Flask, redirect, render_template, request, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_admin import Admin
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField
from wtforms.validators import InputRequired, Email, length
#from flask_bootstrap import WebCDN

from flask_admin.contrib.sqla import ModelView
from operator import index

app = Flask(__name__)
bootstrap = Bootstrap(app)

#app.extensions['bootstrap']['cdns']['jquery'] = WebCDN(
#    '//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/'
#)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///P:\\app\\www\\audit\\login.db'
app.config['SECRET_KEY'] = 'SecreteKey'
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'lumen'


db= SQLAlchemy(app)
loginManager = LoginManager()
loginManager.init_app(app)

class Login(FlaskForm):
	#style = {'my_field': {'style': 'width: 100px font-size:100%'}}
	style = {'username': {'style': 'width: 100px'}}
	username = StringField('Network ID', validators=[InputRequired(), length(5, 10)], render_kw={"data-size" : "mini"})
	password = PasswordField('Password', validators=[InputRequired(), length(min=15, max=30)])
	remember = BooleanField('Remember me', validators=[InputRequired()])

class user(UserMixin, db.Model):
	# column must be id to userMixin to work
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(30), unique=True)

@loginManager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

@app.route('/')
def index():
	"""
	user =- User.query.fliter_by(userName='').first
	login_user(user)
	"""
	form = Login()
	return render_template('login.html', form=form)

@app.route('/login/')
@login_required
def login():
	logout_user()
	return render_template('login.html')

@app.route('/signup/')
def signup():
	return render_template('signup.html')

@app.route('/logout/')
@login_required
def logout():
	logout_user()
	return render_template('login.html')

@app.route('/home/')
@login_required
def home():
	return render_template('home.html')

if __name__ == "__main__":
	app.run(debug=True)
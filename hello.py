from flask import Flask, render_template, session, redirect, url_for,flash,abort,request
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired,Length
import json,os
from datetime import datetime 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
moment= Moment(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate= Migrate(app,db)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

#DB configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///" + os.path.join(basedir,"data.sqlite")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate= Migrate(app,db)


#web forms 
class NameForm(FlaskForm):
    name = StringField("What's your name?", validators=[DataRequired(),Length(1,20)])
    submit= SubmitField("Submit")

class SearchForm(FlaskForm):
    searchword = StringField("Search",validators=[DataRequired()])
    submit_search=SubmitField("Search")



#models
class User(db.Model):
    __tablename__ = "users"
    username = db.Column(db.String(10),unique=True)
    id = db.Column(db.Integer, primary_key=True)
    operations = db.relationship("Operation", backref="user",lazy="dynamic")
    password = db.Column(db.String(64))
 
    def __repr__(self):
        return "<User %r>" % self.username

class Operation(db.Model):
    __tablename__ = "operations"
    id = db.Column(db.Integer,primary_key=True)
    operation = db.Column(db.String(64),nullable=False,index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    def __repr__(self):
        return "<Operation %r>" % self.operation


##DRY
def activity(search_form):
    if search_form.submit_search.data and search_form.validate():
        search_word = search_form.searchword.data
        user = User.query.filter_by(username=search_word).first()
        if not user:
            abort(500)
        else: 
            operation = list(map(lambda x:x.operation, user.operations.all()))
            session["name"]=search_word
            session["operation"] = operation
            return True
            


@app.route('/',methods=["GET","POST"])
def index():
    form = NameForm()
    search_form = SearchForm()
    if form.submit.data and form.validate():
        old_name= session.get("name")
        if old_name is not None and old_name != form.name.data:
            flash("Name change has been detected!")
        session["name"]=form.name.data
        return redirect(url_for('index'))
    
    if activity(search_form):
        return redirect(url_for('user_activity'))

    # if search_form.submit_search.data and search_form.validate():
    #     search_word = search_form.searchword.data
    #     user = User.query.filter_by(username=search_word).first()
    #     if not user:
    #         abort(500)
    #     else: 
    #         print(3)
    #         operation = list(map(lambda x:x.operation, user.operations.all()))
    #         session["name"]=search_word
    #         session["operation"] = operation
    #         return redirect(url_for('user_activity')) 
    return render_template("index.html",form=form,search_form=search_form,name=session.get("name",None))

@app.route("/user_activity",methods=["GET","POST"])
def user_activity():
    search_form = SearchForm()
    if activity(search_form):
        return redirect(url_for('user_activity'))
    return render_template("user_activity.html",name=session.get("name"),operations=session.get("operation"),search_form=search_form)


@app.route('/description',methods=["GET","POST"])
def description():
    search_form = SearchForm()
    if activity(search_form):
        return redirect(url_for('user_activity'))    
    return render_template("description.html",search_form=search_form)

@app.errorhandler(404)
def page_not_found(e):
    admins=json.loads(os.environ.get("admins"))
    return render_template('404.html',admins=admins), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.shell_context_processor
def context_processor():
    return dict(db=db,User=User,Operation=Operation)
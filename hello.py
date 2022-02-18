from flask import Flask, render_template, session, redirect, url_for,flash
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


#web forms 
class NameForm(FlaskForm):
    name = StringField("What's your name?", validators=[DataRequired(),Length(1,20)])
    submit= SubmitField("Submit")

class SearchForm(FlaskForm):
    searchbar = StringField("Search",validators=[DataRequired()])
    submit=SubmitField("Search")



#models
class Role(db.Model):
    __tablename__ =  "roles"
    name = db.Column(db.String(64),unique=True)
    id = db.Column(db.Integer,primary_key=True)
    users = db.relationship("User",backref="role",lazy="dynamic")
    def __repr__(self):
        return "<Role %r>" % self.name

class User(db.Model):
    __tablename__ = "users"
    username = db.Column(db.String(64),index=True)
    rold_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    id=db.Column(db.Integer,primary_key=True)


@app.route('/',methods=["GET","POST"])
def index():
    search_form = SearchForm()
    form = NameForm()
    if form.validate_on_submit():
        old_name= session.get("name")
        if old_name is not None and old_name != form.name.data:
            flash("Name change has been detected!")
        session["name"]=form.name.data
        return redirect(url_for('index'))
    return render_template("index.html",form=form,search_form=search_form,name=session.get("name",None))

@app.route('/description')
def description():
    search_form = SearchForm()
    return render_template("description.html",search_form=search_form)

@app.errorhandler(404)
def page_not_found(e):
    admins=json.loads(os.environ.get("admins"))
    return render_template('404.html',admins=admins), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500



from app.auth.views import login
from . import main
from .. import models
from flask import render_template,session,redirect,url_for,current_app, flash, abort
from .. import db
from ..models import User
from ..email import send_email
from .forms import NameForm,SearchForm
from flask_login import login_required



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
            

@main.route('/',methods=["GET","POST"])
@login_required
def index():
    form = NameForm()
    search_form = SearchForm()
    if form.submit.data and form.validate():
        old_name= session.get("name")
        if old_name is not None and old_name != form.name.data:
            flash("Name change has been detected!")
        session["name"]=form.name.data
        return redirect(url_for('.index'))
    
    if activity(search_form):
        return redirect(url_for('.user_activity'))

    return render_template("index.html",form=form,search_form=search_form,name=session.get("name",None))

@main.route("/user_activity",methods=["GET","POST"])
@login_required
def user_activity():
    search_form = SearchForm()
    if activity(search_form):
        return redirect(url_for('.user_activity'))
    return render_template("user_activity.html",name=session.get("name"),operations=session.get("operation"),search_form=search_form)


@main.route('/description',methods=["GET","POST"])
@login_required
def description():
    search_form = SearchForm()
    if activity(search_form):
        return redirect(url_for('.user_activity'))    
    return render_template("description.html",search_form=search_form)

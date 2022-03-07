from . import main
from flask import render_template,session,redirect,url_for,current_app, flash, abort,jsonify,request
from .. import db
from ..models import Execution, Operation, Permission, User,Role
from .forms import EditProfileForm, NameForm,SearchForm,EditProfileAdminForm,OperationForm
from flask_login import login_required,current_user
from app.decorators import admin_required,permission_required
from os import getenv
import json

##DRY

@main.route('/',methods=["GET","POST"])
@login_required
def index():
    form = NameForm()
    if form.submit.data and form.validate():
        old_name= session.get("name")
        if old_name is not None and old_name != form.name.data:
            flash("Name change has been detected!")
        session["name"]=form.name.data
        return redirect(url_for('.index'))
    return render_template("index.html",form=form,name=session.get("name",None))



@main.route('/description',methods=["GET","POST"])
@login_required
@permission_required(Permission.READ)
def description():  
    return render_template("description.html")


#User profile page
@main.route("/user/<username>")
def user(username):
    user=User.query.filter_by(username=username).first_or_404()
    ops = user.operations.order_by(Operation.timestamp.desc()).all()
    return render_template("user.html",user=user,ops=ops)

@main.route("/edit-profile",methods=["GET","POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash("Your Profile has been updated")
        return redirect(url_for('.user',username=current_user.name))
    form.location.data = current_user.location
    form.about_me = current_user.about_me
    return render_template("edit_profile.html",form=form)


@main.route('/edit-profile-admin/' , methods=["GET","POST"])
@login_required
@admin_required
def edit_profile_admin():
    search=SearchForm()
    if search.validate_on_submit():
        email = search.searchword.data
        user=User.query.filter_by(email=email).first_or_404()
        return redirect(url_for(".edit_profile_admin_user",id=user.id))
    return render_template("edit_profile.html",search=search)


@main.route('/edit-profile-admin/<int:id>',methods=["GET","POST"])
@login_required
@admin_required
def edit_profile_admin_user(id):
    user=User.query.get_or_404(id)
    search=SearchForm()
    form = EditProfileAdminForm(user=user) # Pass in user instance! 
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash(f"The username has been changed to {user.username}.")
        return redirect(url_for('.edit_profile_admin'))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id #
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html',search=search, form=form)



#--------------------Operation----------------------------


@main.route('/operation',methods=["GET","POST"])
@login_required
@admin_required
def operation():
    if request.method=="POST":
        pass

    return render_template("operation.html")

@main.route('/op_call',methods=["POST"])
@login_required
@admin_required
def op_call():
    info = json.loads(getenv("SOLUTION"))
    req= request.get_json()
    
    if req["req_client"] in info.keys(): 
       # print(info.keys())
        session["solution"] = req["req_client"]
        return jsonify({"result": tuple(info[req["req_client"]].keys()),"type":"cluster"})
    if req["req_client"] in info[session["solution"]]:
        session["cluster"] = req["req_client"]
       # print(info[session["solution"]][session["cluster"]])
        return jsonify({"result":tuple(info[session["solution"]][session["cluster"]]),"type":"nodes"})
    if req["req_client"] == "form":
        return jsonify("",render_template("oper.html",form=OperationForm(solution=session["solution"])))
    
@main.route("/op_call/exec",methods=["POST"])
@login_required
@admin_required
def op_call_exec():

    if current_user.can(Permission.EXECUTE) and request.method=="POST" :
        req= request.get_json()
        #You can just put req["execution"] as it is based on number already. and its value is coerced into integer.
        op = Operation(exec_id=req["execution"],user=current_user._get_current_object(),cluster=req["cluster"])
        db.session.add(op)
        db.session.commit()
        print(request.get_json())
        return 
    return jsonify("dd")
    

@main.route("/operation/history")
@login_required
@admin_required
def ops_history():
    return render_template("operation_history.html")


@main.route("/operation/table")
@login_required
@admin_required
def ops_table():
    return {"data":[op.to_dict() for op in Operation.query]}
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

@main.route('/steps',methods=["GET","POST"])
def steps():
    SOLUTION =json.loads(getenv("SOLUTION"))
    #default
    solutions = tuple(solutions.keys())

    if request.method == "POST":
        #second step  (When solution was selected)
        clusters = SOLUTION.get(request.get_json().get('solution'))
        if clusters:
            clusters = tuple(clusters.key())
        
        #third step : list (When cluster was selected)
        nodes = SOLUTION.get(request.get_json().get("solution")).get(request.get_json().get("cluster"))
        if all((clusters,nodes)):
            print("Selected cluster has following nodes: " +",".join(ip for ip in nodes))
            return jsonify("",render_template("selection.html",nodes=nodes))
        if clusters:
            print("Selected solution has following clusters: " +",".join(cluster for cluster in clusters))
            return jsonify("",render_template("selection.html",clusters=clusters))
    return jsonify("",render_template("selection.html",solutions=solutions))
        


@main.route('/op',methods=["GET","POST"])
def op():
    if request.method=="POST":
        pass
    print("dd")
    return render_template("op.html")

@main.route('/practice',methods=["POST"])
def whatever():
    info = json.loads(getenv("SOLUTION"))
    req= request.get_json()
    
    if req["req_client"] in info.keys(): 
        print(info.keys())
        session["solution"] = req["req_client"]
        return jsonify({"result": tuple(info[req["req_client"]].keys()),"type":"cluster"})
    if req["req_client"] in info[session["solution"]]:
        session["cluster"] = req["req_client"]
        print(info[session["solution"]][session["cluster"]])
        return jsonify({"result":tuple(info[session["solution"]][session["cluster"]]),"type":"nodes"})
    return 




@main.route('/operation',methods=["GET","POST"])
@login_required
@admin_required
def operation():
    form = OperationForm()
    if current_user.can(Permission.EXECUTE) and form.validate_on_submit():
        op = Operation(exec_id=form.execution.data,user=current_user._get_current_object())
        db.session.add(op)
        db.session.commit()
        return redirect(url_for(".operation"))
    #ops = Operation.query.order_by(Operation.timestamp.desc()).all()
    return render_template("operation.html",form=form)

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
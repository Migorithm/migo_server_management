from . import main
from flask import render_template,session,redirect,url_for,current_app, flash, abort,jsonify,request
from .. import db
from ..models import Execution, Operation, Permission, User,Role
from .forms import EditProfileForm, NameForm,SearchForm,EditProfileAdminForm,OperationForm
from flask_login import login_required,current_user
from app.decorators import admin_required,permission_required
from os import getenv
import json
from app.core_features.ES import Es
from app.core_features.REDIS import Redis
from app.core_features.AGENT import Agent
from typing import IO


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
        form = OperationForm(solution=session["solution"])
        return jsonify("",render_template("oper.html",form=form))
    
@main.route("/op_call/exec",methods=["POST"])
@login_required
@admin_required
def op_call_exec():
    if current_user.can(Permission.EXECUTE) and request.method=="POST" :
        req : dict= request.get_json()
        
        #For ES 
        if req.get("solution") == "ElasticSearch":
            es = Es(req.get("nodes"),getenv("AUTH_"+req.get("cluster")))
            #For Rolling restart
            if int(req.get("execution")) == Execution.query.filter_by(name="RollingRestart",solution="ElasticSearch").first().id:
                if es.RollingRestart():
                    print("Right on")
                    #You can just put req["execution"] as its value is coerced into integer in the model.
                    op = Operation(exec_id=req["execution"],user=current_user._get_current_object(),cluster=req["cluster"])
                    db.session.add(op)
                    db.session.commit()
                    flash("Rolling Restart on '{}' has been completed!".format(req.get("cluster")))
                    return jsonify({"task":"RollingRestart"})
                else:
                    flash("Rolling Restart on cluster '{}' has failed!".format(req.get("cluster")))
                    return jsonify({"task":"RollingRestart"})
            
            #For Cluster Health Check
            if int(req.get("execution")) == Execution.query.filter_by(name="ClusterHealthCheck",solution="ElasticSearch").first().id:
                result = es.ClusterHealthCheck()
                if result in ("green","yellow","red"):
                    flash("Cluster '{}' status: {}!".format(req.get("cluster"),result))
      
                else:
                    flash("Cluster '{}' status: {}!".format(req.get("cluster"),result))
                return jsonify({"task":"ClusterHealthCheck"})
                
            #For Configuration change
            if int(req.get("execution")) == Execution.query.filter_by(name="Configuration",solution="ElasticSearch").first().id:
                ##es.Configuration() #How to process YAML file?
                form:dict = es.Configuration
                if isinstance(form,Exception):
                    flash(str(form))
                    return jsonify({"task":"Configuration"})
                else:
                    return jsonify({"task":"Configuration","data":form})
                       
        #For Redis
        if req.get("solution") == "Redis":
            redis = Redis(req.get("nodes"),getenv("AUTH_"+req.get("cluster")))
            
            #For health check
            if int(req.get("execution")) == Execution.query.filter_by(name="Ping",solution="Redis").first().id:
                green = redis.ClusterHealthCheck()
                print(green)
                if green:
                    flash("Cluster '{}' status: green!".format(req.get("cluster")))
                else:
                    flash("Cluster '{}' status: Not all nodes are up and running!".format(req.get("cluster")))
                return jsonify({"task":"ClusterHealthCheck"})
                
            
            #For rolling restart
            if int(req.get("execution")) == Execution.query.filter_by(name="RollingRestart",solution="Redis").first().id:
                success = redis.RollingRestart()
                if success:
                    print("Right on")
                    op = Operation(exec_id=req["execution"],user=current_user._get_current_object(),cluster=req["cluster"])
                    db.session.add(op)
                    db.session.commit()
                    flash("Rolling Restart on {} has been completed!".format(req.get("cluster")))
                    return jsonify({"task":"RollingRestart"})
                else:
                    flash("Rolling Restart on cluster '{}' has failed!".format(req.get("cluster")))
                    return jsonify({"task":"RollingRestart"})            
            
            #For config modification
            if int(req.get("execution"))==Execution.query.filter_by(name="Configuration",solution="Redis").first().id:
                data:dict = redis.Configuration
                if isinstance(data,Exception):
                    flash(str(data))
                    return jsonify({"task":"Configuration"})
                else:
                    return jsonify({"task":"Configuration","data":data})
        
        print(request.get_json())
        return jsonify("ee")
    return jsonify("dd")
    
    
@main.route("/op_call/config",methods=["POST"])
@login_required
@admin_required
def op_call_config():
    if current_user.can(Permission.EXECUTE) and request.method=="POST":
        req:dict = request.get_json()
        solution=req.get('solution')
        cluster=req.get("cluster")
        nodes= req.get("nodes")
        data = req.get("data")
        exec_id= req.get("execution") #for db 
        #print(req)
        
        if solution =="ElasticSearch":
            for k,v in data.items():
                if "," in v:
                    data[k] = v.split(",")
                if v.lower() =="true":
                    data[k] = True
                if v.lower() =="false":
                    data[k] =False
            es= Es(nodes,getenv("AUTH_"+cluster))
            reports = es.SetConfiguration(data)
            if reports[0]:
                op=Operation(exec_id=exec_id,user=current_user._get_current_object(),cluster=cluster)
                db.session.add(op)
                db.session.commit()
                flash("Configuration modification on {} succeeded.".format(cluster))
                return jsonify({"data":"okay"})
            else:
                flash("Configuration modification on {} failed.".format(cluster))
                for report in reports[1]:
                    flash(report)    
                
                return jsonify({"data":"not okay"})
        if solution =="Redis":
            redis = Redis(nodes,getenv("AUTH_"+cluster))
            reports= redis.SetConfiguration(data)
            if reports[0]:
                op=Operation(exec_id=exec_id, user=current_user._get_current_object(),cluster=cluster)
                db.session.add(op)
                db.session.commit()
                flash("Configuration modification on {} succeeded.".format(cluster))
                return jsonify({"data":"okay"})
            else:
                flash("Configuration modification on {} failed.".format(cluster))
                for report in reports[1]:
                    flash(report) 
                return jsonify({"data":"not okay"})
    

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


#----------------Agent synchronization -----------------------------
@main.route('/agent_sync',methods=["GET","POST"])
@login_required
@admin_required
def sync():
    """
    On agent server, it has: 
    1. status check ('/',methods=["GET"]) 
    2. sync ('/agent/command/sync',methods=["POST"] - token required)
    3. restart ('/agent/command/restart',methods=["POST"] - token required) 
    
    Todo list:
    - showing the list of clusters and 
    """
    if request.method=="POST":
        #From front
        req:dict = request.get_json()
        nodes:list = req.get("cluster")
        cluster_name:str= ""
        out_of_sync:list[str] = filter(lambda x: not Agent.sync_status(x),nodes) #status check
        

        
        #To the agents
        Agent.file_load()
        files:dict = Agent.files
        sync_success = Agent.agent_sync(out_of_sync,files)
        if not sync_success:
            print("[ERROR] Attempt to synchronize Agent application on {} failed".format(cluster_name))
        else:
            if Agent.agent_sync(out_of_sync):
                return jsonify() #success
            else:
                return jsonify() #fail
            
    return render_template("agent_sync.html")
    
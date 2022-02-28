from . import main
from flask import render_template,session,redirect,url_for,current_app, flash, abort
from .. import db
from ..models import Permission, User,Role
from .forms import EditProfileForm, NameForm,SearchForm,EditProfileAdminForm
from flask_login import login_required,current_user
from app.decorators import admin_required,permission_required



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
@permission_required(Permission.READ)
def description():
    search_form = SearchForm()
    if activity(search_form):
        return redirect(url_for('.user_activity'))    
    return render_template("description.html",search_form=search_form)


#User profile page
@main.route("/user/<username>")
def user(username):
    user=User.query.filter_by(username=username).first_or_404()

    return render_template("user.html",user=user)

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
## User Profiles

### Profile Information

*app/models.py*:
```python
import datetime
class User(UserMixin, db.Model):
    #...
    name=db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)

```
Noe that the ***datetime.utcnow*** is missing the () at the end. This is because the default argument in db.Column() can take a function as a value.<br><br>

*last_seen* field needs to be refreshed each time the user accesses the site. A method in the User class can be added to perform this update:<br><br>

*app/models.py*: refreshing a user's last visit time
```python
class User(UserMixin,db.Model):
    def ping(self):
        self.last_sessn = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
```
The ***ping()*** method must be called each time a request from a user is received. Because the ***@{blueprint}.before_app_request** handler runs before every request, it can do this easily:<br><br>

*app/auth/views.py*
```python
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.endpoint \
            and request.blueprint != "auth"\
            and request.endpoint != "static":
            return redirect_for(url_for("auth.unconfirmed"))
```

### User Profile Page
*app/main/views.py*
```python
@main.route("/user/<username>")
def user(username):
    user= User.query.filter_by(username=username).first_or_404()
    return render_template("user.html",user=user)
```
This simple route is added in the main blueprint. For a user named "john", the profile page will be at *http://localohst:5000/user/john.* An invalid username sent into this route will cause a 404 error to be returned. <br><br>

The ***user.html*** template will receive the user object as an argument. An initial version of this template is shown below:<br><br>

*app/templates/user.html*:
```html
{% extends "base.html" %}

{% block title %}Flasky - {{ user.username }}{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>{{ user.username }}</h1>
    {% if user.name or user.location %}
    <p>
        {% if user.name %}{{ user.name }}{% endif %}
        {% if user.location %}
            From <a href="http://maps.google.com/?q={{ user.location }}">{{ user.location }}</a>
        {% endif %}
    </p>
    {% endif %}
    {% if current_user.is_administrator() %}
    <p><a href="mailto:{{ user.email }}">{{ user.email }}</a></p>
    {% endif %}
    {% if user.about_me %}<p>{{ user.about_me }}</p>{% endif %}
    <p>Member since {{ moment(user.member_since).format('L') }}. Last seen {{ moment(user.last_seen).fromNow() }}.</p>
</div>
{% endblock %}
```
<br>

A few interesting implementation details: 
- The user location field is rendered as a link to Google Maps query so that clicking on it opens a map centered on the location.
- If the logged-in user is an administartor, then the email address of the user is shown, rendered as ***mailto*** link. This is useful  when an administrator is viewing the profile page of another user and needs to contact the user. 
- timestamps are rendered to the page using Flask-Moment.
<br>

Let's add profile page in navigation bar.<br>
*app/templates/base.html*
```html
{% if current_user.is_authenticated %}
<li>
    <a href="{{ url_for('main.user',username=current_user.username)}}">
        Profile
    </a>
</li>
{% endif %}
```

### Profile Editor
There are two different use cases related to editing user profiles.
- Allowing users to enter information themselves.
- Letting administrators edit the profiles of other users - not only their personal information items but also other fields in the User model to which users have NO direct access, such as ***the user role***. To meet two different requirements, two different forms will be created.<br><br>

#### User-Level Profile Editor
*app/main/forms.py*
```python
class EditProfileForm(FlaskForm):
    name = StringField("Real name", validators=[Length(0,64)])
    location = StringField("Location", validatros=[Length(0,64)])
    about_me = TextAreadField("About_me")
    submit = SubmitField("Submit")
```
Note that as all the fields in this form are optional, the length validator allows a length of zero as a minimum. Let's see the route definition that uses this form.<br><br>

*app/main/views.py*
```python
@main.route('/edit-profile',methods=["GET","POST"])
@login_required
def edit_profile():
    form = EditProfimeForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash("Your profile has been updated")
        return redirect(url_for('.user',username=current_user.name))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template("edit_profile.html",form=form)
```
The data associated with each form field is available at *form.{field-name}.data*. This is useful not only to obtain values submitted by the user, but also to provide initial values that are shown to the user for editing.<br><br>

To make it easy for users to reach this page, a direct link can be added as shown below.<br>
*app/templates/user.html* 
```html
{% if user == current_user %}
<a class="btn btn-default" href="{{ url_for('.edit_profile')}}">
    Edit Profile
</a>
{% endif %}
```
The conditional that enclosed the link will make the link appear only when users are viewing their own profiles(as it's ***user.html***).

#### Administrator-Level Profile Editor
The profile editing form for admin is more complex than the one for regular users as shown below.<br><br>

*app/main/forms.py* 
```python

from wtforms import StringField, TextAreaField, BooleanField, SelectField,SubmitField
from wtforms import ValidationError

class EditProfileAdminForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(),Length(1,64),Email()])
    username = StringField("Username",validators=[
        DataRequired(),
        Length(1,64), 
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])])
    confirmed = BooleanField("Confirmed")
    role = SelectField("Role",coerce=int)
    name = StringField("Real name",validator=[Length(0,64)])
    location = StringField("Location",validator=[Length(0,64)])
    about_me = TextAreaField("About Me")
    submit = SubmitField("Submit")

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        #SelectField requires you to list off choices 
        self.role.choices = [(role.id,role.name) for role in Role.query.order_by(Role.name).all()] 
        self.user = user
    
    def validate_email(self,field):
        if field.data  != self.user.email and \
            User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")
    
    def validate_username(self,field):
        if field.data != self.user.name and \ 
            User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already in use")
```
SelectField is WTForm’s wrapper for the < select > HTML form control, which implements a drop-down list. SelectField must have the items set in its choices attribute. <br><br>

They must be given as a list of tuples, with each tuple consisting of two values: an identifier for the item and the text to show in the control as a string. The ***choices*** list is set in the constructor(\_\_init\_\_ method). The identifier(first value of tuple) is id of each role. Because this value is integer, ***coerce=int*** argument is added so that filed values are stored as integered instead of default string values. <br><br>

***email*** and ***username*** fields were implement with regard to ensuring the new value doesn't duplicate another user's. To implement this logic, the form's constructor receives the user object as an argument which will be later used in the custom vaildation methods(validate_email and validate_username).<br><br>

The route definition is shown below.<br>
*app/main/views.py*
```python
from ..decorators import admin_required
from .forms import EditProfileForm, EditProfileAdminForm

@main.route('/edit-profile/<int:id>' , methods=["GET","POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    user=User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user) # Pass in user instance! 
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id #
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
```
Again, the ***user.id*** is given as a dynymic argument. When setting the initial value for *SelectField*, the ***rold_id*** is assigned to ***field.role.data*** because the list of tuples set in the choices attribute uses the numeric identifiers to reference each option.<br><br>

When the form is submitted, the id(role_id) is extracted from the field's data attribute and used in a query to load the selected role object by its id once again. The ***coerce=int*** argument used in the SelectedField declaration in the form ensures that the data attribute of this filed is always integer.<br><br>

To link the page, another button is added in the user profile page.<br>
*app/templates/user.html*:
```html
{% if current_user.is_administrator() %}
    <a class="btn btn-danger" href="{{ url_for('.edit_profile_admin', id=user.id) }}">
        Edit Profile [Admin]
    </a>
{% endif %}

```


### User Avatars(Optional)
You will learn how to add user avatars provided by ***Gravatar***. Gravatar associates avatar images with email addresses. The service exposes teh user's avatar through a specially crafted URL taht includes the MD5 hash of the user's email address, which can be calculated as follows:<br>
```python
>>> import hashlib
>>> hashlib.md5("migo@wemakeprice.com".encode('utf-8')).hexdigest()
'2e1f051ab0e51459dcd5020b6d1dd724'
```
<br>

The avatar URLs are then generated by appending the MD5 hash to the ***https://secure.gravatar.com/avatar/{MD5_hash}***. And then a few query string arguments can be added to configure the characteristics of the avatar image, as described below:
- s     : size
- r     : image rating. Options are "g", "pg", "r", "x"
- d     : default image generator. Options are 404 to return 404 error, "mm","imoticon","monsterid", "wavatar", "retro", "blank"
- fd    : Force the use of default avatars
<br>

For example, adding ***?d=identicon*** will generate a different default avartar that is based on geometric designs. All these options to generate avatar URLs can be added to ***User model*** as shown below.<br><br>

*app/models.py* 
```python
import hashlib
from flask import request
class User(UserMixin, db.Model):
    # ...
    def gravatar(self,size=100,default='identicon',rating='g'):
        url = "https://secure.gravatar.com/avatar'
        hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return f"{url}/{hash}?s={size}&d={default}&r={rating}"
```
Note that one of the requirements of the Gravatar service is that the email address from which the MD5 hash is obtained is normalized to contain only lowercases, so the conversion method(.lower()) is added. <br><br>

As you can imagine, gravatar() method can also be invoked from Jinja2 templates.<br>
*app/templates/user.html*:
```html
...
<img class="img-rounted profile-thumbnail" src="{{ user.gravatar(size=256) }}">
<div class="profile-header">
    ...
</div>
```
The profile-thumbnail CSS class helps with the positioning of the image on the page.<br>
Using a simmilar approach, the base templte can add a small thumbnail image of the logged-in user in the navigation bar.<br><br>

The generation of avatars requires an MD5 hash to be genereated which is a CPU-intensive operation. Since the MD5 hash for a user will remain constant for as long as the email address stays the same, it can be ***cached*** in the User model. The following shows the changes to the User model to store the MD5 hashes in the database.<br><br>

*app/models.py* 
```python
class User(UserMixin,db.Model):
    #...
    avatar_hash = db.Column(db.String(32))
    def __init__(self,**kwargs):
        #...
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
    
    def change_email(self,token):
        # ...
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True
    
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode("utf-8")).hexdigest()
    
    def gravatar(self,size=100,default="identicon", rating="g"):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
            hash = self.avatar_hash or self.gravatar_hash() #here! 
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
                url=url, hash=hash, size=size, default=default, rating=rating)

```
During the intialization of instance, the hash is stored in the new ***avatar_hash*** column. If the user updates the email address, then the hash is recalculated. The ***gravatar()*** method uses the stored has if available, or else it generates a new hash as before. 



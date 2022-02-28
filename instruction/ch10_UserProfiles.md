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
        return redirect(url_for('.user',username=cuurent_user.name))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
```

### Authentication Extensions for Flask
- Flask-Login: Management of user sessions for logged-in users
- Werkzeug: Password hashing and verification
- itsdangerous: Cryptographically secure token generation and verification

### Password Security
The key to storing user passwords securely in a database relies on not storing the password itself but a hash of it. A password hashing function takes a password as input, adds a random component to it (the salt), and then applies several ***one-way cryptographic transformations*** to it. The result is a new sequence of characters that has no resemblance to the original password, and has no known way to be trans‐ formed back into the original password.

### Then how do you verify the given password?
Password hashes can be verified in place of the real passwords because hashing functions are repeatable: given the same inputs, the result is always the same. 

### Hashing Passwords with Werkzeug
Werkzeug’s security module conveniently implements secure password hashing. This functionality is exposed with just two functions, used in the registration and verifica‐ tion phases, respectively:
- ***generate_password_hash***(password, method='pbkdf2:sha256', salt_length=8)
- ***check_password_hash***(hash, password)
    - This function takes a password hash previously stored in the database and the password entered by the user. A return value of True indicates that the user pass‐ word is correct.

```py
from werkzeug.security import generate_password_hash, check_password_hash
from flask import SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"]=\
    "sqlite:///" + os.path.join(basedir,"data.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(64),unique=True,index=True)
    role_id=db.Column(db.Integer,db.ForeignKey("roles.id"))
    def __repr__(self):
        return '<User %r>' % self.username
        
    password_hash=db.Column(db.String(128))
    
    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")
    @property.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)
    
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)
```
The password hashing function is implemented through a **write-only** property called password. The password hashing functionality is now complete and can be tested in the shell:

***flask shell***
```python
>>> u = User()
>>> u.password = 'cat'
>>> u.password
...
...
AttributeError: password is not a readable attribute
>>> u.password_hash
'pbkdf2:sha256:50000$moHwFH1B$ef1574909f9c549285e8547cad181c5e0213cfa44a4aba4349 fa830aa1fd227f'
>>> u.verify_password("cat")
True
>>> u.verify_password("dog")
False

>>> u2 = User()
>>> u2.password="cat"
>>> u2.password_hash
'pbkdf2:sha256:50000$Pfz0m0KU$27be930b7f0e0119d38e8d8a62f7f5e75c0a7db61ae16709bc aa6cfd60c44b74'
#Different from the u's passoword with the actually the same password input
```
<br>

To ensure that this functionality continues to work in the future, the preceding tests done manually can be written as unit tests that can be repeated easily.
```python
import unittest
from app.models import User
class UserModelTestCase(unittest.TestCase): 
    def test_password_setter(self):
        u = User(password = 'cat') 
        self.assertTrue(u.password_hash is not None)
    def test_no_password_getter(self):
        u = User(password = 'cat')
        with self.assertRaises(AttributeError):
            u.password
    def test_password_verification(self):
            u = User(password = 'cat') 
            self.assertTrue(u.verify_password('cat')) 
            self.assertFalse(u.verify_password('dog'))
    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat') 
        self.assertTrue(u.password_hash != u2.password_hash)
```
To run these new unit tests, use the following command:<br>
    ***$ flask test***
You can run the unit test suite like this every time you want to confirm everything is working as expected. 

## User Authentication with Flask-Login
When users log in to the application, their authenticated state has to be recorded in the user session, so that it is remembered as they navigate through different pages. ***Flask-Login*** is a small but extremely useful extension that specializes in managing this particular aspect of a user authentication system, without being tied to a specific authentication mechanism.

### Preparing the User Model for Logins
Flask-Login works closely with the application’s own User objects. To be able to work with the application’s User model, the Flask-Login extension requires it to implement a few common properties and methods. Propety/method and descriptions of it follow:
- is_authenticated  : Must be True if the user has valid login credentials or False otherwise.
- is_active         : Must be True if the user is allowed to log in or False otherwise. A False value can be used for disabled accounts
- is_anonymous      : Must always be False for regular users and True for a special user object that represents anonymous users.
- get_id()          : Must return a unique identifier for the user, encoded as a Unicode string
<br>

These properties can be implemented directly in the model class but as an easier alternative Flask-Login provides a UserMixin class that has default implementations that are appropriate for most cases:
```py
from flask_login import UserMixin
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username
```
Note that an email field was also added. In this application, users will log in with their email addresses, as they are less likely to forget those than their usernames.<br><br>

***Flask-login*** will be initialized in application factory as follows:
*app/_ _init_ _.py*
```python
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
def create_app(config_name): 
    # ...
    login_manager.init_app(app) 
    # ...
```
The login_view attribute of the LoginManager object sets the endpoint for the login page. Flask-Login will *redirect to the login page when an anonymous user tries to access a protected page.*<br><br>

Finally, Flask-Login requires the application to designate a function to be invoked when the extension needs to load a user from the database given its identifier.<br>
***app/models.py: user loader function***

```py
from . import login_manager
@login_manager.user_loader
    def load_user(user_id):
    return User.query.get(int(user_id))
```
***login_manager.user_loader*** decorator is used to register the function with Flask-Login, which will call it when it needs to retrieve information about the logged-in user. The return value of the function must be the user object, or None if the user identifier is invalid or any other error occurred.

### Protecting Routes
To protect a route so that it can only be accessed by authenticated users, Flask-Login provides a ***login_required*** decorator. An example of its usage follows:

```python
from flask_login import login_required
@app.route('/secret') 
@login_required
def secret():
    return 'Only authenticated users are allowed!'
```

When two or more decorators are added to a function, each decorator only affects those that are below it, in addition to the target function. In this example, the secret() function will be protected against unauthorized users with login_required, and then the resulting function will be registered with Flask as a route(Reversing the order will produce the wrong result).<br>
Thanks to the login_required decorator, if this route is accessed by a user who is not authenticated, Flask-Login will intercept the request and send the user to the login page instead.

### Adding  Login Form
The login form that will be presented to users has:
- Text field for the email address
- Password field 
- “remember me” checkbox 
- Submit button. 
The Flask-WTF form class that defines this form is shown below:

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField 
from wtforms.validators import DataRequired, Length, Email
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')
```

The PasswordField class represents an < input > element with type="password". The BooleanField class represents a checkbox. <br>
The email field uses the Length() and Email() validators from WTForms in addition to DataRequired(), to ensure that the user not only provides a value for this field, but that it is valid.<br>
In the template, you'll just need to render the form using Flaks-Bootstarp's wtf.quick_form() macro. <br>

### Signing Users In
The implementation of the login() view function is shown below:
```python
from flask import render_template, redirect, request, url_for, flash 
from flask_login import login_user
from . import auth
from ..models import User
from .forms import LoginForm

@auth.route('/login', methods=['GET', 'POST']) 
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data) 
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index') 
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)
```
When the request is of type GET, the view function just renders the template, which in turn displays the form. When the form is submitted in a POST request, Flask-WTF’s validate_on_submit()function validates the form variables, and then attempts to log the user in.<br><br>

If the password is valid, Flask-Login’s login_user() function is invoked to record the user as logged in for the user session. The login_user() function takes the user to log in and an optional “remember me” Boolean. 

#### Remember Me 
If the value of "remember me" set to False, user ssession will expire when browser window is closed. A value of True causes a ***long-term cookie*** to be set in the user’s browser, which Flask-Login uses to restore the user session. The optional ***REMEMBER_COOKIE_DURATION*** configuration option can be used to change the default one-year duration for the remember cookie.

#### Post/Redirect/Get pattern
POST request that submitted the login credentials ends with a redirect, but there are two possible URL destinations:
- If the login form was presented to the user to prevent unauthorized access to a protected URL the user wanted to visit, then ***Flask-Login will have saved that original URL in the next query string*** argument, which can be accessed from the request.args dictionary.
- If the next query string argument is not available, a redirect to the home page is issued instead. 
The URL in next is validated to make sure it is a relative URL, to prevent a malicious user from using this argument to redirect unsuspecting users to another site.<br><br>

***NOTE*** - On a production server, the application must be made available over secure HTTP(HTTPs), so that login credentials and user sessions are always transmitted encrypted.

#### Login template
```html
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}
{% block title %}Flasky - Login{% endblock %}
{% block page_content %}
<div class="page-header"> 
    <h1>Login</h1>
</div>
<div class="col-md-4">
    {{ wtf.quick_form(form) }}
</div>
{% endblock %}
```

### Signing Users Out
*app/auth/views.py: logout route*
```python
from flask_login import logout_user, login_required 
@auth.route('/logout')
@login_required
def logout(): 
    logout_user()
    flash('You have been logged out.') 
    return redirect(url_for('main.index'))
```
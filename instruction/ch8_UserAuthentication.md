## User Authentication

### Authentication Extensions for Flask
- Flask-Login: Management of user sessions for logged-in users
- Werkzeug: Password hashing and verification
- itsdangerous: Cryptographically secure token generation and verification

#### Password Security
The key to storing user passwords securely in a database relies on not storing the password itself but a hash of it.<br> 
What a password hashing function does is: 
- take password as input
- add a random component to it (the salt), 
- apply several ***one-way cryptographic transformations*** to it. 
<br>

The result is a new sequence of characters that has no resemblance to the original password, <br>
and has no known way to be transformed back into the original password.<br>

#### Then how do you verify the given password?
Password hashes can be verified in place of the real passwords because hashing functions are repeatable:<br>

    given the same inputs, the result is always the same. 
    But it doesn't allow count operate them through the result. 


#### Hashing Passwords with Werkzeug
Werkzeug’s security module conveniently implements secure password hashing.<br>
This functionality is exposed with just two functions, used in the registration and verification phases, respectively:

- ***generate_password_hash***(password, method='pbkdf2:sha256', salt_length=8)
- ***check_password_hash***(hash, password)
    - This function takes a hashed password previously stored in the database and the password entered by the user. 
    - A return value of True indicates that the user password is correct.
<br>

*app/models.py*
```py
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


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
    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)
    
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)
```
The password hashing function is implemented through a ***write-only*** property called password.<br>
The password hashing functionality is now complete and can be tested in the shell:<br>

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
You can run the unit test suite like this every time you want to confirm everything is working as expected. <br>

### Creating an Authentication Blueprint
Authentication Blueprint will be used to define routes.<br>
The routes related to the user authentication subsystem will be added to another blueprint, called auth.<br>
Using different blueprint for different subsystem of the application is a great way to keep the code clean.<br><br>

*app/auth/\_\_init\_\_.py 
```python
from flask import Blueprint
auth = Blueprint("auth", __name__)

from . import views
```
<br><br>

***app/auth/views.py*** will import the blueprint and define the routes that are specifically associated with authentication using its route decorator(***auth.route('endpoint')***):
```python
from flask import render_template
from . import auth

@auth.route('/login')
def login():
    return render_template('auth/login.html')
```

Note that template file given to ***render_template()*** is stored inside the *auth* subdirectory.<br>
As Flask expects the templates' paths to be relative to application directory, store them under ***app/template***.<br><br>

Teh auth blueprint needs to be attached to the application in the ***create_app()*** factory function.<br>
*app/\_\_init\_\_.py*
```python
...
...
def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
```
the ***url_prefix*** argument in ***register_blueprint*** is optional.<br>
When used, all routes defined in the blueprint will be registered with the given prefix.<br>
Now, while you can get an access to routes defined in main blueprint without the prefix attached,<br>
You can access login route defined in auth blueprint only through "http://localhost:5000/auth/login". <br>





### User Authentication with Flask-Login
When users log in to the application, their authenticated state has to be recorded in the user session, so that it is remembered as they navigate through different pages.<br><br>

***Flask-Login*** is a small but extremely useful extension that specializes in managing this particular aspect of a user authentication system, without being tied to a specific authentication mechanism.<br>

#### Preparing the User Model for Logins
Flask-Login works closely with the application’s own User objects. To be able to work with the application’s User model, the Flask-Login extension requires it to implement a few common properties and methods. Propety/method and descriptions of it follow:<br>

- is_authenticated  : Must be True if the user has valid login credentials or False otherwise.
- is_active         : Must be True if the user is allowed to log in or False otherwise. A False value can be used for disabled accounts
- is_anonymous      : Must always be False for regular users and True for a special user object that represents anonymous users.
- get_id()          : Must return a unique identifier for the user, encoded as a Unicode string
<br><br>

These properties can be implemented directly in the model class but as an easier alternative Flask-Login provides a ***UserMixin*** class that has default implementations that are appropriate for most cases:
```py
from flask_login import UserMixin
class User(UserMixin, db.Model):
    """
    UserMixin adds properties and methods
    - is_authenticated : bool 
    - is_active : bool
    - is_anonymous : bool = False
    - get_id() : str 
    """

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
*app/\_\_init\_\_.py*
```python
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.login_view = "auth.login" ### 
def create_app(config_name): 
    # ...
    login_manager.init_app(app) 
    # ...
```
The login_view attribute of the LoginManager object sets the endpoint for the login page.<br>
Flask-Login will *redirect to the login page when an anonymous user tries to access a protected page.*<br>
Because the login route is inside a blueprint, it needs to be prefixed with the blueprint name.<br><br>

#### loading a user from Database
Finally, Flask-Login requires the application to designate a function to be invoked when the extension needs to load a user from the database given its identifier.<br>

***app/models.py: user loader function***
```py
from . import login_manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

***login_manager.user_loader*** decorator is used to register the function with Flask-Login, which will call it when it needs to retrieve information about the logged-in user. The return value of the function must be the user object, or None if the user identifier is invalid or any other error occurred.<br><br>

**Where does user_id come from?**<br>
That's the question that deserves another section.<br>
If you want to get an answer right way, go to "Understanding How Flask-Login Works."<br>


### Protecting Routes
To protect a route so that it can only be accessed by authenticated users, Flask-Login provides a ***login_required*** decorator. An example of its usage follows:

```python
from flask_login import login_required
@app.route('/secret') 
@login_required
def secret():
    return 'Only authenticated users are allowed!'
```
Just as with normal Python wrappers, you can "chain" multiple function decorators.<br>
In this example, the secret() function will be protected against unauthorized users with login_required.<br> 
Thanks to the login_required decorator, if this route is accessed by a user<br>
who is not authenticated, Flask-Login will intercept the request and send the user to the login page instead.<br><br>

### Adding  Login Form
The login form that will be presented to users has:
- Text field for the email address
- Password field 
- “remember me” checkbox 
- Submit button. 
<br>

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

The email field uses the Length() and Email() validators from WTForms in addition to DataRequired(), to ensure that the user not only provides a value for this field, but that it is valid.<br><br>

In the template, you'll just need to render the form using Flaks-Bootstarp's wtf.quick_form() macro. <br><br>

You may also want to display "LogIn" or "Log Out" links depending on the logged-in state of the current user.<br>

*app/templates/base.html*
```html
            <ul class="nav navbar-nav navbar-right">
                {% if current_user.is_authenticated %} 
                <!-- current_user variable is defined by Flask-Login and it's 
                automatically available to view functions and templates -->

                <li><a href="{{ url_for('auth.logout') }}">Log Out</a></li>
                {% else %}
                <li><a href="{{ url_for('auth.login') }}">Log In</a></li>
                {% endif %}
            </ul>
```


### Signing Users In
The implementation of the more realistic login() view function is shown below:
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
            #Here, you put user object and boolean value to login_user
            login_user(user, form.remember_me.data)  

            #in case user wanted to go to different page before coming to login page. 
            next = request.args.get('next')
            
            if next is None or not next.startswith('/'):
                next = url_for('main.index') 
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)
```
<br>

If the password is valid, Flask-Login’s ***login_user()*** function is invoked to record the user as logged in for the user session. The login_user() function takes the user to log in and an optional ***"remember me"*** Boolean.<br><br>

If the value of ***"remember me"*** set to False, user ssession will expire when browser window is closed. A value of True causes a ***long-term cookie*** to be set in the user’s browser, which Flask-Login uses to restore the user session. The optional ***REMEMBER_COOKIE_DURATION*** configuration option can be used to change the default one-year duration for the remember cookie.

#### Post/Redirect/Get pattern
POST request that submitted the login credentials ends with a redirect, but there are two possible URL destinations: 

- If the login form was presented to the user to prevent unauthorized access to a protected URL the user wanted to visit, then ***Flask-Login will have saved that original URL in the next query string*** argument, which can be accessed from the request.args dictionary.
- If the next query string argument is not available, a redirect to the home page is issued instead. 
<br>

The URL in next is validated to make sure it is a relative URL, to prevent a malicious user from using this argument to redirect unsuspecting users to another site.<br><br>

***NOTE*** - On a production server, the application must be made available over secure HTTP(HTTPs), so that login credentials and user sessions are always transmitted encrypted.

#### Login template
***app/templates/auth/login.html***
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

### Understanding How Flask-Login Works
The following is the sequence of operations.<br>

1. The user navigates to http://localhost:5000/auth/login by clicking on the "Log In" link. The handler for this URL returns the login form.

2. User enters their credentials. 
    - 2-1. Handler validates submitted credentials and then invokes ***login_user()*** function to log the user in. 
    - 2-2. the ***login_user()*** function writes the ID of the user to the ***user session*** as a string. It's possible as you pass user object as an argument.
    - 2-3. view function returns with a redirect to a different page.
3. client(browser) receives redirects.
    - 3-1. the view function of redirected endpoint is invoked, triggers rendering. 
    - 3-2. during the rendering, a reference to Flask-Login's ***current_user*** is now possible. 
    - 3-3. ***current_user*** context variable doesn't have value assigned for this request yet. So it invokes Flask-Login's internal function **_get_user()** to find out who the user is. 
    - 3-4. **_get_user()** function essentially checks if user session has 'user ID'.
        - If there isn't one, it returns an instance of Flask-Login's ***AnonymousUser***. 
        - If there is, ***_get_user()*** invokes the function registered in ***app/models.py*** with ***@login_manager.user_loader*** decorator, with its ID as its argument.
        - Note that here the ***ID is primary ID of the user object.***
    - 3-5. ***load_user(user_id)*** handler reads the user from the database and returns it. Flask-Login assigns it to the current_user context variable for the current request. 
    - 3-6. The template receives the newly assigned value of current_user.
<br>

The **@login_required** decorator builds on top of the current_user context variable<br>
by allowing only the decorated view function to run when the expression,<br> 
***current_user.is_authenticated*** is set to True.<br><br>

***NOTE*** - You can't see the logic about how "@login_required" checks the current_user's authentication status as **@login_required** must have been implemented using current_user variable which is made available by Flask-Login even in view function.<br>


### Testing Logins
*app/templates/index.html*:
```html
Hello,
{% if current_user.is_authenticated %}
    {{ current_user }}
{% else %}
    Stranger
{% endif %}!
```
<br>
Now, because no user registration functionality has been built, a new user can only be registered from the shell at this time.: <br>
```sh
$ flask shell
>>> u = User(email="example@example.com", username="Ko",password = "cat")
>>> db.session.add(u)
>>> db.session.commit()
```






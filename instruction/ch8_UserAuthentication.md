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

Now, because NO user registration functionality has been built, a new user can only be registered from the shell at this time.: <br>

```sh
$ flask shell
>>> u = User(email="example@example.com", username="Ko",password = "cat")
>>> db.session.add(u)
>>> db.session.commit()
```

### New User Registration
#### Adding a User registration Form 
***app/auth/forms.py***
```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField,SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from twforms import ValidationError
from ..models import User

class RegistrationForm(FlaskForm):
    email=StringField("Email",validators=[
        DataRequired(),
        Length(1,64),
        Email()])
    username=StringField("Username",validators=[
        DataRequired(),
        Length(1,64),
        Regexp(r'^[a-zA-Z][A-Za-z0-9_.]*$',
                flags=0,
                message="Usernames must have only letters, numbers, dots or underscores")
        ]
        )
    password=PasswordField("Password",validators=[
        DataRequired(),
        EqualTo("password2",
                message="Password must match") 
                ])
    password2=PasswordField("Confirm password",validators=[DataRequired()])

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")
    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already in use")
```
<br>

This form uses the ***Regexp()*** validator, arguments of which are pattern, flags(re.IGNORECASE, for example) and Error message to raise.<br><br>

The password is entered twice as a safety measure. Validating two password fields are same is done with ***EqualTo()*** validator.<br><br>

In addition to validators provided by *wtfform.validators*, here we have two custom validators implemented as methods. When inheriting ***FlaskForm***, if the subclass defines a method with: the prefix "***validate_*** and field name", the method is invoked in addition to regularly defined validators. So in this case, when ***email*** field is validated, this custom validator is also applied.  <br><br>

#### Adding templates

The template that presents this form is called /templates/auth/register.html:
```html
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}

{% block title %}Flasky - Register{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Register</h1>
</div>
<div class="col-md-4">
    {{ wtf.quick_form(form) }}
</div>
{% endblock %}
```
<br>

The registration page needs to be linked from the login page so that users who don't have an account can easily find it:
```html
<p>
    New User?
    <a href="{{ url_for('auth.register') }}">
        Click here to register
    </a>
</p>
```

#### View functions for User registration
The view function that performs registering user to database is shown below:<br>

***app/auth/views.py***
```python
from .forms import RegistrationForm
from ..models import User
@auth.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email= form.email.data,
                    username= form.username.data,
                    password= form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("You can now login")
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)
```

### Account Confirmation
For certain applications, it is important to ensure user information provided during registration is valid. <br><br>

To validate the email address, applications send a confirmation email to users immediately after they register. The new account is initially marked as unconfirmed. The account confirmation procedure typically involves clicking a specially crafted UTL link hat includes a confirmation token. <br>

#### Generating Confirmation Tokens with 'itsdangerous' 
The simplest account confirmation link would be a URL with the format ***http://www.example.com/auth.confirm/< id >***. So when the user clicks the link, the view function that handles this route receives the user id to confirm as an argument and can easily update the 'confirmed' status of the user. <br><br>

But that is obviously not secure implementation. The better idea would be replacing < id > part in the ***URL with a token that only server can generate***.<br><br>

Flask uses cryptographically signed cookies to protect the content of user sessions against tampering. The user session cookies contain cryptographic signature generated by a package called "itsdangerous". <br><br>

If the contents of the user session is altered, the signature will not match the content anymroe. Flask then discards the session and start the new one. The same concopt can be applied to confirmation tokens. <br><br>

*Shell session to show how itsdangerous can generate a signed token*:
```python
$ flask shell
>>> from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
>>> s = Serializer(app.config["SECRET_KEY"],expires_in=3600)
>>> token = s.dumps({"confirm":23})
>>> token 
'eyJhbGciOiJIUzI1NiIsImV4cCI6MTM4MTcxODU1OCwiaWF0IjoxMzgxNzE0OTU4fQ.ey ....'
>>> data= s.loads(token)
>>> data
{'confirm': 23}
```
While itsdangerous package contain several types of token generators, we will use the class TimedJSONWebSignatureSerializer that generates JSON Web Signatures(JWSs) with a time expiration. This class takes encryption key which in a Flask application can be configured with SECRET_KEY.<br><br>

***dumps()*** method generates a cryptographic signature for the data. To decode the token, ***loads()*** that the token as argument. The function verifies the signature and the expiration time. If and only if both are valid, it returns the original data, or else exception is raised. <br><br>

Token generation and verification can be added to User model: <br>
*app/models.py*:
```python
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from . import db

class User(UserMixin,db.Model):
    confirmed=db.Column(db.Boolean, default=False)

    def generate_confirmation_token(self,expiration=300):
        s = Serializer(current_app.config["SECRET_KEY"],expiration)
        return s.dumps({'confirm':self.id}).decode('utf-8') #token
    
    def confirm(self,token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try :
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get("confirm") != self.id:
            return False
        self.confirm=True
        db.session.add(self)
        return True
```
Hoo! ***generate_confirmation_token()*** method generates a token with a default validity time of 5 minutes. <br><br>

The ***confirm()*** method verifies the token and, if valid, sets the new confirmed attribute in the user instance to True. Plus, it check if the id from the token matches the logged-in user's id. <br><br>


#### Test User model in the unittest
tests/token_test.py
```python
import unittest
from app.model import User
import time
from app import create_app,db

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context=self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit.()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))
    
    def test_invalid_confirmation_token(self):
        u1 = User(password="cat")
        u2 = User(password="dog")
        db.session.add_all([u1,u2])
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        u = User(password='tiger')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))
```

#### Sending Confirmation Emails
The current */register* route directs to /index after adding the new user to the database. But, before redirecting, this route now needs to send the confirmation email as follows:<br><br>

*app/auth/views.py*:
```python
from ..email import send_email
@auth.route('/register', methods=["GET","POST"])
def register():
    form =RegistrationFrom()
    if form.validate_on_submit():
        ...
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,"Confirm Your Account", "auth/email/confirm", user=user, token=token)
        flash("A confirmation email has been sent to you by email")
        return redirect(url_for("main.index"))
    return render_template("auth/register.html",form=form)
```
As 'id' field is required to generate confirmation token, db.session.commit() must be called first.<br><br>

The email templates used by the authentication blueprint will be added in the templates/auth/email directory to keep them separate from the HTML templates. For each email, two templates are needed for the plain-text and HTML versions of the body: <br><br>

*app/templates/auth/email/confirm.txt*
```html
Dear {{ user.username }},

Welcome to Vertica Project!

To confirm your account please click on the following link:

{{ url_for('auth.confirm', token=token,_external=True)}}

Sincerly,

Vertial Data Management Team - Migo

Note: replies to this email address are not monitored.
```
<br>

By default, url_for() generates relative URLs, such as '/auth/confirm/< token >'. Within the context of webpage, it works fine but when sending URL over email there is no such context. You need to specify pull path by setting ***_external*** to True. <br><br>

The view function that confirms the accounts is shown below.<br>
*app/auth/view.py*
```python
from flask_login import current_user

@auth.route("/confirm/<token>")
@login_required
def confirm(token):
    if current_user.confirmed: #In case they're already confirmed
        return redirect(url_for('main.index'))
    if current_user.confirm(token): 
        db.session.commit() #remember, we left off at db.session.add()
        flash("You have confirmed your account!")
    else:
        flash("The confirmation link is invlid or has expired")
    return redirect(url_for("main.index"))
```
This route is protected with ***@login_required.***<br><br>

The function first checks if the logged-in user is already confirmed.<br><br>

Because actual token confirmation is done entirely in the User model, all the view function has to do is call the ***confirm()*** method and then flash the message. If the function returns True, it means the function have checked the token and changed confirm attribute of user instance to True and added them. So to finalize it, you need to do db.session.commit() <br><br>

Each application can decide what unconfirmed users are allowed to do before they confirm their accounts. This step can be done using Flask's ***before_request*** hook. <br><br>

From a blueprint, the ***before_request*** hook applies only to requests that belong to the blueprint. To install a blueprint hook for all application request, ***before_app_request*** must be used instead. The following example shows how this handler is implemented:<br><br>

*app/auth/views.py*
```python
@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
        and not current_user.confirmed \
        and request.blueprint != 'auth' \
        and request.endpoint != 'statc' :
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anynomous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')
```

The before_app_request handler will intercept a request when three conditions are true: 
- A user is logged in(current_user.is_authenticated)
- The account is not confirmed
- The requested URL is outside of authentication blueprint and is not for static file.
    - Access to the authentication routes needs to be granted, as those are the routes that will enable the user to confirm the account. 
<br><br>

The page that is presented to unconfirmed users just renders a template that gives users instructions for how to confirm their accounts and offers a link to request a new confirmation email. <br><br>

*app/templates/auth/unconfirmed.html:
```html
{% extends "base.html" %}

{% block title %}Confirm your account{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>
        Hello, {{ current_user.username }}!
    </h1>
    <h3>You have not confirmed your account yet.</h3>
    <p>
        Before you can access this site you need to confirm your account.
        Check your inbox, you should have received an email with a confirmation link.
    </p>
    <p>
        Need another confirmation email?
        <a href="{{ url_for('auth.resend_confirmation') }}">Click here</a>
    </p>
</div>
{% endblock %}
```
<br>

*app/auth/views.py*:
```python
from flask_login import current_user

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token=current_user.generate_confirmation_token()
    send_email(current_user.email,"Confirm Your Account", 'auth/email/confirm', user=current_user,token=token)
    flash('A new confimration email has been sent to you by email.')
    return redirect(url_for('main.index'))
```

This route repeats what was done in the ***"registration"*** route (not confirm/< token >) using current_user, the user who's logged in as the target user. 

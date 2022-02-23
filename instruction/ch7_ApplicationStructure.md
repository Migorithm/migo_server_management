## Large Application Structure

The way to structure the application in Flask is left entirely to developer.<br>
So here, the possible way to organize a large application is presented.<br>

Basic Layout:<br>

    |-project
        |-app
            |-templates/
            |-static/
            |-main/
                |-__init__.py
                |-errors.py
                |-forms.py
                |.views.py
            |-__init__.py
            |-email.py
            |-models.py
        |-migrations/
        |-tests/
            |-__init__.py
            |-test*.py
        |-venv/
        |-requirements.txt
        |-config.py
        |-project_name.py

### Configuration Options
Applications often need several configuration sets.<br>
The best example of this is the need for using different databases.<br>

The following shows the ***config.py***, with all settings.
```python
import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config:     #Base class which contains settings common to all configs 
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'default.mail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Vertica]'
    FLASKY_MAIL_SENDER = 'Vertica Admin <noreply@example.com>'
    FLASKY_ADMIN = os.environ.get('ADMINS')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


"""
The SQLALCHEMY_DATABASE_URI variable is assigned different values under each of the
three configurations.
"""

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
#For testing configuration, the default is an in-memory database as there is no need to store any data. 



class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
```
<br>

- ***Config*** class and its subclasses(Dev,Test,Prod) can define an ***init_app()*** class method that takes the application instance as an argument. For now, it's empty. 
- At the bottome, the different configurations are registered in a ***config*** directory.

### Application Package
***"app/"*** is where all the application code, tempaltes, static files live.<br>
Specifically, it consists of:
- tempaltes/
- static/ 
- models.py (database)  
- email.py  

But that's certainly not the end.

#### Using an Application Factory
Although creating application in a single file may be convenient, <br>
as such application is created in global scope, there is no way to apply<br>
configuration changes dynamically.<br>
This is particularly important for unit test because sometimes<br>
it is necessary to run the application under different configuration settings.<br><br>

The solution to this problem is to ***delay the creation of the applcation***<br>
by moving it into a ***factory function*** that can be explictly invoked from the script.<br>
The application factory function is defined in the ***app** package constructor(\_\_init\_\_.py): <br>
<br>

*app/\_\_init\_\_.py
```python
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    
    # config setting stored in class defined in config.py will be used
    # by using app.config.from_object()
    app.config.from_object(config[config_name]) 
    config[config_name].init_app(app)

    # Once an application is created and configured, 
    # the extensions below can be initialized.
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    return app
```
- This constructor imports most of the Flask extensions currently in use.
- ***create_app()*** function is the application factory, which takes an argument, the name of a configuration to use for application.

Note that applications created with the factory function in its current state are INCOMPLETE, as they are missing ***routes*** and ***custom error page*** handlers. And this deserves more details.<br>

#### Implementing Application Functionality in a Blueprint
In single-script applications, the application instance exists in the global score, so routes can be easily defined using ***app.route*** decorator.<br><br>

But now that the application is created at runtime, ***app.route*** decorator begins to exist only after ***create_app()*** is invoked, which is too late. And custom error page handlers present the same problem as they are also defined with ***app.errorhandler***.<br><br>

To solve this, Flask offers ***blueprints***, which are similar to an application in that it can also define routes and error handlers. But the different is when they are defined, it's in dormant state until the blueprint is registered with an application, at which point they become a part of it.<br><br> 

By using a blueprint which you define in global scope, the routes and error handler can be defined the same way as in the single-sciprt application.<br><br>

Blueprints can be defined all in a single file or can be created in a more structured way. To allow for the greatest flexibility, a ***subpackage INSIDE app/ package*** will be created.<br><br>

*app/main/\_\_init\_\_.py*
```python
from flask import Blueprint
main = Blueprint("main", __name__) #Just as you define app = Flask(__name__)

from . import views, errors
```

When initailized, the constructor of Blueprint class takes two arguments:
- blueprint name
- module or package where the blueprint is located; hence \_\_name\_\_ is just right. 
<br>

The routes of the application are stored in ***app/main/views.py*** and error handlers are in ***app/main/errors***.<br><br>

**Importing these modules causes the routes and error hanlders to be associated with the blueprint.** However, note that these modules are imported at the bottom of \_\_init\_\_.py script to avoid errors due to ***circular dependencies.***<br><br>

In this particular example the problem is that app/main/views.py and app/main/errors.py in turn are going to import the main blueprint object, so the imports are going to fail unless the ***circular reference*** occurs after main is defined.(circular dependencies are evaluated at build or compile time where as circular reference is at runtime.)<br><br>

The blueprint is registered with the application inside the ***create_app() factory*** function below.<br><br>

*app/\_\_init\_\_.py* 
```python

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint) ### register_blueprint! 

    return app
```
<br>

By registering blueprint at runtime, all the routes and error handlers<br>
could also be used that are defined inside app/main/routes and errors.<br>
HOWEVER, ***would that be app.routes('path') ?*** No!<br><br>

*app/main/errors.py*
```python
from flask import render_template
from . import main

@main.app_errorhandler(404)  #main! not app
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

```
The difference is that these decorators will be invoked only for things that<br>
originate in the routes defines BY the blueprint. So, "@main.errorhandler"<br>
is not application-wide error handler. To aboid this, you use ***"@main.app_errorhanlder"***<br>
To indicate it's application-wide one. Let's see views as well: <br><br>

*app/main/views.py*
```python
from flask import render_template, session, redirect, url_for, current_app
from .. import db
from ..models import User
from ..email import send_email
from . import main
from .forms import NameForm


@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            if current_app.config['FLASKY_ADMIN']:
                send_email(current_app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('.index'))
    return render_template('index.html',
                           form=form, name=session.get('name'),
                           known=session.get('known', False))
```
In addition to ***"@main.route()"*** replcaing app with main,<br> 
the key difference added here is the usage of ***url_for()*** function.<br><br>

As you may remember, the first argument to ***url_for()*** is the endpoint name(function name. Flask applies a namespace to all the endpoints defined in a blueprint, so that multiple blueprints can define view functions with the same endpoint names without collisions. <br><br>

The namespace is the name passed as first argument to Blueprint constructor, and is separated from the endpoint name with a dot. The index() view function is therefor registered with the name "main.index" and its URL can be obtained through ***url_for('main.index')***.<br><br>

Using just ***".index"*** is shorter format for endpoints. This essentially means, redirects WITHIN the same blueprint can use the shorter form, while redirects that go for other blueprint(namespace) require fully qualified endpoint name, such as "second_blueprint.index".<br><br>

To complete the changes, the following are also needed to be completed
- forms.py (*app/main/forms.py*)
- email.py (*app/email.py*)
- models.py (*app/models.py*)
<br>

***app/main/forms.py***:
```python
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')
```
<br>

***app/email.py***
```python
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
```


***app/models.py***
```python
from . import db
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username
```



### Application Script
***project_name.py*** is where application instance is really defined(Don't get confused by so many \_\_init\_\_.py under app/ and app/main.)<br><br>

*project_name.py*:
```python
import os
from app import create_app, db   #application factory and db
from app.models import User,Role 
from flask_migrate import Migrate

app = create_app(os.getenv("FLASK_CONFIG") or 'default')
migrate = Migrate(app,db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

```
The configuration is taken from environment variable "FLASK_CONFIG" if it was defined, or else "default" which in this case will be mapped to DevelopmentConfig instance.<br><br>

Because main script of the application changed from hello.py to project_name.py, value of FLASK_APP must be changed accordingly.<br><br>

### Unit Tests
As yet, this application is quite small; therefore there isn't a lot to test. But as an example, two simple tests can be defined, as shown below:<br><Br>

*tests/test_basics.py*:
```python
import unittest
from flask import current_app
from app import create_app, db


class BasicTestCase(unittest.TestCase):
    def setUp(self): #For every test, it will proceed
        self.app = create_app('testing')

        #Activation of app context
        self.app_context = self.app.app_context()
        self.app_context.push()

        #create db in memory(path not defined)
        db.create_all()

    def tearDown(self): # For every test, this will follow.
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
```
setUp() and tearDown() methods of the test case class run before and after each test.<br>
Any methods that have a name that begins with ***test_*** are executed as tests.<br>
***setUp*** method is to create an environment that is as close to that of running application.<br>
***app.config['TESTING']*** and ***app.config['DEBUG']*** are set to False and become True <br>
only when appropriate config subclass is chosen. <br><br>

To make ***tests/*** directoryu a proper package, a ***tests/\_\_init\_\_.py*** module needs to be added even if it's empty.<br><br>

To run the unit tests, a custom command can be added to the ***project_name.py***:
```python
@app.cli.command()
def test(test_names=None):
    """Run the unit tests."""
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
```

The app.cli command decorator makes it simple to implement custom commands. The ***name of decorated function is used as command name (test in this example)***. And the function's docstring is displayed in the help messages. The implementations of the test() function invokes the test runner from the unittest package. <br><br>

This unit tests can be executed as follows:
```sh
$ flask test
test_app_exists  .... ok
test_app_is_esting .... ok
```


### Database Setup
The database URL is taken from an environment variable as a first choice.<br>
For example, in development configuration, the URL is obtained from DEV_DATABASE_URL.<br><br>

Regardless of the source of the database URL, the database tables must be created for the new database.<br> 
When working with Flask-Migrate to keep track of migrations, database tables can be created or upgraded<br> 
to the latest revision with a single command: 
```sh
flask db upgrade
```



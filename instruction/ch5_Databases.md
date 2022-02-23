## Databases

### Database Management with Flask-SQLAlchemy
It offers a high-level ORM and low-level access to the database’s native SQL functionality. In Flask-SQLAlchemy, a database is specified as a URL. For example:

- MySQL : mysql://username:password@hostname:port/database
- Postgres : postgresql://username:password@hostname:port/database
- SQLite : (Linux, macOS) sqlite:////absolute/path/to/database
- SQLite : (Windows) sqlite:///c:/absolute/path/to/database

In these URLs, hostname refers to the server that hosts the database service, which could be localhost or a remote server. So, database indicates the name of the database to use.<br><br>

#### Prerequisite
- The URL MUST be configured as the key ***SQLALCHEMY_DATABASE_URI*** in the Flask configuration object.
- It's also suggested to set key ***SQLALCHEMY_TRACK_MODIFICATIONS to False*** to use less memory unless signals for object changes are needed.


#### Initialization
```python
import os
from flask_sqlalchemy import SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
```

#### Model definition
In the context of an ORM, a model is typically a Python class with attributes that match the columns of a corresponding database table. <br>

database instance('db=SQLAlchemy(app)') from Flask-SQLAlchemy provides a base class which is passed to the model:
```python
class Role(db.Model):
    __tablename__ = 'roles'  # Table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)

    def __repr__(self):
        return '<User %r>' % self.username
```
As you can see, in addition to providing base class, it also provides helper functions usable to define the structure of table. <br><br>
The first argument given to the db.Column constructor is the type of the database column
and model attribute and the second arguments to db.Column specify configuration options for each
attribute such as:
- primary_key
- unique
- index
- nullable
- default


### Relationships (one-to-many)
When you think about it, the tables defined above will have one(roles)-to-many(users) relationship as one role can belong to many users. If we draw the relationship correctly and apply that to our model:
```python
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id')) #table name is roles, not Role. 

    def __repr__(self):
        return '<User %r>' % self.username
```
Key notes:
- The 'roles.id' argument in db.ForeingKey() specifies that the column should be interpreted as having id values from rows in the roles table.
- 'users' attribute in Role class represents the ***object-oriented view of the relationship***. What it means is ***'users' will return the list of users*** associated with the specific role(role instance). 
- ***backref*** may be confusing but what it does is it adds "role" attribute to the User model. So, any instance of User can see its role without having to do "join" to see its role. If it were not for this one, to see role of the User, they should implement something like:

    "SELECT username.Users, name.roles FROM users INNER JOIN roles on users.rold_id=roles.id"

#### Useful relationship options
- backref      : described above.

- primaryjoin  : specify the join condition between two models. Necessary when ambiguous.

- lazy         : specify how the related times are to be loaded. Commonly used values are:    
    - select    : items are loaded on demand the first time they are accessed.
    - dynamic   : instead of ladoing the items, the query that can load them is given. 

- uselist      : if set to False, use a scalar instead of list

- order_by     : specify the ordering for the items in the relationship


#### what about in one-to-one relationship?
The one-to-one relationship can be expressed the same way as one-to-many, as described earlier, but with the uselist option set to False within the db.relationship() definition so that the “many” side becomes a “one” side.

### Database Operations
Now, things are ready. The best way to learn how to work with these models is in a Pyhon shell.

#### Creating tables
```python
>>> $ flask shell
>>> from hello import db
>>> db.create_all()
```
***db.create_all()*** locates all the subclasses of db.Model and create corresponding tables.<br>
db.create_all() function will not re-create or update a database table if it already exists in the database.<br>
This can be inconvenient when the models are modified and the changes need to be applied to an existing database.<br>
The brute-force solution will be:
```python
>>> db.drop_all()
>>> db.create_all()
```
But the obvious side-effect of this approach is it destroys all teh data in the old database.<br>
The better solution to this problem is ***"migration"***. We'll cover that later. 

#### Inserting rows
```python
>>> from hello import Role, User
>>> admin_role = Role(name='Admin')
>>> mod_role = Role(name='Moderator')
>>> user_role = Role(name='User')
>>> user_john = User(username='john', role=admin_role)
>>> user_susan = User(username='susan', role=user_role)
>>> user_david = User(username='david', role=user_role)
```
Note here again, we didn't define role attribute explictly in User class but it's still accessible thanks to ***backref*** defined as a second keyword argument in db.relationship().<br>
Primary key, id attributes of both class were not set: they are managed by database itself. And as they are on Python side yet, their id values are not assigned, therefore not accessible.<br>

Changes to the database are managed through a database session(transaction), which Flask-SQLAlchemy provides as db.session:
```python
>>> db.session.add(admin_role)
>>> db.session.add(mod_role)
>>> db.session.add(user_role)
>>> db.session.add(user_john)
>>> db.session.add(user_susan)
>>> db.session.add(user_david)
#Or more concisely,
db.session.add_all([admin_role, mod_role, user_role,user_john, user_susan, user_david])
```
To write the objects to the database, the session needs to be committed by calling its commit() method:
```python
>>> db.session.commit()
```

#### Deleting rows
The database session also has a delete() method. The following example deletes the "Moderator" role from the database:
```
>>> db.session.delete(mod_role)
>>> db.session.commit()
```
Note that deletions, like insertions and updates, are executed only when the database session is committed.

#### Querying rows
The most basic query for a model is triggered with the all() method.
```python
>>> Role.query.all()
[<Role 'Administrator'>, <Role 'User'>]
>>> User.query.all()
[<User 'john'>, <User 'susan'>, <User 'david'>]
```
<br>

Of course, query object can be configured to issue more specific database searches through the use of ***filters***.<br>
The following example finds all the users that were assigned the "User" role:
```python
>>> user_role = Role(name='User')
>>> User.query.filter_by(role=user_role).all()
[<User 'susan'>, <User 'david'>]
```

#### Extracting the native query
It is also possible to inspect the ***native SQL query*** that SQLAlchemy generates for a given query by converting the query object to a string:
``` python
>>> str(User.query.filter_by(role=user_role))
"""
SELECT users.id AS users_id, users.username AS users_username, users.role_id AS users_role_id 
FROM users WHERE :param_1 = users.role_id
"""
```

#### Filters
Filters such as filter_by() are invoked on a query object and ***return a new refined query.***<br> 
Multiple filters can be called in sequence ***until the query is configured as needed.***<br>
The most common filters available are:
- filter()      : Return a new query that adds an additional filter to original query (pythonic filtering like User.name =="John")
- filter_by()   : Return a new query that adds an additional "equality" filter to the original query(keyword argument)
- limit()       : Return a new query that limits the number of results.
- order_by()    : Return a new query that sorts the result.
- group_by()    : Return a new query that groups the results.

#### After filters are applied...
After the desired filters have been applied to the query, ***a call to all() will cause the query to execute*** and return the results as a list. But there are other query executors too: 
- all()
- first()
- get()     : Returns the row that matches the given primary key, or None.
- count()   : Returns the result count of the query.
- paginate(): Returns a ***Pagination object*** that contains the specified range of results.          
<br>

Let's take a look at the relationship we made between 'users' and 'roles' table:
```python
>>> from hello import db,Role,User
>>> user_role = Role(name="user")
>>> user_john = User(username="John", role=user_role)
>>> user_susan = User(username="Susan",role=user_role)
>>> db.session.add_all([user_role,user_john,user_susan])
>>> db.session.commit()

# Get users that has a role of "user_role" by querying against users table.
>>> User.query.filter_by(role=user_role).all() #here, all() is what execute the query
[<User 'Susan'>, <User 'John'>]

# Get users that has a role of "user_role" by querying against User instance. 
>>> user_role.users
[<User 'Susan'>, <User 'John'>]
```
***user_role.users*** query here has a small problem. The implicit query interally calls ***all()*** executor to return the list of users. Because the intermediate, query object is hidden, it's not possible to refine it with additional query filters. But say you want to list them in alphabetical order, you can't and this necessitates modification of our code so query is not automatically executed: 

```python
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role',lazy="dynamic")

    def __repr__(self):
        return '<Role %r>' % self.name
```

With the relationship configured in this way, user_role.users returns a query that hasn’t executed yet, so filters can be added to it:
```python
>>> user_role.users.order_by(User.username).all()
[<User 'david'>, <User 'susan'>]
>>> user_role.users.count()
2
```

### Database Use in View Functions

```python
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()  
        if user is None: # check if submitted name is in the DB
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False #after inserting new user information, set "known" key to False 
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))
```
<br>
Corresponding index.html page follows:
```html
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}

{% block title %}Flasky{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Hello, {% if name %}{{ name }}{% else %}Stranger{% endif %}!</h1>
    {% if not known %}
    <p>Pleased to meet you!</p>
    {% else %}
    <p>Happy to see you again!</p>
    {% endif %}
</div>
{{ wtf.quick_form(form) }}
{% endblock %}
```

## Integration with the Python Shell
Having to import the database instance and the models each time a shell session is started is tedious work. To avoid having to constantly repeat these steps, the flask shell command can be configured to automatically import these objects:

```python
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)
```
The shell context processor function returns a dictionary that includes the database instance and the models. The flask shell command will import these items automatically
into the shell.

```python
$ flask shell
>>> app
<Flask 'hello'>
```

## Database Migrations with Flask-Migrate
Say you want to add more attribute to the class that models tables in DB. When it happens, the database needs to be updated as well. But as we discussed earlier, Flask-SQLAlchemy creates tables only when they don't exist already. If you brute-forcily destroy and recreat, that costs you the loss of data. So, here comes the need for ***migration***.

### Introduction to Flask-Migrate
The developer of SQLAlchemy has written a migration framework called Alembic, but instead of using Alembic directly, Flask applications can use the Flask-Migrate extension, a lightweight Alembic wrapper that integrates it with the flask command.


### Creating Migration Repository
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
```
To expose the database migration commands, Flask-Migrate adds a ***flask db*** command with several subcommands.<br>
Working on a new project, you add ***init***:
```sh
flask db init
```
This command creates a "migrations" directory, where all migration scripts will be stored.

### Creating a Migration Script
A database migration is represented by a migration script.<br>
This script has two functions called upgrade() and downgrade():
- upgrade() : applies the database changes that are part of the migration
- downgrade() : removes the changes
***These adding and removing abilities mean we can reconfigure database to any point in the change history.***
<br>

Alembic migrations can be created manually by ***revision command*** or automatically by ***migrate command***.<br>
- manual migration: A manual migration creates a migration skeleton script with empty upgrade() and downgrade() functions that need to be implemented by the developer using ***directives*** exposed by Alembic's Operation object.<br>
- automatic migration: it attempts to generate the code for the upgrade() and downgrade() functions by looking for difference between the model definitions and the current state of the database. 
    - This is not always accurate and can miss some details that are ambiguous. For example, when column is renamed, it may show that the column wad deleted and new column was added with the new name. In this case, leaving the migration as is will cause data loss. 
    - For this reason, automatic migration should always be reviewed and corrected manually. 

### Migration procedure
- initialization of migration version control by ***"flask db init"***
- Make necessary changes to the model classes
- create automatic migration script with the ***"flask db migrate"*** command
- review the generated script and adjust it so that it accurately represents the changes that were made to the models.
- Add the migration script to source control
- apply the migration to the database with the ***"flask db upgrade"*** command

For a first migration, ***flask db upgrade*** will be effectively the same as calling "db.create_all()" but in successive migrations the "flask db upgrade" command will apply updates to the tables without affecting their contents. If you already have database file that was created with the db.create_all() function, "flask db upgrade" will fail because it will try to create database tables that already exist. To address this problem, you can skip the flask db upgrade and instaed mark the existing database as upgraded using the ***"flask db stamp"*** command.

### Avoid having lots of very small migration scripts
If your last migration has not been committed to source control yet, migrate it and upgrade will cause a lot of meaningless scripts. Do avoid it, do the follwoings:
- Remove the last migration with ***"flask db downgrade"***
- Delete the last migration scripts, which is now orphaned.
- Generate a new database migration with ***"flask db migrate command"***, which will now include the changes in the migration script you just removed. 
- Review the scripts and if there is no problem, apply it by ***"flask db upgrade"*** command
## User Roles
There are several ways to implement roles in an application. If it's simple application, it may need just two roles, one for regular users and the other for administrators. In this case, ***is_administrator*** Boolean field in the ***User*** model may be all that is necessary.<br><br>

On top of that, you can assign a certain permission to a role and then you assign the role to user instance. The user role implementation presented here is a hybrid between discrete roles and permissions.

### Database Representation of Roles 
The following shows Role model.<br>
*app/models.py*:
```python
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64),unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship("User",backref="role",lazy="dynamic")

    def __init__(self,**kwargs):
        super(Role,self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions= 0
```
The ***default*** field must be set to True for only one role and False for all the others. The role marked as default will be the one automatically assigned to new users upon registration. Plus, since the application is going to search *roles* table to fine the default one, this column is indexed for faster search.<br><br>

The ***permissions*** field is an Integer value to define a list of permission in a compact way. Permission value will be powers of two(1,2,4,8,16, for example) to give each possible combination of permissions a unique value. Let's see an example.<br><br>

*app/models.py*:
```python
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16
```
<br>

With the permission constants in place, a few new methods can be added to the ***Role*** model to manage permissions.<br><br>

```python
class Role(db.Model):
    #...

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm
```
The ***add_permission(), remove_permission(), reset_permission()*** methods all use basic arithmetic operations.<br><br>

The ***has_permission()*** is the most complex of the set as it relies on *bitwise AND operator "&"* to check if a combined permission value includes the given basic permission. You can play with it:<br><br>

*flask shell*:
```python
>>> r = Role(name='User')
>>> r.add_permission(Permission.FOLLOW) 
>>> r.add_permission(Permission.WRITE) 
>>> r.has_permission(Permission.FOLLOW) 
True
>>> r.has_permission(Permission.ADMIN) 
False
>>> r.reset_permissions()
>>> r.has_permission(Permission.FOLLOW)
False
```
<br>

Adding the roles to the database manually is time consuming and error-prone, so instead a class method can be added to ***Role*** model class for this purpose. This will make it easy to recreate the correct roles and permissions during unit testing and more importantly, on the production server.<br><br>

*app/models.py*:
```python
class Role(db.Model):
    #... 
    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()
```

The inser_roles() function  tries to find existing roles by name and update them. A new role object is created only for roles that are not in the database already.<br><br>

To add a new role or change the permission assignment for a role, change the *roles* dictionary at the top of the function and then run the function again. <br><br>

### Role Assignment
We are done with ***'Role'*** model class. What about ***'User'*** model which will practically get the roles and permissions? <br><br>

When users register an account, the correct role should be assigned to them. For most users, any role that is marked as "default" would be assigned. The exception is made for administrator, who needs to be assigned the "Administrator" role from the start.<br><br>

You may then wonder how we can identify them. And it's done by email address stored in the ***ADMIN*** configuration variable, so as soon as that email address appears in a registration request it can be given the correct role.<br><br>

*app/models.py*:
```python
class User(UserMinin,db.Model):
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN']: #replace == with in if necessary
                self.role = Role.query.filter_by(name='Administrator').first()
            #if no Admin role has been defined, 
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
```

### Role Verification
To simplify the implementation of roles and permissions, a helper method can be added to ***User*** model that checks whether users have a given permission in the role:<br><br>

*app/models.py*:
```python
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager

class User(UserMixin,db.Model):
    #...
    def can(self,perm):
        return self.role is not None and self.role.has_permission(perm)
    def is_administrator(self):
        return self.can(Permission.ADMIN)

class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False
    def is_administrator(self):
        return False

login_manager.anonymous_user=AnonymousUser

```
The ***can()*** method added to the User model returns True if the requested permission is present in the role. The check for administation permission is so common that it is also implemented as a standalone ***is_administrator()*** method.<br><br>

***AnonymousUser*** class is created as it will enable the application to freely call ***current_user.can()*** and ***current_user.is_administrator()*** without having to check whether the user is logged in first. You can set this class in the ***login_manager.anonymous_user*** attribute. <br><br>

For cases in which an entire view function needs to be made available only to users with certain permissions, the following custom decorator can be used:<br><br>

***app/decorators.py***
```python
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission

def permission_required(permission): #decoration factory
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f): 
    #Why is this necessary? because the return value 
    #of permmision_required will be "decorator" not decorator(f)
    return permission_required(Permission.ADMIN)(f) 
```
<br>

Now, a page for 403 eror should be added:<br>
app/templates/403.html
```html
{% extends "base.html" %}

{% block title %}Vertica - Forbidden{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Forbidden</h1>
</div>
{% endblock %}
```
<br>

The following are two examples of how you use these decorators:
```python
from .decorators import admin_required, permission_required

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return "For administrators!"

@main.route('/moderate')
@login_required
@permission_required(PERMISSION.MODERATE)
def for_moderators_only():
    return "For comment moderators!"
```
As a rule of thumb, the ***@blueprint.route*** decorator from Flask should be given first. And the remaining decorators should be given in the order in which they need to evaluate when the view function is invoked. In this case, user authentication needs to be checked first since the user needs to be redicreted if not authenticated. <br><br>

Permission may also need to be checked from templates, so the Permission class with all its constants needs to be accessible to them. If you had to add a template argument in every render_template() call, it would be tedious and error-prone. To avoid it, a ***context processor*** can be used. What they do is make variables available to all templates during rendering.<br><br>

*app/main/\_\_init\_\_.py*
```python
from flask import Blueprint

main = Blueprint('main', __name__)

from ..models import Permission

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

from . import views, errors
```
<br>

Don't forget to test things out as well.<br>
*tests/test_user_model.py*
```python
import unittest
from app.models import User,AnonymousUser,Role,Permission
class UserModelTestCase(unittest.TestCase):
    #...
    def test_user_role(self):
        u = User(email ="john@example.com", password="cat") #assign default role
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))
    
    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))
```

Before you move on, add the new roles to your development database in a shell session.<br>
Plus, it's also good idea to update the user list so that all the user accounts that were created before roles and permissions existed have a role assigned.<br>

*flash shell*:
```python
>>> Role.insert_roles()
>>> Role.query.all()
[<Role 'Administrator'>, <Role 'User'>, <Role 'Moderator'>]

>>> admin_role = Role.query.filter_by(name="Administrator").first()
>>> default_role = Role.query.filter_by(default=True).first()
>>> for u in User.query.all():
...     if u.role is None:
...         if u.email == app.config["ADMIN"]:
...             u.role = admin_role
...         else:
...             u.role = default_role
...
>>> db.session.commit()
```



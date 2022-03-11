from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from enum import Enum, IntEnum,auto
from datetime import datetime
import json
from .execs import RedisDirector,ElasticDirector


class User(UserMixin, db.Model):
    __tablename__ = "users"
    username = db.Column(db.String(64),index=True)
    id = db.Column(db.Integer, primary_key=True)
    operations = db.relationship("Operation", backref="user",lazy="dynamic")
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    email = db.Column(db.String(64),unique=True,index=True)
    password_hash = db.Column(db.String(128))

    location= db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)
    
      #confirmed status
    confirmed = db.Column(db.Boolean, default=False)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()


    #role assignment
    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email in current_app.config["ADMINS"]:
                self.role = Role.query.filter_by(name="Admin").first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
    
    def can(self,perm):
        return self.role is not None and self.role.has_permission(perm)
    def is_administrator(self):
        return self.can(Permission.ADMIN)
    # ---------------------

    def __repr__(self):
        return "<User %r>" % self.username
    
    @property
    def password(self):
        raise AttributeError("Not Readable Attribute")
    
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def generate_confirmation_token(self,expiration=300):
        s = Serializer(current_app.config["SECRET_KEY"],expiration)
        return s.dumps({"confirm":self.id}).decode("utf-8") #PK of this instance
    
    def confirm(self,token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True  #confirmed. Not confirm.
        db.session.add(self)
        return True

class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False
    def is_administrator(self):
        return False

#Operation part
class Executable(Enum):
    ROLLING_RESTART=auto()
    FILE_TRANSER=auto()

class Execution(db.Model):
    __tablename__= "executions"
    id= db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    operations = db.relationship("Operation",backref="execution",lazy="dynamic")
    solution= db.Column(db.String(64))
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
    def __repr__(self):
        return "<Execution %r>" % self.name
    
    @staticmethod
    def remove_execution(exec_name,solution):
        exec = Execution.query.filter_by(name=exec_name,solution=solution).first()
        if exec : 
            db.session.delete(exec)
            db.session.commit()
    
    @staticmethod
    def insert_execution():
        REDIS= RedisDirector.construct() #dict - solution, execution
        ELASTIC = ElasticDirector.construct() #dict 
        SOLUTIONS=[REDIS,ELASTIC]
        for sol in SOLUTIONS:
            for exe in sol["execution"]:
                execution = Execution.query.filter_by(name=exe,solution=sol["solution"]).first()
                if execution is None:
                    execution = Execution(name=exe,solution=sol["solution"])
                db.session.add(execution)
            db.session.commit()
                
    
    
class Operation(db.Model):
    __tablename__ = "operations"
    id = db.Column(db.Integer,primary_key=True)
    timestamp= db.Column(db.DateTime,index=True,default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    exec_id = db.Column(db.Integer, db.ForeignKey("executions.id"))
    cluster = db.Column(db.String(64))
    #user
    #exeuction
    def __repr__(self):
        return "<Operation %r %r>" % self.user.username, self.execution.name
    def to_dict(self):
        return {
            "id":self.id,
            "timestamp":self.timestamp,
            "user":self.user.username,
            "execution":self.execution.name,
            "email":self.user.email,
            "solution":self.execution.solution,
            "cluster":self.cluster
        }
#----------------------------    
    
    
# To load "a" user, we need to define
# User loading function 
@login_manager.user_loader 
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.anonymous_user=AnonymousUser


class Permission(IntEnum):
    READ =1
    WRITE= 2
    EXECUTE =4 
    ADMIN = 8


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)
    default = db.Column(db.Boolean,default=False,index=True)
    permissions = db.Column(db.Integer)
    
    # One user will have one role while one role will have
    # A lot of users
    users = db.relationship("User",backref="role",lazy="dynamic")
    def __init__(self,**kwagrs):
        super(Role,self).__init__(**kwagrs)
        if self.permissions is None:
            self.permissions=0
    
    def __repr__(self):
        return "<Role {}>".format(self.name)

    def has_permission(self,perm):
        return self.permissions & perm == perm

    def add_permission(self,perm):
        if not self.has_permission(perm):
            self.permissions += perm
    def remove_permission(self,perm):
        if self.has_permission(perm):
            self.permissions -= perm
    def reset_permissions(self):
        self.permissions=0

    @staticmethod
    def insert_roles():
        roles = {
            "User":[Permission.READ],
            "Admin":[PERMISSION for PERMISSION in Permission]
        }
        default_role="User"
        for r in roles.keys():
            role = Role.query.filter_by(name=r).first()
            
            #if role has yet been registered,
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            
            #To set role's default
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()


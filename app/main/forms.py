from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField,BooleanField,SelectField,ValidationError,SelectMultipleField,widgets
from wtforms.validators import DataRequired,Length,Email,Regexp
from app.models import User,Role,Execution
import os
import json


class NameForm(FlaskForm):
    name = StringField("What's your name?", validators=[DataRequired(),Length(1,20)])
    submit= SubmitField("Submit")

class SearchForm(FlaskForm):
    searchword = StringField("Search",validators=[DataRequired(),Length(1,64),Email()])
    submit_search=SubmitField("Search")

class EditProfileForm(FlaskForm):
    location = StringField("Location", validators=[Length(0,64)])
    about_me = TextAreaField("About_Me")
    submit = SubmitField("Submit")

    
class EditProfileAdminForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(),Length(1,64),Email()])
    username = StringField("Username",validators=[
        DataRequired(),
        Length(1,64), 
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0)])
    confirmed = BooleanField("Confirmed")
    role = SelectField("Role",coerce=int)
    location = StringField("Location",validators=[Length(0,64)])
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
        if field.data != self.user.username and \
            User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already in use")
        

class OperationForm(FlaskForm):
    execution = SelectField("Execution",coerce=int)
    submit =SubmitField("Go!")
    
    def __init__(self,*args,**kwargs):
        super(OperationForm,self).__init__(*args,**kwargs)
        self.execution.choices = [(exe.id,exe.name) for exe in Execution.query.filter_by(solution=kwargs["solution"]).order_by(Execution.name).all()]

class ConfigurationForm(FlaskForm):
    submit = SubmitField("Go!")
    def __init__(self,dic:dict):
        super(ConfigurationForm,self).__init__(dic)
        for k,v in dic.items():
            setattr(self,k,StringField("",default=v,render_kw={"placeholder": "{}".format(v)})) #To insert place holder

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class ClusterForm(FlaskForm):
    cluster = SelectField(coerce=str)
    def __init__(self,*args,**kwargs):
        super(ClusterForm,self).__init__(*args,**kwargs)
        
        self.cluster.choices =[(None,"Choose")]+ [(cluster,cluster) for clusters in json.loads(os.getenv("SOLUTION")).values()
                                                for cluster in clusters.keys()]

    @classmethod
    def node_checkbox(cls,clustername):
        cls.nodes=SelectField(coerce=str)
        cls.nodes.choices=[(node,node)for _,node in zip(range(1000),*[clusters.get(clustername) for clusters in json.loads(os.getenv("SOLUTION")).values() if clusters.get(clustername)])]

        return cls
    

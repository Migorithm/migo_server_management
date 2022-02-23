### Web forms
With HTML, it is possible to create web forms, in which users can enter information. The form data is then submitted by the web browser to the server, typically in the form of a POST request. The Flask ***request*** object exposes all the information sent by the client and provides access to the user information through ***request.form***.
<br><br>
Although the support provided in Flask’s request object is sufficient for the handling of web forms it may become soon tedious and repetitive. Two good examples are:
- generation of HTML code for forms
- validation of the submitted form data 

***Flask-WTF*** extension makes working with web forms a much more pleasant experience.

### Configuration
Flask-WTF does not need to be initialized at the appli‐ cation level, but it expects the application to have a ***secret key*** configured:
```python
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
```
The app.config dictionary is a general-purpose place to store configuration variables used by Flask. The configuration object also has methods to import configuration values from other object as follows:
```python
from flask import Flask
app = Flask(__name__)
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

app.config.from_object(Config)
```
Flask-WTF requires a secret key to be configured in the application because ***this key is part of the mechanism the extension uses to protect all forms against cross-site request forgery (CSRF)*** attacks. <br>

For your information, CSRF is a malicious exploit of a website where unauthorized commands are submitted from a user that the web application trusts. This is done by hacker who forges a request for a fund transfer to a website by embedding the request into a hyperlink and sending it to visitors who may be logged into the site. ***Flask-WTF generates security tokens for all forms and stores them in the user session***, which is protected with a cryptographic signature generated from the secret key.

### Form classes
Each web form is represented in the server by a class that inherits from the class FlaskForm.
```python
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField from wtforms.validators import DataRequired
    class NameForm(FlaskForm):
        name = StringField('What is your name?', validators=[DataRequired()]) 
        submit = SubmitField('Submit')
```
- labels: The first argument to the field constructors("What's your name" and "Submit") is the ***label*** that will be used when rendering the form to HTML.
- validators: The DataRequired() validator ensures that the field is not submitted empty.
<br>

The list of HTML fields supported by WTForms is shown below:
- BooleanField          : Checkbox with True and False values
- DateField             : Text field that accepts datetime.date value in a given format
- DateTimeField         : Text field that accpets datetime.datetime 
- FileField             : File upload field
- MultipleFileField     : Multiple file upload field
- PasswordField
- RadioField
- SelectField           : Drop-down list of choices
- SubmitField           : Form submission button
- StringField           : Text field
<br>

The list of validators follows:
- DataRequired          : Validates that the field contains data after type conversion.
- Email                 : Validates an email address
- EqualTo               : Compares the values of two fields
- InputRequired         : Validates that the field contains data before type conversion
- IPAddress             : Validates an IPv4 network address
- Length                : Validates the length of the string entered
- MacAddress            : Validates a MAC address
- NumberRange           : Validates that the value entered is within a numeric range
- Regexp                : Validates the input against a regular expression
- URL                   : Validates a URL


### HTML rendering of forms and Form Handling in view functions
Form fields are callables that, when invoked from a template, render themselves to HTML. Assuming that the view function passes a **NameForm** instance to the template as an argument named myform, the template can generate a simple HTML form as follows:
```html
<form method="POST">
    {{ myform.hidden_tag() }}
    {{ myform.name.label }} {{ myform.name() }} {{ myform.submit() }}
</form>
```
Note that form has a form.hidden_tag() element. This element defines an extra form field that is hidden, used by Flask-WTF to implement CSRF protection.<br>

But with the above approach, there is way too many works so it would be better if we could leverage Bootstrap's own set of form styles, and there is!:
```html
{% import "bootstrap/wtf.html" as wtf %}
{{ wtf.quick_form(myform) }}
```
The import directive works in the same way as regular Python script do. <br>
The wtf.quick_form() function takes a Flask-WTF form object and renders it using default Bootstrap style.<br><br>

Let's a look at how what we've discussed can be implemented below:
```html
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}
{% block page_content %}
<div class="page-header">
    <h1>Hello, {% if name %}{{name}}{% else %}Stranger{% endif %}!</h1>
</div>
{{ wtf.quick_form(form) }}
{% endblock %}
```

```python
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired
app = Flask(__app__)
bootstrap = Bootstrap(app)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

class NameForm(FlaskForm):
    name = StringField("What's your name?", validators=[DataRequired()])
    submit= SubmitField("Submit")

@app.route('/',methods=["GET","POST"])
def index():
    name =None
    form = NameForm()
    if form.validate_on_submit():
        name= form.name.data
        form.name.data=''
    return render_template("index.html",form=form,name=name)
```
- ***methods*** argument added to the app.route decorator tells Flask to register the view function as a handler for GET and POST requests in the URL map.
- The local name variable is used to hold the name received from the form when available.
- validate_on_submit() method of the form returns True when the form was submitted and the data was accepted by all the field validators. 
- ***form.name.data=''*** - is used so that the field is blanked when the form is rendered again.
- If the user submits the form with an empty name, the DataRequired() validator catches the error.
<br>
When a user navigates to the application for the first time, the server will receive a GET request with no form data; therefore False to be set for ***validate_on_submit()***

### Redirect and User Sessions
The last version has a *usability* problem. If you enter the name and submit then click the refresh button in your browser, you'll likely get an warning. This happens because browsers repeat the last request when they're asked to refresh a page.<br><br>

When the last request sent is a POST request with form data, a refresh would cause a duplicate form submission, which in almost all cases is not the desired action. It is therefore considered good practice for web applications to NEVER leave a POST request as the last request.<br><br>

This is achieved by responding to POST requests with a ***redirect*** instead of a normal response. When the browser receives a redirect response, it issues a *GET* request for the redirect URL, and that is the page that it displays. And now the last request is a GET as opposed to POST, the refresh command will work as expected. This trick is known as ***POST/Redirect/GET*** pattern.<br><br>

But this approach brings a second problem - as soon as that request ends, the form data is lost. So the application needs to store the name so that the redirected request can have it and use it to build the actual response. <br><br>

Applications can “remember” things *from one request to the next* by storing them in the user session, which is a private storage that is available to each connected client. Yes, session is one of the variables associated with the ***request context***. By default, user sessions are stored in client-side cookies and any tampering with the cookie content would render the signature invalid, thus invalidating the session.<br>

Look at the changes made to index() view function:
```python

from flask import Flask, render_template, session, redirect, url_for
@app.route('/',methods=["GET","POST"])
def index():
    form = NameForm()
    if form.validate_on_submit():
        session["name"]=form.name.data
        return redirect(url_for('index'))
    return render_template("index.html",form=form,name=session.get("name",None))
```
Note the followings:
- how session[ 'name' ] was used so it is remembered beyond the request.
- redirect() takes the URL to redirect to as an argument.
- render_template() now obtains the name argument directly from the session using .get method. Doing so enables avoiding an exception for keys that aren't found.

### Message Flashing
To give the user a *status update* after a request is completed, such as confirmation message, warning or an error you can use flash() function.<br>

Let's see how message can be flashed
```python
@app.route('/',methods=["GET","POST"])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name= session.get("name")
        if old_name is not None and old_name != form.name.data:
            flash("Name change has been detected!")
        session["name"]=form.name.data
        return redirect(url_for('index'))
    return render_template("index.html",form=form,name=session.get("name",None))
```
In this example, each time a name is submitted it is compared against the name stored in the user session. If the two names are different, the flash() function is invoked with a message ***to be displayed on the next response*** sent back to the client.<br><br>

Calling flash() is not enough; template also decides where you will place the flashed message:
```html
{% block content%}
    <div class="container">
        {% for message in get_flashed_messages() %}
        <div class="alert alert-info">
            <button type="button" class="close" data-dissmiss="info">&times;</button>
            {{message}}
        </div>
        {% endfor %}
        {% block page_content %}{% endblock %}
    </div>
{% endblock %}
```
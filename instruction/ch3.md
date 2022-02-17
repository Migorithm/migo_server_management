## Template
Mixing business logic and presentation logic could lead to unintelligible code.<br>
A template is a file that contains the text of a response, with ***placeholder variables*** for<br>
dynamic parts. The process that replaes the variables with actual values and return a final<br>
string is called ***rendering***. For that specific task, Flask uses Jinja2

### rendering_template
```python
from flask import Flask, render_template

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)
```

#### Q1. Wait, **how does Flask find 'index.html' and 'user.html'? From where?** <br>
By default, Flask looks for template in a *templates* subdirectory located *inside* main application directory.

#### Q2. Additional argument shown in the view function, user?
These arguments are key-value pairs passed into template. "name" on the left represents the argument name which is used in the placeholder in the templat and "name" on the right is variable in current scope that provides the actual value. Let's see the template using this variable:

*template/user.html*
```html
<h1>Hello, {{ name }}!</h1>
```

### Variables
Jinja2 recognizes variables of any type, even complex types such as lists, dictionaries, and objects. For example:
```html
<p>A value from a dictionary: {{ mydict['key'] }}.</p>
<p>A value from a list: {{ mylist[3] }}.</p>
<p>A value from a list, with a variable index: {{ mylist[myintvar] }}.</p> 
<p>A value from an object's method: {{ myobj.somemethod() }}.</p>
```
<br>

Variables can be modified with filters, which are added after the variable name with a pipe character(|) as separator. For example, the following template shows the name variable capitalized:
```html
Hello, {{ name|capitalize }}
```

### Control Structures 
#### Conditional Statements
```html
{% if user %}
    Hello, {{ user }}!
{% else %}
    Hello, Stranger!
{% endif %}
```

#### For loop 
```html
<ul>
    {% for comment in comments %}
    <li>{{ comment }}</li> 
    {% endfor %}
</ul>
```

#### Inheritance
Portions of template code that need to be repeated can be stored in a separate file and *included* from all the other templates to avoid repetitions. So first, we create a base template with the name ***base.html***:
```html
 <html>
    <head>
        {% block head %}
        <title>{% block title %}{% endblock %} - My Application</title> 
        {% endblock %}
    </head>
    <body>
        {% block body %}
        {% endblock %}
    </body>
</html>
```
<br>
Base templates defines ***block*** that can be overriden by "child" templates. The Jinha2 block and endblock directives defines blocks of content that are added to the base template. The following child template will extend this base template:
```html
{% extends "base.html" %}
{% block title %}Index{% endblock %}
{% block head %}
    {{ super() }}
    <style>
    </style>
{% endblock %}
{% block body %} 
<h1>Hello, World!</h1> 
{% endblock %}
```
When a block has some content in both the base and derived templates, the content from the derived template is used. If you want to keep the contents of base template, you can call {{ super() }} to reference the contents of the block in the base template. Plus, the order of block actually doesn't affect the presentation. 

### Bootstrapping
Even with the existence of flask-bootstrap, I am going to use normal bootstrap so that<br>
I can take dependency off the framework with more freedom.

*base.html*
```html
<!DOCTYPE html>
<html>
    <head>
        <!-- bootstrap link -->
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <!-- This is where you put image for the title -->
        <link rel="shortcut icon" href="{{ url_for('static', filename='favicon_wmp.ico') }}" type="image/x-icon">
        <link rel="icon" href="{{ url_for('static', filename='favicon_wmp.ico') }}" type="image/x-icon">    
        <title>
            {% block title %}Vertica Management{% endblock %}
        </title>
    </head>
    <body>
  
        {% block content%}{% endblock %}

        <!-- jquery and javascript link -->
        <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    </body>
</html>
```

### Custom error pages
When you enter an invalid route in our browser's address bar, you get a code 404 error page.<br>
Flask allows an application to define custom error pages that can be based on templates. The two most common error codes are:
- 404(Not Found)
- 500(unhandled exception)
The following shows how to provide custom handlers:
```python
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
```
Note that responding to client, these hanlders also return numeric status code.<br>

base template for error hanlders is as follows:
*errorbase.html*
```html
<!DOCTYPE html>
<html>
    <head>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <link rel="shortcut icon" href="{{ url_for('static', filename='favicon_wmp.ico') }}" type="image/x-icon">
        <link rel="icon" href="{{ url_for('static', filename='favicon_wmp.ico') }}" type="image/x-icon">    
        <title>     
            {% block title %}Vertica Management{% endblock %}
        </title>
    </head>
    <body>
        {% block content%}
        <div class="container">
            {% block page_content %}{% endblock %}
        </div>
        {% endblock %}
    </body>
</html>
```

The content block of this template is just a container < div > element that wraps a new empty block called page_content. Error handling pages will now inherit from this template:
<br>
*404.html*
```html
{% extends "errorbase.html" %}
{% block title %}Vertica - Internal Error{% endblock %}
{% block page_content %}
<div class="jumbotron">
    <h1>Unhandled Exception Occurred</h1>
    <p>
        Please contact any of the people listed below<br>
        <ul class="list-group">
            {% for admin in admins %}
            <li class="list-group-item" style="color:gray">{{ admin }}</li>
            {% endfor %}
          </ul>
    </p>
</div>
{% endblock %}
```

### Links
For dynamic routes with variable portions it can get complicated to build the URLs in the template. Also, URLs written *directly* in template can create dependency on the routes defined in the code, meaning that if the routes are reorganized, liks in template may break.<br><br>

To avoid these problems, Flask provides the ***url_for*** which generate URLs from application's *URL map*. what ***url_for*** does is:
- take view function name such as 'index'
- return its relative URL, which is in this example '/'
- To get absolute URL, call ***url_for('index',_external=True)*** and then it will return "http://localhost:5000/"
- For dynamic urls, you can pass in arguments as well by saying ***url_for('user',name="Migo",_external=True)***. It will then return "http://localhost:5000/user/Migo"


### Localization of Dates and Times with Flask-Moment
Server needs uniform time units; therefore UTC is used. For users, however, we need to convert them into local time. A solution is to send UTC time units to the web browser. Web browsers can do a much better job at this task because they have access to time zone on user's computer.<br><br>

There is an open source library that renders dates and times in the browser called ***Moment.js***. Flask-Moment is an extension to integrate Moment.js into Jinja2:
```python
from flask_moment import Moment
from datetime import datetime
moment = Moment(app)

@app.route('/')
def index():
    return render_template("index.html",current_time=datetime.utcnow())

```
Flask-Moment depends also on jQuery.js in addition to Moment.js(which we've already included)<br>
<br>

To work with timestamps, Flask-Moment makes a ***moment*** object available to templates. 
```
{% block scripts %}
    {{ moment.include_moment() }}
{% endblock %}
```

Let's pass variable called current_time to index.html template for rendering
```html
{% extends "base.html" %}
{% block page_content %}
<p>The local date and time is {{ moment(current_time).format('LLL') }}</p>
<p>That was {{ moment(current_time).fromNow(refresh=True) }}</p>
{% endblock %}
```
The ***format('LLL')*** method renders the date and time according to the time zone and local settings in the client computer. The argument determines the rendering style, from 'L' to 'LLLL' for four different levels of verbosity. ***fromNow()*** method renders a relative timestamp and automatically refreshes it as time passes. A language also can be selected by passing two-letter language code to function ***locale()***, right after the Moment.js library is included:

``` 
{% block scripts %}
    {{ moment.include_moment() }}
    {{ moment.locale('kr') }}
{% endblock %}

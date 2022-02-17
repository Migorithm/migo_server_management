## Basics

### Initialization of app
```python
from flask import Flask
app=Flask(__name__)
```
\_\_name\_\_ is used to determine the location of the application, which in turn allows it to locate other files such as images and templates.

### View functions
```python
from flask import Flask
app=Flask(__name__)

@app.route('/')
def index():
    return "<h1>Hello World!</h1>"
```
Tihs registers function ***index()*** as the handler for the application's root URL. Traditionally it was written as follows:

```python
def index():
    return "<h1>Hello World!</h1>"
app.add_url_rule('/','index',index) 
                #URL, endpoint name, view function in order
```

#### Dynamic routes
```python
@app.route('/user/<name>')
def index():
    return "<h1>Hello World!</h1>"
```

### flask run command
This command looks for the name of Python script that contains the application instance in the FLASK_APP environment variable. To start with:
```sh
$ export FLASK_APP=hello.py
$ flask run
```
<br>

Alternatively;
```python
if __name__ == "__main__":
    app.run(host="0.0.0.0",,port=41410,debug=True)
```
Debug mode allows auto-reloading and debugging. But never use debug mode on production server as it allows the client to request remote code exeuction, resulting in vulnerability.

## Request - Response Cycle
### Application and Request Contexts
Flask uses ***context*** to temporarily make certain objects globally accessible.
For example, *request* object encapsulates the HTTP request sent by the client.
```python
from flask import request
@app.route('/')
def index():
    user_agent = request.headers.get("User-agent")
```
Note how request is used as if it were a global variable. In reality, in a multithreaded serer, several threads can be working on different requests from different clients all at the same time, so each thread needs to see a different object in request. Contexts are what make this possible.

### Type of context
- application context 
    - current_app   : The application instance for the active application
    - g             : Where you store temporary data. This variable is reset with each request.
- request context
    - request       : What encapsulates the contents of HTTP
    - session       : The user session, a dictionary that application can use to store values that are "remembered."

### Demonstaration of how application context works
```python
>>> from hello import app
>>> from flask import current_app
>>> current_app.name #error out

>>> app_context = app.app_context()
>>> app_context.push() #Push the app context, then you can use current app
>>> current_app.name
'hello'
>>> app_context.pop() #Pop the app context
```

### Request Dispatching
When receiving request, Flask looks up the URL in the application's URL map<br>
Flask builds this map using the data provided in the app.route.decorator:
```python
>>> from hello import app
>>> app.url_map
Map([<Rule '/' (HEAD, OPTIONS, GET) -> index>,
 <Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
 <Rule '/user/<name>' (HEAD, OPTIONS, GET) -> user>])
```
/static/< filename > route is a special route added by Flask to give access to static files.<br>
HEAD and OPTIONS are managed automatically by Flask.<br>
So in practice what you need to care is only methods and view function name<br>

### Request Hooks
Sometimes it is useful to execute code before or after each request is processed.<br>
The proper example is, when you need to create DB connection or authenticate users.<br>
Request hooks are implemented as decorators. These are the four hooks supported by Flask:
- before_request        : run before each request
- before_first_request
- after_request         : run after each requets (unless unhandled exception occurred)
- teardown_request      : run after each request even if unhandled exception occurred

For examle, *before_request* handler can load the logged-in user from the database and<br>
store it in g.user. 

### Responses
#### Response object
```python
@app.route('/')
def index():
    return "<h1>Bad request</h1>",400
```
Note that status code is set to 200(default to 400).<br>
And It can be added as a ***second return value***.<br>

Instead of returning one, two, or three values as a tuple,<br>
Flask view functions have the option of returning a response object
```python
from flask import make_response

@app.route('/') 
def index():
    response = make_response('<h1>This document carries a cookie!</h1>') 
    response.set_cookie('answer', '42')
    response.status_code(200)
    return response
```

#### Redirect
```python
from flask import redirect
@app.route('/')
def index():
    return redirect("http://www.example.com")
```

#### abort
```python
from flask import abort
@app.route('/user/<id>')
def user(id):
    user = load_user(id)
    if not user:
        abort(404)
    return '<h1>Hi!</h1>'
```
Note that *abort()* doesn't return control back to the function because it raises<br>
an exception.

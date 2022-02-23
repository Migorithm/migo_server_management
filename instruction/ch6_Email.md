## Email

### Email support with Flask-Mail
```sh
pip install flask-mail
```
The extension connects to SMTP server. If no configuration is given, Flask-mail connects to *localhost* at port 25. The following shows the list of configuration keys that can be used to configure the SMTP server. 
- MAIL_SERVER   : default to localhost, Hostname or IP address of email server
- MAIL_PORT     : default to 25, Port of the email server
- MAIL_USE_TLS  : default to False, Enable Transport Layer Security(TLS)
- MAIL_USE_SSL  : default to False, Enable Secure Socket Layer(SSL) security
- MAIL_USERNAME : default to None, Mail account username
- MAIL_PASSWORD : default to None, Mail account password


#### On Development environment
If you are in the middle of development, it may be more convenient to connect to external SMTP server like Google:
```python
import os
# ...
app.config['MAIL_SERVER'] = 'smtp.googlemail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True 
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') 
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
```
Again, you don't want to write account credential directly in your scripts. To protect your account info, have your script import sensitive information from environment variables. Plus, Gmail accounts are configured to require external applications to use OAuth2 authentication to connect to the email server. Python's smtplib library doesn't support this yet. To make your Gmail accpet standard SMTP authentication, go to *GOogle account settings page* and select ***"Signing in to Google"*** from the left menu bar. On that page, locate ***"Allow less secure apps"***

### Flask-Mail initialization
```python
from flask_mail import Mail
mail = Mail(app)
```

#### Holding email server username and password in environment
```sh
export MAIL_USERNAME=<mail username>
export MAIL_PASSWORD=<mail password>
```

### Sending Email from the Python shell
```python
$ flask shell
>>> from flask_mail import Message
>>> from hello import mail
>>> msg = Message('test email', sender='you@example.com', ... recipients=['you@example.com'])
>>> msg.body = 'This is the plain text body'
>>> msg.html = 'This is the <b>HTML</b> body'
>>> with app.app_context():
... mail.send(msg)
...
```
Note that Flask-Mail's send() function uses ***current_app***, so it needs to be executed with an activated application context.<br>
Message function takes:
- subject
- sender
- recipients 
And it has contents part which can be composed of html body and just normal body. 


### Integrating Emails with the Application
Let's abstract the common parts of the application's email sending functionality into a function
```python
from flask_mail import Message 
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <flasky@example.com>'
def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)
```
There are two application-specific configuration kyes that define a prefix string for the subject and the address that will be used as the sender.<br>
The template name must be given without the extension, so that two versions of the template can be used for the plain text and HTML bodies.<br>

***View function*** that will serve mailing service will look like this:
```python
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))
```

***Templates*** are as follows:
*templates/mail/new_user.html templates/mail/new_user.txt*
```html
User <b>{{ user.username }}</b> has joined.
```
```txt
User {{ user.username }} has joined.
```
- The recipient of the email is given in the FLASKY_ADMIN environment variable. 
- Two template files needs to be created for the text and HTML versions. 
    - As this templates expect the user to be given as a template argument, send_email() includes it as a keyword argument(\*\*kwargs\*\*)

Don't forget to set environmental variable for FLASKY_ADMIN:
```sh
export FLASKY_ADMIN=<"your-email-address">
```

### Sending Asynchronous Email
If you sent a few test emails, you likely noticed that the mail.send() function blocks for a few seconds while the email is sent, making the browser look unresponsive during that time. To avoid unnecessary delays during request handling, the email send function can be moved to a background thread. 
```python
from threading import Thread
def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwagrs):
    msg = Message(app.config["Flasky_MAIL_SUBJECT_PREFIX"]) + subject, \
                    sender = app.config["FLASKY_MAIL_SENDER"], recipients=[to])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_tempalte(template + ".html", **kwargs)
    thr = Thread(target = send_async_email,args=[app,msg])
    thr.start()
    return thr
```
Why do we have to pass 'app' as an argument? <br>
Many Flask extensions oper‐ ate under the assumption that there are active application and/or request contexts.<br>
Flask-Mail’s send() function uses current_app, so it requires the application context to be active.<br>
But since contexts are associated with a thread, when the mail.send() function executes in a different thread<br>
it needs the application context to be created artificially using app.app_context().<br><br>

If you run the application now, you will notice that it is much more responsive, but keep in mind that for applications that send a large volume of email, having a job dedicated to sending email is more appropriate than starting a new thread for each email send operation. For example, the execution of the send_async_email() func‐ tion can be sent to a Celery task queue.



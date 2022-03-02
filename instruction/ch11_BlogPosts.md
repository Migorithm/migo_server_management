## Blog Posts

This chapter is dedicated to the implementation of main feature. Here I will cover new techniques for:
- reuse of templates
- pagination 
- working with rich text

### Blog Post Submission and Display
To support blog posts, a new database model that represents them is necessary.<br>
*app/models.py*: 
```python
class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

class User(UserMixin, db.Model):
    #...
    posts = db.relationship("Post", backref="author",lazy="dynamic")
```
<br>

And the form that will be shown in the main page lets users write a blog post.<br>
*app/main/form.py*:
```python
class PostForm(FlaskForm):
    body = TextAreaField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField("Submit")
```
<br>

The ***index()*** view function handles the form and passes the list of old blog posts to the templates.<br>
*app/main/views.py*:
```python
@main.route('/', methods=["GET","POST"])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit(): 
        post = Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for(".index"))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html',form=form,posts=posts)
```
This view function passes the form and the complete list of blog posts to the template. The list of posts is ordered by timestamp, in descending order. The current user's permission to write article is checked before allowing the new post.<br><br>

Note how the ***author*** attribute of the new post object is set to the expression ***current_user._get_current_object()***. The ***current_user*** variable is implemented as a ***thread-local proxy*** object. Although this object behaves like a user object but is really a thin wrapper that contains the actual user obejct inside. The database needs a real user object, which is obtained by calling ***_get_current_object()*** on the proxy object. <br><br>

For your information, a thread local is a global object in which you can put stuff in and get back later in a thread-safe and thread-specific way.<br><br>

The form is rendered below.<br>
*app/templates/index.html*:
```html
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}

{% block title %}Flasky{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Hello, {% if current_user.is_authenticated %}{{ current_user.username }}{% else %}Stranger{% endif %}!</h1>
</div>
<div>
    {% if current_user.can(Permission.WRITE) %}
    {{ wtf.quick_form(form) }}
    {% endif %}
</div>
<ul class="posts">
    {% for post in posts %}
    <li class="post">
        <div class="post-thumbnail">
            <a href="{{ url_for('.user', username=post.author.username) }}">
                <img class="img-rounded profile-thumbnail" src="{{ post.author.gravatar(size=40) }}">
            </a>
        </div>
        <div class="post-content">
            <div class="post-date">{{ moment(post.timestamp).fromNow() }}</div>
            <div class="post-author"><a href="{{ url_for('.user', username=post.author.username) }}">{{ post.author.username }}</a></div>
            <div class="post-body">{{ post.body }}</div>
        </div>
    </li>
    {% endfor %}
</ul>
{% endblock %}
```
Note that the ***User.can()*** method is used to skip the blog post form for those who don't have the right Permission.<br>

### Blog Post on Profile Pages
You can let a user see posts written by themselves on profile page.<br>
*app/main/views.py*:
```python
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template("user.html",user=user,posts=posts)
```

Here, the *user.html* template needs < ul > HTML tree just as in index.html.<br>
But having to maintain two identical copies of a piece of HTML code is not ideal.<br>
For cases like this, Jinja2's ***include*** directive is very useful.<br>
*app/templates/_posts.html*:
```html
<ul class="posts">
    {% for post in posts %}
    <li class="post">
        <div class="post-thumbnail">
            <a href="{{ url_for('.user', username=post.author.username) }}">
                <img class="img-rounded profile-thumbnail" src="{{ post.author.gravatar(size=40) }}">
            </a>
        </div>
        <div class="post-content">
            <div class="post-date">{{ moment(post.timestamp).fromNow() }}</div>
            <div class="post-author"><a href="{{ url_for('.user', username=post.author.username) }}">{{ post.author.username }}</a></div>
            <div class="post-body">{{ post.body }}</div>
        </div>
    </li>
    {% endfor %}
</ul>
```
<br>

And the following is ***app/templates/user.html*** that use ***include*** to incorporate the copy.
```html
...
<h3>Posts by {{user.username}}</h3>
{% include '_posts.html' %}
...
```

### Paginating Long Blog Post Lists
As the site grows, it will become slow and impratical to show the complete list of posts.<br>
The solution is to ***paginate*** the data and render it in chunks. <br>

#### Creating Fake Blog Post Data
To work with multiple pages, it's necessary to have a test database. Manually adding new database entries is time consuming and tedious; so I'm going to use automated solution: Faker.<br>
```sh
$ pip install faker
```
<br>

The following shows a new module added to the application that contains two functions that generates fake users and posts.<br>
***app/fake.py***:
```python
from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User,Post

def users(count=100):
    fake = Faker()
    i = 0
    while i < count : 
        u = User(email= fake.email(),
                 username= fake.user_name(),
                 password='password',
                 confirmed=True,
                 name=fake.name(),
                 location=fake.city(),
                 about_me=fake.text(),
                 member_since=fake.past_date())
        db.session.add(u)
        try:
            db.session.commit()
            # email address must be unique but since Faker generates thigns
            # randomly, it must be handled by try-exception 
            # In case of error, database will  throw IntegrityError
        except IntegrityError:
            db.session.rollback()

def posts(count=100):
    fake = Faker()
    user_count= User.query.count()
    for i in range(count):
        #To select the random user, offset and randint are used
        u = User.query.offset(randint(0,user_count -1)).first()
        p =  Post(body=fake.text(),
                  timestamp=fake.past_date()
                  author=u)
        db.session.add(p)
    db.session.commmit()
```
<br>

The new functions make it easy to create a large number of fake users and posts from the Python shell; flask shell:<br>
```python
>>> from app import fake
>>> fake.users(100)
>>> fake.posts(100)
```
If you run the application now, you will see a long list of random blog posts on the home page, by many different users.<br>


#### Rendering in Pages
The following shows the changes to the home page route to support pagination.<br>
*app/main/views.py*:
```python
@main.route('/',methods=["GET","POST"])
def index():
    #...
    page = request.args.get('page',1,type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config["POSTS_PER_PAGE"],
        error_out=False)
    posts = pagination.items
    return render_template('index.html',form=form,posts=posts,pagination=pagination)
```

The Page number to render is obtained from the request's query string. When a page is not given, a default page of 1 is used. The ***type=int*** argument ensures that if the argument cannot be converted to an integer(passing "one", for example), default value is returned. <br><br>

To load a single page of records, the final call ***.all()*** is replaces with ***.paginate()*** which takes:
- (required) page number
- (optional) per_page 
- (optional) error_out. 
    - If it's True, 404 code will be issued against requests for page outside the valid range. 
    - If it's False, pages outside the range are returned with empty list of items 
<br>

With these changes, the blog post list on the home page will show a limited number of items. To see the second page of posts, add a *page=2* query string to the URL in the address bar. 

#### Adding a Pagination Widget
The return value of *paginate()* is an object of class Pagination. This object contains several properties(attributes) and methods as follows:
- ***Attributes***
    - items     : The records in the current page
    - query     : The source query that was paginated
    - page      : The current page number
    - next_num  : The next page number
    - prev_num  : The previous page number
    - pages     : The total number of pages for the query
    - total     : The total number of items returned by the query.
- ***Methods***
    - iter_pages(left_edge=2,left_current=2,right_current=5,right_edge=2) : With these values, for page 50 of 100, this iterator will return the following pages: 1,2,None,48,49,50,51,52,53,54,55, None,99,100.
    - prev()    : A pagination object for the previous page
    - next()    : A pagination object for the next page
<br>

With this powerful ojbect, it's quite easy to build a pagination fotter in the template. The implementation shown below is done as a reusable Jinja2 macro.<br>
*app/templates/_macros.html*:
```html
{% macro pagination_widget(pagination, endpoint) %}
<ul class="pagination">
    <li {% if not pagination.has_prev %} class="disabled"{% endif %}>
        <a href="{% if pagination.has_prev %}{{ url_for(endpoint, page=pagination.prev_num, **kwargs) }}{% else %}#{% endif %}">
            &laquo;
        </a>
    </li>
    {% for p in pagination.iter_pages() %}
        {% if p %}
            {% if p == pagination.page %}
            <li class="active">
                <a href="{{ url_for(endpoint, page = p, **kwargs) }}">{{ p }}</a>
            </li>
            {% else %}
            <li>
                <a href="{{ url_for(endpoint, page = p, **kwargs) }}">{{ p }}</a>
            </li>
            {% endif %}
        {% else %}
        <li class="disabled"><a href="#">&hellip;</a></li>
        {% endif %}
    {% endfor %}
    <li {% if not pagination.has_next %} class="disabled"{% endif %}>
        <a href="{% if pagination.has_next %}{{ url_for(endpoint, page=pagination.next_num, **kwargs) }}{% else %}#{% endif %}">
            &raquo;
        </a>
    </li>
</ul>
{% endmacro %}
```
The macro creates a Bootstrap pagination element( < class="pagination" > ).<br>
This defines the following page links inside it:
- "previous page" link. This link gets the ***disabled*** CSS class if the curernt page is the first one.<br><br>
- "next page" link. This link will appear disabled if the current page is the last one.<br><br>
- Links to all pages returned by the pagination object's ***iter_pages()*** iterator. These pages are rendered as links with an explicit page number. The page currently displayed is highlighted using the ***active*** CSS class.
<br><br>

The ***pagination_widget*** macro can be added below the *_posts.html* template included by *index.html* and *user.html*. The following shows how it is used.<br>
*app/templates/index.html*:
```html
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}
{% import "_macros.html" as macros %} <!-- import! -->

{% block title %}Vertica{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Hello, {% if current_user.is_authenticated %}{{ current_user.username }}{% else %}Stranger{% endif %}!</h1>
</div>
<div>
    {% if current_user.can(Permission.WRITE) %}
    {{ wtf.quick_form(form) }}
    {% endif %}
</div>
{% include '_posts.html' %}
{% if pagination %}   <!-- if pagination is given. -->
<div class="pagination">
    {{ macros.pagination_widget(pagination, '.index') }}
</div>
{% endif %}
{% endblock %}
```

### Permanent Links to Blog Posts
Users may want to share links to specific blog posts with friends on social networks. For this purpose, each post will be assigned a page with a unique URL that reference it.<br>
*app/main/views.py*
```python
@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template("post.html",posts=[post])
```
<br>

If you prefer using readable URLs instead of numeric IDs, an alternative to numeric ID is *slug* which is a unique string that's based on the title or first few words of the post.<br><br>

Note that the post.html template receives a list with a single element that is the post to render. The permanent links are added at the bottom of each post in the generic ***_posts.html*** template, as shown below.<br>
*app/templates/_posts.html*:
```html
<ul class="posts">
    {% for post in posts %}
    <li class="post">
        <div class="post-thumbnail">
            <a href="{{ url_for('.user', username=post.author.username) }}">
                <img class="img-rounded profile-thumbnail" src="{{ post.author.gravatar(size=40) }}">
            </a>
        </div>
        <div class="post-content">
            <div class="post-date">{{ moment(post.timestamp).fromNow() }}</div>
            <div class="post-author"><a href="{{ url_for('.user', username=post.author.username) }}">{{ post.author.username }}</a></div>
            <div class="post-body">
                {% if post.body_html %}
                    {{ post.body_html | safe }}
                {% else %}
                    {{ post.body }}
                {% endif %}
            </div>
            <div class="post-footer"> <!-- Here comes new changes -->
                <a href="{{ url_for('.post', id=post.id) }}">
                    <span class="label label-default">Permalink</span>
                </a>
            </div>
        </div>
    </li>
    {% endfor %}
</ul>

```
<br>

The new *post.html* template that renders the permanent link page is shown below.
*app/templates/post.html*:
```html
{% extends "base.html" %}
{% block title %}Vertica - Post{% endblock %}
{% block page_content %}
{% include '_posts.html' %}
{% endblock %}
```

### Blog Post Editor
The last feature related to blog posts is a post editor that allows users to edit their own posts. The edit_post.html template is shown below.<br>
*app/templates/edit_post.html*:
```html

{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}

{% block title %}Vertica - Edit Post{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Edit Post</h1>
</div>
<div>
    {{ wtf.quick_form(form) }}
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
{{ pagedown.include_pagedown() }}
{% endblock %}
```
<br>

The route that supports the blog post edit follows.<br>
*app/main/views.py*:
```python
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)

    #only the author or admin
    if current_user != post.author and \
            not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)
```
<br>

To complete the feature, a link to the blog post editor can be added below each blog post, next to the permanent link.<br>
*app/templated/_posts.html*:
```html
<ul class="posts">
    {% for post in posts %}
    <li class="post">
        ...
        <div class="post-content">
            ...
            <div class="post-footer">
                ...
                {% if current_user == post.author %}
                <a href="{{ url_for('.edit',id=post.id )}}">
                    <span class="label label-primary">Edit</span>
                </a>
                {% elif current_user.is_administrator() %}
                <a href="{{ url_for('.edit',id=post.id)}}">
                    <span class="label label-danger">Edit [Admin]</span>    
                </a>
                {% endif %}
            </div>
        </div>
    </li>
    {% endfor %}
</ul>

```
This change adds an "Edit" link to any blog posts that are authored by the current user. 
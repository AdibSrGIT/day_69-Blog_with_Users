import flask
from flask import Flask,g, render_template, redirect, url_for, flash, request,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL','sqlite:///blog3.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## user Gravatar image
gravatar = Gravatar(app,
                    size=2,
                    rating='g',
                    default="https://media.giphy.com/media/DRI4dtTDzY3Kw/giphy.gif",
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None
                    )

# Relational Databases
## place a foreign key in the child table
## place a relationship() in the parent table
## for 1-2-1 use param: userlist=False in relationship()

## use relationship() var of child to access parent table attr , eg: child.relationshipvar().name

##CONFIGURE TABLES
# TODO: This is the DB for POSTS
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # author = db.Column(db.String(250), nullable=False)    ### we are cutting this out at last stg, cuz we want to create our own users/authors
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    find_parent_id_user = db.Column(db.Integer, db.ForeignKey('user.id'))    # placing foreign key in child table ref parent
    authorof_post = relationship("User",back_populates="children_post")        # User is parent
    children_comment = relationship("Comment", back_populates="authorof_blog")



# TODO: This is the DB for USERS
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    children_post = relationship("BlogPost", back_populates="authorof_post")     # if 1-to-1 is needed, set param >> uselist=False
    children_comment = relationship("Comment", back_populates="authorof_comment")

# TODO: Make Comment
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))        # or db.Text

    find_parent_id_inuser = db.Column(db.Integer, db.ForeignKey('user.id'))
    authorof_comment = relationship("User", back_populates="children_comment")

    find_parent_id_inblog = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    authorof_blog = relationship("BlogPost", back_populates="children_comment")
#
# db.create_all()
# db.drop_all()


# TODO: new post
newpst = BlogPost(
    # author="Adib S",          ### we are cutting this out at last stg, cuz we want to create our own users/authors
    title='The Life of Cactus',
    subtitle= 'Who knew that cacti lived such interesting lives.',
    date='September 22, 2022',
    body='<p>Nori grape silver beet broccoli kombu beet greens fava bean potato quandong celery.</p> \
            <p>Bunya nuts black-eyed pea prairie turnip leek lentil turnip greens parsnip.</p> \
            <p>Sea lettuce lettuce water chestnut eggplant winter purslane fennel azuki bean earthnut pea sierra leone bologi leek soko chicory celtuce parsley j&iacute;cama salsify.</p>',
    img_url='https://images.unsplash.com/photo-1530482054429-cc491f61333b?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1651&q=80',
    find_parent_id_user= '1'
)
# db.session.add(newpst)
# db.session.commit()




@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()

    return render_template("index.html", all_posts=posts)


@app.route('/register', methods= ["GET","POST"])
def register():
    new_user_form = RegisterForm()

    if new_user_form.validate_on_submit():
        new_user = User(
            email = new_user_form.email.data,
            password = generate_password_hash(new_user_form.password.data, method= 'pbkdf2:sha256', salt_length=8),
            name = new_user_form.name.data,
        )
        db.session.add(new_user)
        db.session.commit()
        print("USER ADDED", User.query.filter(User.email == new_user_form.email.data).first().email)

        # TODO: also login

        login_user(new_user)
        print("auth?", new_user.is_authenticated,
              "active?", new_user.is_active)

        return redirect(url_for('get_all_posts'))
    return render_template("register.html",form=new_user_form)

# TODO: setup Login manager
login_mng = LoginManager()
login_mng.init_app(app)
login_mng.login_view = 'login'

# TODO: setup user loader callback
@login_mng.user_loader
def load_user(user_id):
    user= User.query.get(int(user_id))
    return user

# TODO: worng details fn
def wrong():
    flash("Wrong User credentials. Please try again")
    return redirect(url_for('login'))

@app.route('/login',methods= ["GET","POST"])
def login():
    loginform = LoginForm()

    if loginform.validate_on_submit():
        this_user_id = request.form["email"]
        this_user = User.query.filter(User.email == this_user_id).first()
        print(this_user_id,this_user)#,this_pass)
        if not this_user or not check_password_hash(this_user.password, flask.request.form["password"]):
            wrong()
        else:
            login_user(this_user)
            print("auth?",this_user.is_authenticated,
                  "active?", this_user.is_active)
            return redirect(url_for("get_all_posts",logged_in=this_user.is_authenticated))

    return render_template("login.html", form=loginform)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts', current_user = current_user))


@app.route("/post/<int:post_id>", methods=["GET","POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    makecom = CommentForm()
    all_users = User.query.all()


    if makecom.validate_on_submit():
        if current_user.is_authenticated:
            newcomment = Comment(
                text= makecom.body.data,
                find_parent_id_inuser=current_user.id,
                find_parent_id_inblog=requested_post.id

            )
            print(newcomment.text, flush=True)
            db.session.add(newcomment)
            db.session.commit()
        else:
            wrong()
    all_comments_tbl = Comment.query.all()
    textcomments= [all_comments_tbl.index(comment) for comment in all_comments_tbl]
    print(textcomments)
    print()

    # print(hash("https://media.giphy.com/media/L9AqjFr6H4iaY/giphy.gif"))
    userimgs= ['https://media.giphy.com/media/DRI4dtTDzY3Kw/giphy.gif',
               'https://media.giphy.com/media/L9AqjFr6H4iaY/giphy.gif',
               'https://media.giphy.com/media/L9AqjFr6H4iaY/giphy.gif',
               'https://media.giphy.com/media/jU2mwGALDEbPtIvUio/giphy.gif',
               'https://media.giphy.com/media/26gsdnOWGYQb1NQFq/giphy.gif']

    return render_template("post.html", post=requested_post,
                           commentform=makecom,
                           comments=all_comments_tbl,
                           textcomments=textcomments,
                           users=all_users,
                           userimgs=userimgs)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")

# TODO: understand before request  ???
# @app.before_request
def before_request(fn2):
    g.user = current_user
    return g.user

'''

from functools import wraps
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function
'''

def admin_only(fn):
    def wrapper(*args, **kwargs):

        unknown_user = login_mng.anonymous_user().is_anonymous
        # print(unknown_user)
        # if g.user is None:

        # TODO: How to handle no user logged in w/ except try
        try:
            print(fn.__name__, 'running','heres the current user',current_user.__getattr__('id'))

            # TODO: how to handle NO Admin logged in
            if current_user.id != 1:
                print(f"Please login with ADMIN to access the page."
                      f"  Current user is {current_user} {current_user.id}")
                # f"\nIS anonnymus {unknown_user}")
                return flask.abort(403)

        except AttributeError:
            # print(fn.__name__, 'running')
            flash("HeLLO Scammer!! Kindly Get Out! (or Login properly)")
            return redirect(url_for('login'))

        return fn(*args, **kwargs)
    return wrapper

@app.route("/new-post", endpoint='nwpost')
@admin_only
def add_new_post():
    form = CreatePostForm()

    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", endpoint='edtpost', methods=["GET","POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        # author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        # post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>", endpoint='dltpost')
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))



if __name__ == "__main__":
    app.run(debug=True, port=5000)

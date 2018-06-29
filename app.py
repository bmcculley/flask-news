# -*- coding: utf-8 -*-
import sys
import argparse
from flask import Flask, render_template, request, flash, \
                    redirect, Response, url_for, abort
from urllib.parse import urlparse, urljoin
from flask_login import LoginManager, UserMixin, current_user, \
                            login_required, login_user, logout_user
from forms import LoginForm, RegistForm, PostForm
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import time


def current_time():
    '''
    return current time as epoch
    '''
    return int(time.time())

# flask app setup
app = Flask(__name__)
app.secret_key = "update_me"

# flask-login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# setup flask sqlalchemy
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)

# the user model (flask login)
class User(UserMixin):

    def __init__(self, id):
        user_data = DBUser.query.filter_by(id=id).first()
        self.id = id
        self.name = user_data.username
        self.email = user_data.email
        
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.email)



# the user table structure 
class DBUser(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)
    
    # extra fields to create a profile page
    # created
    # points
    # about

    def __repr__(self):
        return "<DBUser %r>" % self.username
        
class DBPost(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=False, nullable=False)
    text = db.Column(db.String(1000), unique=False, nullable=True)
    url = db.Column(db.String(120), unique=False, nullable=True)
    votes = db.Column(db.Integer)
    submit_date = db.Column(db.String(120), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
        
    user = db.relationship('DBUser',
        backref=db.backref('post', lazy=True))

class DBVote(db.Model):
    __tablename__ = "votes"
    id = db.Column(db.Integer, primary_key=True)
    vote = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    user_votee = db.relationship('DBUser',
        backref=db.backref('user_votee', lazy=True))
        
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'),
        nullable=False)
    post_vote = db.relationship('DBPost',
        backref=db.backref('post_vote', lazy=True))
    
# setup and populate the database
def setup_db():
    db.create_all()
    user_dict = {
        "admin" : DBUser(username="admin", email="admin@example.com", password=bcrypt.hashpw(b"abc123", bcrypt.gensalt())),
        "guest" : DBUser(username="guest", email="guest@example.com", password=bcrypt.hashpw(b"password", bcrypt.gensalt()))}
    for key, user in user_dict.items():
        print("%s added to the database."% user.username)
        db.session.add(user)
    db.session.commit()

# snippet to check if the url is safe
# http://flask.pocoo.org/snippets/62/
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and \
           ref_url.netloc == test_url.netloc


# home page (non protected)
@app.route("/")
def home():
    # this query needs to be fixed to handle the ranking math
    posts = DBPost.query.all()
    return render_template("home.html")


# an example protected url
@app.route("/submit")
@login_required
def submit():
    form = PostForm(request.form)
    if request.method == "POST"  and form.validate():
        #post_user = DBUser(username=current_user.name)
        post = DBPost(title=form.title.data, text=form.text.data, 
                    url=form.url.data, submit_date=current_time(), 
                    user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
    
    return render_template("submit.html", form=form)


# register here
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if current_user.is_anonymous:
        form = RegistForm(request.form)
        if request.method == "POST" and form.validate():
            try:
                user = DBUser(username=form.username.data, 
                    email=form.email.data, 
                    password=bcrypt.hashpw(form.password.data.encode("utf-8"), bcrypt.gensalt()))
                db.session.add(user)
                db.session.commit()
                return redirect(url_for("login"))
            except:
                # need to improve this error handling
                error = "Username or email already in use."
        return render_template("register.html", form=form, error=error)
    else:
        return redirect(url_for("home"))

# login here
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if current_user.is_anonymous:
        form = LoginForm(request.form)
        if request.method == "POST" and form.validate():
            username = form.username.data
            password = form.password.data.encode("utf-8")
            user_data = DBUser.query.filter_by(username=username).first()
            if user_data and bcrypt.checkpw(password, user_data.password):
                user = User(user_data.id)
                login_user(user)
                flash("You were successfully logged in")
                next = request.args.get("next")
                if not is_safe_url(next):
                    return abort(400)

                return redirect(next or url_for("home"))
            else:
                error = "Login failed"
        return render_template("login.html", form=form, error=error)
    else:
        return "Already logged in."


# log the user out
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# handle failed login
@app.errorhandler(401)
def page_not_found(e):
    return "Login failed"


# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="An example usage of flask login.")
    parser.add_argument("-s", "--setup", dest="dbsetup", action="store_true",
                    help="This creates and sets up the base database.")
    parser.add_argument("-r", "--run", dest="run",  action="store_true",
                    help="Start and run the server.")
    parser.add_argument("-d", "--debug", dest="debug",  action="store_true",
                    help="Start the app in debug mode.")
    parser.add_argument("-l", "--listen", dest="host", default="127.0.0.1",
                    help="Where should the server listen. \
                          Defaults to 127.0.0.1.")
    parser.add_argument("-p", "--port", dest="port", default=5000,
                    help="Which port should the server listen on. \
                          Defaults to 5000.")
    # if no args were supplied print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    # we have args...let"s do things
    args = parser.parse_args()
    if args.dbsetup and args.run:
        print("Setup and run arguments can't be used at the same time.")
        sys.exit(1)
    if args.dbsetup:
        setup_db()
    if args.run:
        app.run(debug=args.debug, host=args.host, port=args.port)
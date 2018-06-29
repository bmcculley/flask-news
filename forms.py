from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, \
                        SubmitField, validators
from wtforms.widgets import TextArea

# the flask wtf login form setup and validation
class LoginForm(Form):
    username = StringField("Username", validators=[validators.DataRequired()])
    password = PasswordField("Password", validators=[validators.DataRequired()])
    submit = SubmitField("Login")


class RegistForm(Form):
    username = StringField("Username", validators=[validators.DataRequired()
        ])
    email = StringField("Email", validators=[
        validators.DataRequired(), 
        validators.Email()
        ])
    password = PasswordField("Password", validators=[validators.DataRequired(), 
        validators.EqualTo("vpassword", message="Passwords don't match")
        ])
    vpassword = PasswordField("Verify Password", validators=[
        validators.DataRequired()
        ])
    submit = SubmitField("Register")
    
class PostForm(Form):
    title = StringField("Post Title", validators=[validators.DataRequired()])
    content = StringField("Post Content", widget=TextArea())
    url = StringField("Post URL")
    submit = SubmitField("Submit")
from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt 

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'                              # connects app.py to database.db
app.config['SECRET_KEY'] = 'thisisasecretkey'                                                # to secure the session cookie 

db = SQLAlchemy(app)                                                                         # creates the database instance 
bcrypt = Bcrypt(app)

Login_manager = LoginManager()
Login_manager.init_app(app)
Login_manager.login_view = "login"

@Login_manager.user_loader                                                                   #allows app and flask login to work together when logging in
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)                                             #identity column for user
    username = db.Column(db.String(20), nullable=False, unique=True)                         #both of these fields cant be empty
    password = db.Column(db.String(80), nullable=False)

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class RegisterForm(FlaskForm):
    username = StringField(validators={InputRequired(), Length(
        min=4, max=20)}, render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators={InputRequired(), Length(
        min=4, max=20)}, render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        
        if existing_user_username:
            raise ValidationError(
                "That username already exists. Please choose a different one.")
        
class LoginForm(FlaskForm):
    username = StringField(validators={InputRequired(), Length(
        min=4, max=20)}, render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators={InputRequired(), Length(
        min=4, max=20)}, render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Login")
    

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods={'GET', 'POST'})
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/dashboard', methods={'GET', 'POST'})
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout', methods={'GET', 'POST'})
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods={'GET', 'POST'})
def register():
    form = RegisterForm()

    if form.validate_on_submit():                                                      # whenever we submit this form, we immediately create a hashed version of the password
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
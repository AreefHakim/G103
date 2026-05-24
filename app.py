
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
    
    store = db.relationship('Store',backref='owner',uselist=False)                            #relationship (User -> Store)

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    description = db.Column(db.String(200))

    phone_number = db.Column(db.String(20),nullable=True)                                     #Phone number support

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    products = db.relationship('Product',backref='store',lazy=True)                           #relationship (Store -> Products)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)                                               #creates unique id for every product

    name = db.Column(
        db.String(100),                                                                        #maximum 100 characters
        nullable=False                                                                         #cant leave this field empty
    )

    price = db.Column(
        db.Float,                                                                               #allow decimal numbers
        nullable=False
    )

    category = db.Column(
        db.String(50)
    )

    image_url = db.Column(                                                                      #store image links to display images on the website
        db.String(500)
    )

    store_id = db.Column(                                                                        #connects Product -> Store
        db.Integer,
        db.ForeignKey('store.id'),
        nullable=False
    )

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        
        if existing_user_username:
            raise ValidationError(
                "That username already exists. Please choose a different one.")
        
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Login")
    

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_stores = Store.query.filter_by(owner_id=current_user.id).all() 
    return render_template('dashboard.html', username=current_user.username, stores=user_stores)

@app.route('/logout',methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():                                                               # whenever we submit this form, we immediately create a hashed version of the password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')     # decode('utf-8') to convert the generated hash into a clean text string before creating user object
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/forgotpassword')
def forgotpassword():
    return render_template('forgotpassword.html')

#store routes

@app.route('/register-store', methods=['GET', 'POST'])                                                                        #combined both api and html for store registration 
@login_required
def register_store():

    if request.method == 'POST':

        store_name = request.form.get('store_name')
        description = request.form.get('description')
        raw_phone = request.form.get('phone_number')

        phone_number = None

        if raw_phone:

            cleaned_phone = raw_phone.strip() \
                .replace('-', '') \
                .replace(' ', '') \
                .replace('+', '')

            if cleaned_phone.startswith('60'):
                cleaned_phone = cleaned_phone[2:]                                                            #automatically formats malaysian phone numbers

            phone_number = cleaned_phone

        new_store = Store(name=store_name, description=description,phone_number=phone_number,owner=current_user)

        db.session.add(new_store)
        db.session.commit()

        return redirect(url_for('my_store'))

    return render_template('registerstore.html')


@app.route('/my-store')
@login_required
def my_store():

    store = Store.query.filter_by(user_id=current_user.id).first()                              #Find the store owned by this user

    if not store:
        return redirect(url_for('register_store'))

    return render_template('mystore.html',store=store)

@app.route('/delete-store', methods=['POST'])
@login_required
def delete_store():

    user_store = Store.query.filter_by(user_id=current_user.id).first()

    if user_store:

        Product.query.filter_by(store_id=user_store.id).delete()

        db.session.delete(user_store)
        db.session.commit()

    return redirect(url_for('dashboard'))

#Product routes

@app.route('/store/update/<int:store_id>', methods=['PUT'])                                    #UPDATE - Edit store
@login_required
def update_store(store_id):

    store = Store.query.filter_by(
        id=store_id,
        owner_id=current_user.id
    ).first()

    if not store:
        return jsonify({"error": "Store not found"}), 404

    data = request.get_json()

    store.store_name = data.get('store_name', store.store_name)
    store.description = data.get('description', store.description)

    db.session.commit()

    return jsonify({
        "message": "Store updated successfully",
        "store": {
            "id": store.id,
            "store_name": store.store_name,
            "description": store.description
        }
    })

@app.route('/store/delete/<int:store_id>', methods=['DELETE'])                                #DELETE - Delete store
@login_required
def delete_store(store_id):

    store = Store.query.filter_by(
        id=store_id,
        owner_id=current_user.id
    ).first()

    if not store:
        return jsonify({"error": "Store not found"}), 404

    db.session.delete(store)
    db.session.commit()

    return jsonify({
        "message": "Store deleted successfully"
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()                                                                #Build and store user's tables if they dont exist
    app.run(debug=True)



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

@app.route('/add-product', methods=['GET', 'POST'])                                       #displaying product form and submitting product data
@login_required
def add_product():

    user_store = Store.query.filter_by(user_id=current_user.id).first()                                 

    if not user_store:
        return redirect(url_for('register_store'))

    if request.method == 'POST':

        name = request.form.get('name')
        price = request.form.get('price')

        selected_cat = request.form.get('category_select')                                  #select category from dropdown menu

        image_url = request.form.get('image_url')

        if selected_cat == 'Others':                                                     #custom type of category
            category = request.form.get(
                'other_category'
            )
        else:
            category = selected_cat

        new_product = Product(
            name=name,
            price=float(price),
            category=category,
            image_url=image_url,
            store_id=user_store.id                                                            #connects product to store owner
        )

        db.session.add(new_product)                                                              
        db.session.commit()                                                                 #saves into database

        return redirect(url_for('my_store'))

    return render_template('add_product.html')


@app.route('/products')
def products():

    all_products = Product.query.all()

    return render_template(
        'products.html',
        products=all_products
    )


@app.route('/view-product/<int:product_id>')                                      #view single product
def view_product(product_id):

    product = Product.query.get_or_404(product_id)                             #find product, if doesnt exists = 404 page

    return render_template('product_detail.html',product=product)               #display one product page


@app.route('/delete-product/<int:product_id>', methods=['POST'])             #delete product (I dont use 'GET' for this to prevent accidental deletion and flask project commonly use post for delete routes)
@login_required
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)                         

    if current_user.store and \
       product.store_id == current_user.store.id:                               #security check: check if this product belongs to current user (without this, any user can delete the product)

        db.session.delete(product)
        db.session.commit()                                                     #removes product permanently 

        return redirect(url_for('my_store'))

    return jsonify({
        "error": "Unauthorized action"
    }), 403                                                                      #user is not allow to do this action

#CRUD (CREATE, READ, UPDATE, DELETE) API

@app.route('/api/store/register', methods=['POST'])                            #CREATE store api 
@login_required
def api_register_store():

    data = request.get_json()

    store_name = data.get('store_name')
    raw_phone = data.get('phone_number')

    if not store_name:                                                      #validation check
        return jsonify({
            "error": "Store name is required" 
        }), 400                                                               #bad request: user sent invalid data
 
    phone_number = None

    if raw_phone:                                                            #only run if there's a phone number provided 

        cleaned_phone = str(raw_phone).strip() \
            .replace('-', '') \
            .replace(' ', '') \
            .replace('+', '')                                                   #convert to string | .strip() used for removing spaces at beginning/end

        if cleaned_phone.startswith('60'):                                   #remove '60' at the start of the phone number 
            cleaned_phone = cleaned_phone[2:]

        phone_number = cleaned_phone

    new_store = Store(name=store_name,description=data.get('description'),phone_number=phone_number,user_id=current_user.id)        #connects store to logged in user

    db.session.add(new_store)                                 #save to database
    db.session.commit()

    return jsonify({
        "message": "Store registered successfully",
        "store": {
            "id": new_store.id,
            "name": new_store.name
        }
    }), 201                                                    # 201 means: new resource successfully created


@app.route('/stores', methods=['GET'])                                          #READ all stores                             #only reads data
@login_required
def get_stores():

    stores = Store.query.filter_by(user_id=current_user.id).all()                 #Finds all stores owned by current user 

    store_list = []

    for store in stores:

        store_list.append({
            "id": store.id,
            "name": store.name,
            "description": store.description,
            "phone_number": store.phone_number
        })

    return jsonify(store_list)


@app.route('/store/<int:store_id>', methods=['GET'])                    #READ single store                                         #only reads data
@login_required
def get_store(store_id):

    store = Store.query.filter_by(id=store_id,user_id=current_user.id).first()               #Find store id that matches url and belongs to current user

    if not store:
        return jsonify({
            "error": "Store not found"
        }), 404

    return jsonify({
        "id": store.id,
        "name": store.name,
        "description": store.description,
        "phone_number": store.phone_number
    })


@app.route('/store/update/<int:store_id>', methods=['PUT'])             #UPDATE store          #PUT for update data
@login_required
def update_store(store_id):

    store = Store.query.filter_by(id=store_id,user_id=current_user.id).first()               #security check: without this, anyone can update other user's store

    if not store:                                                                             #if store doesnt exist or doesnt belong to current user
        return jsonify({
            "error": "Store not found"
        }), 404

    data = request.get_json()                                                        #update data

    store.name = data.get('name',store.name)

    store.description = data.get('description',store.description)

    store.phone_number = data.get('phone_number',store.phone_number)

    db.session.commit()                                                            #save changes

    return jsonify({
        "message": "Store updated successfully"
    })


@app.route('/store/delete/<int:store_id>', methods=['DELETE'])                    #DELETE store
@login_required
def delete_store_api(store_id):

    store = Store.query.filter_by(id=store_id,user_id=current_user.id).first()                #Find store id that matches url and belongs to current user

    if not store:
        return jsonify({
            "error": "Store not found"
        }), 404

    Product.query.filter_by(store_id=store.id).delete()                            #Deletes ALL products in the store 

    db.session.delete(store)
    db.session.commit()

    return jsonify({
        "message": "Store deleted successfully"
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()                                                                #Build and store user's tables if they dont exist
    app.run(debug=True)


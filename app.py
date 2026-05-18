from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- DATABASE MODELS ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    store = db.relationship('Store', backref='owner', uselist=False)

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    # PERUBAHAN 1: Ditambah column phone_number untuk link WhatsApp
    phone_number = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', backref='store', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(500))  # Column storing product image URLs
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)

# --- FORMS ---

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('Username already exists.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

# --- ROUTES ---

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

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password')
def forgotpassword():
    return render_template('forgotpassword.html')

# --- MARKETPLACE & STORE ROUTES ---

@app.route('/register-store', methods=['GET', 'POST'])
@login_required
def register_store():
    if request.method == 'POST':
        store_name = request.form.get('store_name')
        description = request.form.get('description')
        raw_phone = request.form.get('phone_number')
        
        # PERUBAHAN 2: Proses pembersihan input nombor telefon
        phone_number = None
        if raw_phone:
            # Buang sebarang simbol dash, jarak kosong, atau simbol tambah
            cleaned_phone = raw_phone.strip().replace('-', '').replace(' ', '').replace('+', '')
            
            # Buang kod negara jika user terasimilasi masukkan (cth: '6012...' atau '60012...')
            if cleaned_phone.startswith('60'):
                cleaned_phone = cleaned_phone[2:]
            
            phone_number = cleaned_phone

        # Simpan objek kedai baharu bersama nombor telefon
        new_store = Store(name=store_name, description=description, phone_number=phone_number, owner=current_user)
        db.session.add(new_store)
        db.session.commit()
        return redirect(url_for('my_store'))
    return render_template('registerstore.html')

@app.route('/my-store')
@login_required
def my_store():
    store = Store.query.filter_by(user_id=current_user.id).first()
    if not store:
        return redirect(url_for('register_store'))
    return render_template('mystore.html', store=store)

@app.route('/delete-store', methods=['POST'])
@login_required
def delete_store():
    user_store = Store.query.filter_by(user_id=current_user.id).first()
    if user_store:
        Product.query.filter_by(store_id=user_store.id).delete()
        db.session.delete(user_store)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    user_store = Store.query.filter_by(user_id=current_user.id).first()
    if not user_store:
        return redirect(url_for('register_store'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        selected_cat = request.form.get('category_select')
        image_url = request.form.get('image_url')
        
        if selected_cat == 'Others':
            category = request.form.get('other_category')
        else:
            category = selected_cat

        new_product = Product(
            name=name, 
            price=float(price), 
            category=category, 
            image_url=image_url, 
            store_id=user_store.id
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('my_store'))
        
    return render_template('add_product.html')

@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/view-product/<int:product_id>')
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if the product belongs to the store of the current logged-in user
    if current_user.store and product.store_id == current_user.store.id:
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('my_store'))
    else:
        return jsonify({"error": "Unauthorized action"}), 403

# --- API ROUTES (FOR BACKEND TEAM) ---

@app.route('/api/store/register', methods=['POST'])
@login_required
def api_register_store():
    data = request.get_json()
    store_name = data.get('store_name')
    raw_phone = data.get('phone_number')
    
    if not store_name:
        return jsonify({"error": "Store name is required"}), 400
    
    # Pembersihan nombor telefon untuk API endpoint juga
    phone_number = None
    if raw_phone:
        cleaned_phone = str(raw_phone).strip().replace('-', '').replace(' ', '').replace('+', '')
        if cleaned_phone.startswith('60'):
            cleaned_phone = cleaned_phone[2:]
        phone_number = cleaned_phone
    
    new_store = Store(
        name=store_name, 
        description=data.get('description'), 
        phone_number=phone_number, 
        user_id=current_user.id
    )
    db.session.add(new_store)
    db.session.commit()
    return jsonify({"message": "Store registered successfully"}), 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
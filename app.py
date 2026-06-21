
from flask import Flask, render_template, url_for, redirect, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt 
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

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

    phone_number = db.Column(db.String(20), nullable=True)

    rating = db.Column(db.Float, default=0)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    products = db.relationship(                                     #creates connection between store and product
        'Product',
        backref='store',                                         #adds a store property
        lazy=True                                                 #only load stuff when needed
    )

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

class ChangePasswordForm(FlaskForm):

    current_password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Current Password"}
    )

    new_password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "New Password"}
    )

    confirm_password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Confirm New Password"}
    )

    submit = SubmitField('Update Password')

def format_flatpickr_date(raw_date):

    if not raw_date:
        return ""

    if " to " in raw_date:

        try:

            start_str, end_str = raw_date.split(" to ")

            start_obj = datetime.strptime(
                start_str.strip(),
                '%Y-%m-%d'
            )

            end_obj = datetime.strptime(
                end_str.strip(),
                '%Y-%m-%d'
            )

            if start_obj.month == end_obj.month and \
               start_obj.year == end_obj.year:

                return f"{start_obj.strftime('%d')}-{end_obj.strftime('%d %B %Y')}"

            else:

                return f"{start_obj.strftime('%d %B')}-{end_obj.strftime('%d %B %Y')}"

        except:
            return raw_date

    else:

        try:

            date_obj = datetime.strptime(
                raw_date.strip(),
                '%Y-%m-%d'
            )

            return date_obj.strftime('%d %B %Y')

        except:
            return raw_date
    
class ProductView(db.Model):

    id = db.Column(db.Integer,primary_key=True)

    product_id = db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False)

    viewed_at = db.Column(db.DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))              #prevents deprecated datetime problems    #lambda: run function only when new row is created

class StoreRating(db.Model):                                                                                  #store rating

    id = db.Column(db.Integer, primary_key=True)

    rating = db.Column(db.Integer,nullable=False)

    store_id = db.Column(db.Integer,db.ForeignKey('store.id'),nullable=False)

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)


class Event(db.Model):                                                                                      #event

    id = db.Column(db.Integer,primary_key=True)

    title = db.Column(db.String(100),nullable=False)

    description = db.Column(db.String(300))

    event_date = db.Column(db.DateTime(timezone=True),nullable=False)

    created_at = db.Column(db.DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))                 


class Notification(db.Model):                                                                                  #notification 
                      
    id = db.Column(db.Integer,primary_key=True)

    message = db.Column(db.String(300),nullable=False)
                                                                                                                     
    is_read = db.Column(                                                                                        #read/unread status
        db.Boolean,
        default=False)                                                                                   #notification still unread

    created_at = db.Column(db.DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)





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

    user_stores = Store.query.filter_by(
        user_id=current_user.id
    ).all()


    top_rated_stores = db.session.query(
        Store.name,
        func.avg(StoreRating.rating).label('avg_rating')
    ).join(
        StoreRating,
        Store.id == StoreRating.store_id
    ).group_by(
        Store.id
    ).order_by(
        func.avg(StoreRating.rating).desc()
    ).limit(5).all()


    most_viewed_products = db.session.query(
    Product,
    func.count(ProductView.id).label('views')
).join(
    ProductView,
    Product.id == ProductView.product_id
).group_by(
    Product.id
).order_by(
    func.count(ProductView.id).desc()
).limit(5).all()


    upcoming_events = Event.query.filter(
        Event.event_date >= datetime.now(timezone.utc)
    ).order_by(
        Event.event_date.asc()
    ).all()


    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()

    return render_template(
    'dashboard.html',
    username=current_user.username,
    stores=top_rated_stores,
    products=most_viewed_products,
    events=upcoming_events,
    notifications=notifications
)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    form = ChangePasswordForm()

    if form.validate_on_submit():

        if bcrypt.check_password_hash(
            current_user.password,
            form.current_password.data
        ):

            if form.new_password.data == form.confirm_password.data:

                hashed_password = bcrypt.generate_password_hash(
                    form.new_password.data
                ).decode('utf-8')

                current_user.password = hashed_password

                db.session.commit()

                flash(
                    'Password updated successfully!',
                    'success'
                )

                return redirect(url_for('profile'))

            else:

                flash(
                    'New passwords do not match.',
                    'danger'
                )

        else:

            flash(
                'Incorrect current password.',
                'danger'
            )

    return render_template(
        'profile.html',
        form=form
    )


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

@app.route('/register-store', methods=['GET', 'POST'])
@login_required
def register_store():

    if current_user.username == 'admin':
        flash('Admins cannot register stores.', 'danger')
        return redirect(url_for('dashboard'))

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
                cleaned_phone = cleaned_phone[2:]

            phone_number = cleaned_phone

        new_store = Store(
            name=store_name,
            description=description,
            phone_number=phone_number,
            owner=current_user
        )

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

@app.route('/delete-store/<int:store_id>', methods=['POST'])
@login_required
def delete_store(store_id):

    store = Store.query.get_or_404(store_id)

    if current_user.username != 'admin' and \
       store.user_id != current_user.id:                                                                 #For admin to delete stores
        return jsonify({"error": "Unauthorized"}), 403

    Product.query.filter_by(store_id=store.id).delete()

    db.session.delete(store)
    db.session.commit()

    return redirect(url_for('manage_stores'))

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

    search_query = request.args.get('search', '')

    category_filter = request.args.get('category', '')

    sort_by = request.args.get('sort', '')

    query = Product.query.join(Store)

    if search_query:

        query = query.filter(
            Product.name.ilike(
                f'%{search_query}%'
            )
        )

    if category_filter:

        query = query.filter(
            Product.category == category_filter
        )

    if sort_by == 'price_low':

        query = query.order_by(
            Product.price.asc()
        )

    elif sort_by == 'price_high':

        query = query.order_by(
            Product.price.desc()
        )

    elif sort_by == 'popularity':

        query = query.outerjoin(
            ProductView,
            Product.id == ProductView.product_id
        ).group_by(
            Product.id
        ).order_by(
            func.count(ProductView.id).desc()
        )

    elif sort_by == 'rating':

        query = query.outerjoin(
            StoreRating,
            Store.id == StoreRating.store_id
        ).group_by(
            Product.id
        ).order_by(
            func.avg(StoreRating.rating).desc()
        )

    else:

        query = query.order_by(
            Product.id.desc()
        )

    all_products = query.all()

    categories = [
        p.category
        for p in Product.query.with_entities(
            Product.category
        ).distinct()
    ]

    return render_template(
        'products.html',
        products=all_products,
        categories=categories,
        search_query=search_query,
        category_filter=category_filter,
        sort_by=sort_by
    )


@app.route('/view-product/<int:product_id>')
def view_product(product_id):

    product = Product.query.get_or_404(product_id)


    new_view = ProductView(                             #track product view
        product_id=product.id
    )

    db.session.add(new_view)

    db.session.commit()


    return render_template(
        'product_detail.html',
        product=product
    )


@app.route('/rate-store/<int:store_id>', methods=['POST'])
@login_required
def rate_store(store_id):

    store = Store.query.get_or_404(store_id)

    rating_value = int(request.form.get('rating'))

    if rating_value < 1 or rating_value > 5:
        return jsonify({
            "error": "Rating must be between 1 and 5"
        }), 400

    existing_rating = StoreRating.query.filter_by(
        store_id=store.id,
        user_id=current_user.id
    ).first()

    if existing_rating:
        existing_rating.rating = rating_value
    else:
        new_rating = StoreRating(rating=rating_value,store_id=store.id,user_id=current_user.id)

        db.session.add(new_rating)

    db.session.commit()

    return redirect(url_for('my_store'))

@app.route('/delete-product/<int:product_id>', methods=['POST'])             #delete product (I dont use 'GET' for this to prevent accidental deletion and flask project commonly use post for delete routes)
@login_required
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)                           #find product by id or show 404 error if it doesnt exist

    if current_user.username == 'admin' or (                                #allow admin to delete any product
        current_user.store and
        product.store_id == current_user.store.id                           #allow store owner to delete their own products
    ):

        db.session.delete(product)                                          #remove product from database

        db.session.commit()                                                 #save changes permanently

        if current_user.username == 'admin':                                #if admin deleted the product
            return redirect(url_for('manage_stores'))                       #return admin to store management page

        return redirect(url_for('my_store'))                                #return store owner to their store page

    return jsonify({
        "error": "Unauthorized action"
    }), 403                                                                 #user is not allowed to delete this product

@app.route('/create-event', methods=['GET', 'POST'])                                 #create event route
@login_required
def create_event():

    if request.method == 'POST':

        title = request.form.get('title')

        description = request.form.get('description')

        event_date = request.form.get('event_date')

        new_event = Event(
            title=title,
            description=description,
            event_date=datetime.strptime(
                event_date,
                '%Y-%m-%dT%H:%M'                                                           #Converts string into actual datetime object
            ).replace(tzinfo=timezone.utc)                                                 #%Y = year
        )                                                                                  #%m = month
                                                                                           #d = day
        db.session.add(new_event)                                                          #H = hour
        db.session.commit()                                                                #M = minute

       
        users = User.query.all()                                                          #Gets every registered user

        for user in users:

            notification = Notification(
                message=f"Upcoming Event: {title}",                                          #f"" = formatted string
                user_id=user.id
            )

            db.session.add(notification)

        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('create_event.html')

@app.route('/edit-event/<int:event_id>', methods=['GET', 'POST'])                        #Flask expects a value in the URL (need to be int)
@login_required
def edit_event(event_id):

    if current_user.username != 'admin':

        return jsonify({
            "error": "Unauthorized"
        }), 403


    event = Event.query.get_or_404(event_id)


    if request.method == 'POST':

        title = request.form.get('title')

        description = request.form.get('description')

        raw_date = request.form.get('date')


        formatted_date = format_flatpickr_date(raw_date)


        try:

            parsed_date = datetime.strptime(
                raw_date.split(' to ')[0],
                '%Y-%m-%d'
            ).replace(tzinfo=timezone.utc)

        except:

            parsed_date = datetime.now(timezone.utc)


        event.title = title

        event.description = description

        event.event_date = parsed_date

        db.session.commit()

        return redirect(url_for('dashboard'))


    current_date_value = event.event_date.strftime('%Y-%m-%d')


    return render_template(
        'edit_event.html',
        event=event,
        current_date_value=current_date_value
    )

@app.route('/add-event', methods=['GET', 'POST'])
@login_required
def add_event():

    if current_user.username != 'admin':

        return jsonify({
            "error": "Unauthorized"
        }), 403


    if request.method == 'POST':

        title = request.form.get('title')

        description = request.form.get('description')

        raw_date = request.form.get('date')


        formatted_date = format_flatpickr_date(raw_date)


        try:

            parsed_date = datetime.strptime(
                raw_date.split(' to ')[0],
                '%Y-%m-%d'
            ).replace(tzinfo=timezone.utc)

        except:

            parsed_date = datetime.now(timezone.utc)


        new_event = Event(
            title=title,
            description=description,
            event_date=parsed_date
        )

        db.session.add(new_event)

        db.session.commit()


        users = User.query.all()

        for user in users:

            notification = Notification(
                message=f"Upcoming Event: {title}",
                user_id=user.id
            )

            db.session.add(notification)

        db.session.commit()


        return redirect(url_for('dashboard'))


    return render_template('add_event.html')

@app.route('/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):

    if current_user.username != 'admin':

        return jsonify({
            "error": "Unauthorized"
        }), 403


    event = Event.query.get_or_404(event_id)

    db.session.delete(event)

    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/notification/read/<int:notification_id>')                        #mark notification as read
@login_required
def mark_notification_read(notification_id):

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()

    notification.is_read = True

    db.session.commit()

    return redirect(url_for('dashboard'))


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


@app.route('/store/delete/<int:store_id>', methods=['DELETE'])                       #DELETE store
@login_required
def delete_store_api(store_id):

    store = Store.query.get(store_id)                                                    #Find store id that matches url and belongs to current user 

    if not store:
        return jsonify({
            "error": "Store not found"
        }), 404

    if current_user.username != 'admin' and \
       store.user_id != current_user.id:

        return jsonify({
            "error": "Unauthorized"
        }), 403

    Product.query.filter_by(
        store_id=store.id
    ).delete()                                                                           #DELETES all products in the store

    db.session.delete(store)
    db.session.commit()

    return jsonify({
        "message": "Store deleted successfully"
    })

@app.route('/manage-stores')
@login_required
def manage_stores():

    if current_user.username != 'admin':

        return jsonify({
            "error": "Unauthorized"
        }), 403

    stores = Store.query.all()                                              #get all stores

    for store in stores:

        store.products = Product.query.filter_by(                           #get all products belonging to this store
            store_id=store.id
        ).all()

    return render_template(
        'manage_stores.html',
        stores=stores
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()                                                                #Build and store user's tables if they dont exist   #Find store id that matches url and belongs to current user
    app.run(debug=True)


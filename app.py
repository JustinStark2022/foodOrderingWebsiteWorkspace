from flask import Flask, flash, redirect, render_template, request, jsonify, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from gridfs import GridFS
from flask import Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import session


uri = "***REMOVED***"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

app = Flask(__name__, template_folder='templates')
app.config['MONGO_URI'] = '***REMOVED***'
app.secret_key = b'***REMOVED***'
mongo = PyMongo(app)

db = client.groupies
coll = db.groupies
users=db.users

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.active = True

    def get_id(self):
        return self.username

    @property
    def is_active(self):
        return self.active
    
@login_manager.user_loader
def load_user(username):
    user_data = users.find_one({'username': username})
    if user_data:
        return User(username=user_data['username'], password=user_data['password'])
    else:
        return None

def item_serializer(item):
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "price": item["price"],
        "image": item["image"]
    }

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/menu')
def menu():
    items = db.items.find()
    return render_template('menu.html', items=items)

@app.route('/')
def index():
    items = db.items.find()
    return render_template('index.html', items=items)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            elif user['role'] == 'customer':
                return redirect(url_for('dashboard'))  # Redirect to the customer dashboard or a different route
            else:
                flash('Invalid role.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'GET':
        items = db.items.find()
        return render_template('admin.html', items=items)
    
    if request.method == 'POST':
        items = db.items.find()
        newName = request.form.get('newName')
        newPrice = request.form.get('newPrice')
        
        if newName and newPrice and 'newImage' in request.files:
            newImage = request.files['newImage']
            fs = GridFS(db)
            image_id = fs.put(newImage, filename=newImage.filename, content_type=newImage.content_type)
            db.items.insert_one({'name': newName, 'price': newPrice, 'image': newImage.filename, 'image_id': image_id})
            flash('Item added successfully', 'success')
        else:
            flash('Please fill in all the fields and provide an image', 'danger')

        return render_template('admin.html', items=items)
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
    
@app.route('/image/<filename>')
def image(filename):
    fs = GridFS(db)
    image = fs.find_one({'filename': filename})
    if image:
        return Response(image.read(), content_type=image.content_type)
    else:
        return "Image not found", 404
    
@app.route('/register')
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmPass = request.form.get('confirmpass')

        existing_user = users.find_one({'username': username})
        if password != confirmPass:
            flash('Password field must match')

        elif existing_user is None & password == confirmPass:
            hashed_password = generate_password_hash(password)
            users.insert_one({'username': username, 'email': email, 'password': hashed_password, 'role': 'customer'})
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists.', 'danger')

    return render_template('register.html')

@app.route('/remove_from_cart/<item_id>')
def remove_from_cart(item_id):
    cart = session.get('cart', {})
    if item_id in cart:
        cart[item_id] -= 1
        if cart[item_id] == 0:
            del cart[item_id]
        session['cart'] = cart
        flash('Item removed from cart.', 'success')
    else:
        flash('Item not found in cart.', 'danger')
    return redirect(url_for('menu'))

@app.route('/cart')
def show_cart():
    cart = session.get('cart', {})
    cart_items = []
    for item_id, quantity in cart.items():
        item = db.items.find_one({'_id': ObjectId(item_id)})
        if item:
            cart_items.append({'item': item, 'quantity': quantity})
    return render_template('cart.html', cart_items=cart_items)


if __name__ == '__main__':
    app.run(debug=True)
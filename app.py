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
from flask_wtf.csrf import CSRFProtect
import config
from bson import ObjectId


# Added to prevent backend secrets from being shared on public git repo. Requires a config.py file with connection string inside as a variable  "uri" 
uri = config.uri

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

app = Flask(__name__, template_folder='templates')
app.config['MONGO_URI'] = uri
app.secret_key = config.secret_key
csrf = CSRFProtect(app)
mongo = PyMongo(app)

if __name__ == "__main__":
    app.run(debug=True)

db = client.groupies
coll = db.groupies
users = db.users
carts = db.carts

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password
        self.active = True

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.active
    
@login_manager.user_loader
def load_user(user_id):
    user_data = users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_id=str(user_data['_id']), username=user_data['username'], password=user_data['password'])
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
    print("page loaded successfully")
    items = db.items.find()
    return render_template('menu.html', items=items)

@app.route('/')
def index():
    print("Page loaded successfully")
    items = db.items.find()
    return render_template('index.html', items=items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = None  # Initialize the user variable here
        user = users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            user_obj = User(username=user['username'], password=user['password'], user_id=str(user['_id']))
            login_user(user_obj)
            next_page = request.args.get('next')  # Get the value of the 'next' parameter
            if user['role'] == 'admin':
                return redirect(next_page or url_for('admin'))
            elif user['role'] == 'customer':
                return redirect(next_page or url_for('index'))  # Redirect to the customer dashboard or a different route
            else:
                flash('Invalid role.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    username=current_user.username


    if request.method == 'GET':
        items = db.items.find()
        return render_template('admin.html', items=items, username=username)
    
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
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if the user already exists
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            # Hash the password
            hashed_password = generate_password_hash(request.form['password'], method='sha256')
            # Insert the new user data into the database
            users.insert_one({
                'username': request.form['username'],
                'password': hashed_password,
                'email': request.form['email'],
                'role': 'customer',  # Add the 'role' field with the value 'customer'
                'cart': []  # Initialize the cart as an empty array
            })
            return redirect(url_for('login'))

        flash('Username already exists. Please choose a different one.')
    return render_template('register.html')



@app.route('/shoppingcart', methods=['GET', 'POST'])
@login_required
def shoppingcart():
    if request.method == 'POST':
        item_id = request.form['item_id']
        action = request.form['action']
        username = current_user.username

        user_cart = users.find_one({'username': username}).get('cart', [])

        if action == 'update':
            new_quantity = int(request.form['quantity'])
            for item in user_cart:
                if str(item['item_id']) == item_id:
                    item['quantity'] = new_quantity
                    break

        elif action == 'remove':
            user_cart = [item for item in user_cart if str(item['item_id']) != item_id]

        users.update_one({'username': username}, {'$set': {'cart': user_cart}})

    items = []
    user_cart = users.find_one({'username': current_user.username}).get('cart', [])
    for item in user_cart:
        item_data = db.items.find_one({'_id': ObjectId(item['item_id'])})
        if item_data:
            item_data['quantity'] = item['quantity']
            items.append(item_data)

    return render_template('shoppingcart.html', items=items)



@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    print("Request received at /add_to_cart")
    item_id = request.json.get('item_id')
    print(f"Item ID received: {item_id}")  # Add this line
    
    if not item_id:
        return jsonify({'error': 'Item ID is missing'}), 400

    # Check if the item exists in the items collection
    item = db.items.find_one({'_id': ObjectId(item_id)})
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Get the current user
    user = users.find_one({'username': current_user.username})

    # Check if the item is already in the user's cart
    cart_item = next((i for i in user['cart'] if str(i['item_id']) == item_id), None)

    if cart_item:
        # Update the item quantity in the cart
        users.update_one(
            {'_id': user['_id'], 'cart.item_id': ObjectId(item_id)},
            {'$inc': {'cart.$.quantity': 1}}
        )
    else:
        # Add the new item to the cart
        users.update_one(
            {'_id': user['_id']},
            {'$push': {'cart': {'item_id': ObjectId(item_id), 'quantity': 1}}}
        )

    return jsonify({'message': 'Item added to cart successfully'}), 200





if __name__ == '__main__':
    app.run(debug=True)
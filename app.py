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
import config

# Added to prevent backend secrets from being shared on public git repo. Requires a config.py file with connection string inside as a variable  "uri" 
uri = config.uri

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

app = Flask(__name__, template_folder='templates')
app.config['MONGO_URI'] = uri
app.secret_key = config.secret_key
mongo = PyMongo(app)

db = client.groupies
coll = db.groupies
users = db.users

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
        user = None  # Initialize the user variable here
        user = users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            login_user(User(username=user['username'], password=user['password']))
            next_page = request.args.get('next')  # Get the value of the 'next' parameter
            if user['role'] == 'admin':
                return redirect(next_page or url_for('admin'))
            elif user['role'] == 'customer':
                return redirect(next_page or url_for('dashboard'))  # Redirect to the customer dashboard or a different route
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
    
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Get password from form data
        confirmPass = request.form['confirmPass']  # Get confirmPass from form data
        existing_user = users.find_one({'username': username})

        if existing_user is not None:
            flash('username is already taken!', 'danger')
            return redirect(url_for('register'))
        elif existing_user is None and password == confirmPass:
            hashed_password = generate_password_hash(password)
            new_user = {
                'username': username,
                'password': hashed_password,
                'role': 'customer'  # Assuming a default role of 'customer'
            }
            users.insert_one(new_user)
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/shoppingcart')
def shoppingcart():
   
    return render_template('shoppingcart.html')





if __name__ == '__main__':
    app.run(debug=True)
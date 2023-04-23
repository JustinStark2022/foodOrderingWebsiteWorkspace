from flask import Flask, flash, redirect, render_template, request, jsonify, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
#from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://groupiespizzaadmin:Groupies12345@cluster0.3iw3bwg.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

app = Flask(__name__, template_folder='templates')
app.config['MONGO_URI'] = 'mongodb+srv://groupiespizzaadmin:Groupies12345@cluster0.3iw3bwg.mongodb.net/?retryWrites=true&w=majority'
mongo = PyMongo(app)

db = client.groupies
collection = db.groupies
users=db.users

def item_serializer(item):
    return {
        "id": str(item["_id"]),
        "name": item["name"],
    }

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = users.find_one({'username': username})

        if password == admin['password']:
            return redirect('/admin.html')
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
#    orders = mongo.db.orders.find()
#    return render_template('admin.html', orders=orders)
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
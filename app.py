from flask import Flask, flash, redirect, render_template, request, jsonify, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
#from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

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
        username = request.form.get('username')
        password = request.form.get('password')
        admin = users.find_one({'username': username})

        if admin is not None and password == admin['password']:
            return redirect('admin')
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method=='GET':
        items = db.items.find()
        return render_template('admin.html', items=items)
    
    if request.method=='POST':
        items = db.items.find()
        newName = request.form.get('newName')
        newPrice = request.form.get('newPrice')

        db.items.insert_one({'name':newName,'price':newPrice})
        
        return render_template('admin.html', items=items)

if __name__ == '__main__':
    app.run(debug=True)
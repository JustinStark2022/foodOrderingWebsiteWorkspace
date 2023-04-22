from flask import Flask, flash, redirect, render_template, request, jsonify, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates')
app.config['MONGO_URI'] = 'mongodb+srv://groupiespizzaadmin:Groupies12345@cluster0.3iw3bwg.mongodb.net/?retryWrites=true&w=majority'
mongo = PyMongo(app)

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

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/shoppingcart')
def shoppingcart():
    return render_template('shoppingcart.html')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = mongo.groupies.users.find_one({'username': username})

        if admin and check_password_hash(admin['password'], password):
            return redirect(url_for('index.html'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    orders = mongo.db.orders.find()
    return render_template('admin.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
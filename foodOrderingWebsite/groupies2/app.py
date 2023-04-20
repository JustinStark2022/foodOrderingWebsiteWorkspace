from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates')
app.config['MONGO_URI'] = '***REMOVED***'
mongo = PyMongo(app)

def item_serializer(item):
    return {
        "id": str(item["_id"]),
        "name": item["name"],
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = mongo.db.admins.find_one({'username': username})

        if admin and check_password_hash(admin['password'], password):
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    orders = mongo.db.orders.find()
    return render_template('admin_dashboard.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
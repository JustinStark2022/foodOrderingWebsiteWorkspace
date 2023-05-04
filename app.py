"""
Food Ordering Website
"""

import os  # for file paths
from decimal import Decimal  # for tax calculation
import logging  # for logging
from logging.handlers import RotatingFileHandler  # for logging
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    jsonify,
    url_for,
)
from flask_pymongo import PyMongo  # for connecting to the database
from bson.objectid import ObjectId  # for converting string id to bson object id
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)  # for password hashing
from pymongo.mongo_client import MongoClient  # for connecting to the database
from pymongo.server_api import ServerApi  # for server api version 1
from gridfs import GridFS  # for storing images in the database
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)  # for user authentication
from flask_wtf.csrf import CSRFProtect  # for CSRF protection
from flask_restful import Resource, Api  # for RESTful API
import config  # for secrets
# Added to prevent backend secrets from being shared on public git repo.
# # Requires a config.py file with connection string inside as a variable  "uri"
URI = config.uri

# Create a new client and connect to the server
client = MongoClient(URI, server_api=ServerApi("1"))

app = Flask(__name__, template_folder="templates")
app.config["MONGO_URI"] = URI
app.secret_key = config.secret_key
csrf = CSRFProtect(app)
mongo = PyMongo(app)

api = Api(app)  # Initialize the API

db = client.groupies
coll = db.groupies
users = db.users
carts = db.carts

# Set up logging
if not app.debug:
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=10)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Application startup")

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    """This class is used by Flask-Login to represent a user"""

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


class ShoppingCart(Resource):
    """This class pulls a shopping cart for the user from mongoDB"""

    @login_required
    def get(self):
        """This function returns the shopping cart for the user"""
        user = db.users.find_one({"username": current_user.username})
        cart_items = user.get("cart", [])
        cart_summary = calculate_cart_summary(cart_items)
        return jsonify(cart_summary)


api.add_resource(ShoppingCart, "/api/shoppingcart")


@login_manager.user_loader
def load_user(user_id):
    """This function is used by Flask-Login to load a user from the database given an id"""
    user_data = users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(
            user_id=str(user_data["_id"]),
            username=user_data["username"],
            password=user_data["password"],
        )
    else:
        return None


def item_serializer(item):
    """This function serializes an item from the database"""
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "price": item["price"],
        "image": item["image"],
    }


def calculate_cart_summary(items):
    """This function calculates the subtotal, tax, shipping, and total for the cart"""
    subtotal = round(
        sum(Decimal(str(item["price"])) * item["quantity"] for item in items), 2
    )
    tax_rate = Decimal("0.05")
    tax = round(subtotal * tax_rate, 2)
    shipping = round(Decimal("10") if subtotal < Decimal("50") else Decimal("0"), 2)
    total = round(subtotal + tax + shipping, 2)

    return {
    "subtotal": f"{subtotal:.2f}",
    "tax": f"{tax:.2f}",
    "shipping": f"{shipping:.2f}",
    "total": f"{total:.2f}",
}

# API Routes
@app.route("/about")
def about():
    """This function renders the about page"""
    print("Page loaded successfully")
    is_logged_in = current_user.is_authenticated
    return render_template(
        "about.html", current_user=current_user, is_logged_in=is_logged_in
    )


@app.route("/menu")
def menu():
    """This function renders the menu page"""
    print("Page loaded successfully")
    items = db.items.find()
    is_logged_in = current_user.is_authenticated
    return render_template(
        "menu.html", items=items, current_user=current_user, is_logged_in=is_logged_in
    )


@app.route("/")
def index():
    """This function renders the index page"""
    print("Page loaded successfully")
    items = db.items.find()
    is_logged_in = current_user.is_authenticated
    return render_template(
        "index.html", items=items, current_user=current_user, is_logged_in=is_logged_in
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """This function renders the login page and handles user login"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = None  # Initialize the user variable here
        user = users.find_one({"username": username})

        if user and check_password_hash(user["password"], password):
            user_obj = User(
                username=user["username"],
                password=user["password"],
                user_id=str(user["_id"]),
            )
            login_user(user_obj)
            next_page = request.args.get(
                "next"
            )  # Get the value of the 'next' parameter
            if user["role"] == "admin":
                return redirect(next_page or url_for("admin"))
            elif user["role"] == "customer":
                return redirect(
                    next_page or url_for("index")
                )  # Redirect to the customer dashboard or a different route
            else:
                flash("Invalid role.", "danger")
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


# admin route
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    """This function renders the admin page and handles adding new items to the menu"""
    username = current_user.username

    if request.method == "GET":
        items = db.items.find()
        return render_template("admin.html", items=items, username=username)

    if request.method == "POST":
        items = db.items.find()
        newName = request.form.get("newName")
        newPrice = request.form.get("newPrice")

        if newName and newPrice and "newImage" in request.files:
            newImage = request.files["newImage"]
            fs = GridFS(db)
            image_id = fs.put(
                newImage, filename=newImage.filename, content_type=newImage.content_type
            )

            # Round the price to 2 decimal places
            price = round(float(newPrice), 2)

            # Round the price to 2 decimal places
            price = round(float(newPrice), 2)

            db.items.insert_one(
                {
                    "name": newName,
                    "price": price,
                    "image": newImage.filename,
                    "image_id": image_id,
                }
            )
            flash("Item added successfully", "success")
        else:
            flash("Please fill in all the fields and provide an image", "danger")

        return render_template("admin.html", items=items)


@app.route("/logout")
@login_required
def logout():
    """This function logs the user out"""
    logout_user()
    return redirect(url_for("index"))


@app.route("/image/<filename>")
def image(filename):
    """This function returns the image with the given filename"""
    fs = GridFS(db)
    stored_image = fs.find_one({"filename": filename})
    if stored_image:
        return Response(stored_image.read(), content_type=stored_image.content_type)
    else:
        return "Image not found", 404


@app.route("/register", methods=["GET", "POST"])
def register():
    """This function renders the register page and handles user registration"""
    if request.method == "POST":
        # Check if the user already exists
        existing_user = users.find_one({"username": request.form["username"]})

        if existing_user is None:
            # Hash the password
            hashed_password = generate_password_hash(
                request.form["password"], method="sha256"
            )
            # Insert the new user data into the database
            users.insert_one(
                {
                    "username": request.form["username"],
                    "password": hashed_password,
                    "email": request.form["email"],
                    "role": "customer",  # Add the 'role' field with the value 'customer'
                    "cart": [],  # Initialize the cart as an empty array
                }
            )
            return redirect(url_for("login"))

        flash("Username already exists. Please choose a different one.")
    return render_template("register.html")


@app.route("/shoppingcart")
@login_required
def shopping_cart():
    """This function renders the shopping cart page"""
    user = users.find_one({"username": current_user.username})
    is_logged_in = current_user.is_authenticated
    cart_items = user["cart"]

    items = []
    for item in cart_items:
        item_details = db.items.find_one({"_id": item["item_id"]})
        item_details["quantity"] = item["quantity"]
        items.append(item_details)

    cart_summary = calculate_cart_summary(items)

    return render_template(
        "shoppingcart.html",
        username=current_user.username,
        items=items,
        cart_summary=cart_summary,
        is_logged_in=is_logged_in,
    )


# Add to cart route
@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    """This function adds an item to the user's cart"""
    app.logger.info("Request received at /add_to_cart")
    item_id = request.json.get("item_id")
    app.logger.info("Item ID received: %s, {item_id}")

    if not item_id:
        return jsonify({"success": False, "message": "Item ID is missing"}), 400

    # Check if the item exists in the items collection
    item = db.items.find_one({"_id": ObjectId(item_id)})
    if not item:
        return jsonify({"success": False, "message": "Item not found"}), 404

    # Get the current user
    user = users.find_one({"username": current_user.username})
    app.logger.info("User's cart before update: %s, {user['cart']}")

    # Check if the item is already in the user's cart
    cart_item = next((i for i in user["cart"] if str(i["item_id"]) == item_id), None)

    if cart_item:
        # Update the item quantity in the cart
        users.update_one(
            {"_id": user["_id"], "cart.item_id": ObjectId(item_id)},
            {"$inc": {"cart.$.quantity": 1}},
        )
    else:
        # Add the new item to the cart
        users.update_one(
            {"_id": user["_id"]},
            {"$push": {"cart": {"item_id": ObjectId(item_id), "quantity": 1}}},
        )

    # Fetch the updated user data
    user = users.find_one({"username": current_user.username})
    app.logger.info("User's cart after update: %s, {user['cart']}")

    return jsonify({"success": True, "message": "Item added to cart successfully"}), 200


# Update cart route
@app.route("/update_cart", methods=["POST"])
@login_required
def update_cart():
    """This function updates the quantity of an item in the user's cart"""
    app.logger.info("update_cart route called")
    app.logger.info("Request payload:%s, {request.json}")
    action = request.json.get("action")
    item_id = request.json.get("item_id")

    if not action or not item_id:
        app.logger.error("Action or Item ID is missing")
        return jsonify({"error": "Action or Item ID is missing"}), 400

    # Get the current user
    user = users.find_one({"username": current_user.username})

    if action == "increment":
        result = users.update_one(
            {"_id": user["_id"], "cart.item_id": ObjectId(item_id)},
            {"$inc": {"cart.$.quantity": 1}},
        )
    elif action == "decrement":
        result = users.update_one(
            {"_id": user["_id"], "cart.item_id": ObjectId(item_id)},
            {"$inc": {"cart.$.quantity": -1}},
        )

    elif action == "delete":
        result = users.update_one(
            {"_id": user["_id"]},
            {"$pull": {"cart": {"item_id": ObjectId(item_id)}}},
        )
    else:
        app.logger.error("Invalid action")
        return jsonify({"error": "Invalid action"}), 400

    if result.modified_count == 0:
        app.logger.error("No documents were updated")
        return jsonify({"error": "No documents were updated"}), 400

    app.logger.info("Cart updated successfully")
    return jsonify({"message": "Cart updated successfully"}), 200


@app.route("/checkout")
def checkout():
    """This function renders the checkout page"""
    return render_template("checkout.html")


if __name__ == "__main__":
    app.run(debug=True)

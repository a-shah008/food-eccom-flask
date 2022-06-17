from flask_login import login_user, current_user, logout_user, login_required
from enum import unique
from flask import flash, request
from sqlalchemy.orm import backref
from app import db, login_manager, app
from flask_login import UserMixin
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(60))
    phonenumber = db.Column(db.String(15), unique=True)
    image_file = db.Column(db.String(60), default="default.jpg")
    confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    creditcardnum = db.Column(db.Integer)
    securitycode = db.Column(db.Integer)
    expirationdate = db.Column(db.String(50))
    street = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postalzip = db.Column(db.String(100))
    billing_information_saved = db.Column(db.Boolean, nullable=False, default=False)
    carts = db.relationship("Cart", backref="buyer")

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({"user_id": self.id}).decode("utf-8")

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token)["user_id"]
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"{self.email}"

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_price = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, nullable=False, default=False)
    purchase_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    purchase_confirmed_date = db.Column(db.String(200))
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    lineitems = db.relationship("Lineitem", backref="all_lineitems")

    def __repr__(self):
        return f"Cart: {self.id}"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lineitem = db.relationship("Lineitem", backref="specific_product")
    image_file = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    size = db.Column(db.String(50), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f"{self.name}"

class Lineitem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __repr__(self):
        return f"{self.name} with a quantity of {self.quantity}"


from logging import warning
from threading import active_count
from flask import url_for, render_template, request, redirect, flash, session
from flask_wtf import form
from app import app, db, bcrypt, mail
from app.forms import AdminEditInitializeForm, RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm, AddToCart, EditInformationForm, RemoveAllQuantityOfProduct, EmptyCartForm, EditItemQuantityForm, ChangeEmailForm, SixDigitPinForm, AuthenticateAdminForm, AdminDeleteProductForm, AdminAddProductForm, AdminEditInitializeForm, AdminEditProductForm, FilterForm
from app.models import db, User, Cart, Lineitem, Product
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import datetime
import random
import math
import uuid

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


ALL_EMAILS_SENDER = os.environ.get('EMAIL')
ADMIN_PIN = "963241"
sixdigitcode = ""
form_new_email_data = ""

def current_cart():
    active_cart = Cart.query.filter_by(active=True, buyer_id=current_user.id).first()
    if active_cart:
        active_cart = active_cart
    else:
        active_cart = Cart(total_price=0, active=True, purchase_confirmed=False, purchase_confirmed_date="Purchase not confirmed yet", buyer_id=current_user.id)
        db.session.add(active_cart)
        db.session.commit()
    return active_cart

def item_count():
    item_counter = 0
    active_cart = current_cart()
    items = Lineitem.query.filter_by(cart_id=active_cart.id).all()
    for item in items:
        item_counter += item.quantity
    item_counter = item_counter
    return item_counter

def all_products():
    active_cart = current_cart()
    user_items = Lineitem.query.filter_by(cart_id=active_cart.id).all()
    total_price = 0.0
    products = {}
    for item in user_items:
        item_id = item.product_id
        item_quantity_li = item.quantity
        product = Product.query.filter_by(id=item_id).first()
        products[product] = item_quantity_li
        db.session.commit()
    for item in products:
        total_price += item.unit_price * products[item]
        active_cart.total_price = total_price
        db.session.commit()
    
    return total_price, products, user_items

def send_authentication_email(user, token):
    msg = Message('Account Activation', sender=ALL_EMAILS_SENDER, recipients=[user.email])
    msg.body = f'''Thank you for signing up! To activate your account, please follow the link bellow:

{url_for("confirm_email", token=token, _external=True)}
'''
    mail.send(msg)

def create_six_digit_code():
    digits = "0123456789"
    sixdigitcode = ""
    for i in range(6) :
        sixdigitcode += digits[math.floor(random.random() * 10)]

    return sixdigitcode

def send_changed_email_confirmation(user):
    global sixdigitcode
    sixdigitcode = create_six_digit_code()
    msg = Message('Email Changed Confirmation', sender=ALL_EMAILS_SENDER, recipients=[user])
    msg.body = f'''Your email change request has been successfully received. Please enter the following six digit code into the provided URL:

    {sixdigitcode}

{url_for("confirm_changed_email", _external=True)}
'''
    mail.send(msg)

    return sixdigitcode

def send_order_confirmation_email(user, total_price):
    active_cart = current_cart()
    item_objs_list = []
    items = Lineitem.query.filter_by(cart_id=active_cart.id).all()
    for item in items:
        item_objs_list.append(item)
    msg = Message("Order Received", sender=ALL_EMAILS_SENDER, recipients=[user.email])
    msg.body = f'''Thank you for placing an order in the JSMC Food Court! Your order has been successfully receieved by the JSMC Food Court team.

Your Order Total: ${total_price}0

You can view your order histories and summaries by following this link: {url_for("account", _external=True)}
'''
    mail.send(msg)

def account_activation_email(user_email):
    msg = Message('Account Activation', sender=ALL_EMAILS_SENDER, recipients=[user_email])
    msg.body = f'''Thank you for previously signing up. To finish your account activation, please follow the directions in the link below:

{url_for("activate_account", _external=True)}
'''
    mail.send(msg)

@app.route("/", methods=["GET", "POST"])
def snack_page():
    edit_quantity_form = EditItemQuantityForm()
    filter_form = FilterForm()
    addtocart = AddToCart()
    if request.method == "POST":
        if filter_form.validate_on_submit():
            print("Button click received")
            if filter_form.name.data and filter_form.minimum_unit_price.data and filter_form.maximum_unit_price.data == None:
                flash("You have not selected any filtering options. Please try again.", "warning")
                return redirect(url_for("snack_page"))
        else:
            return redirect(url_for("snack_page"))

        if request.form.get("addtocart"):
            active_cart = current_cart()
            item = request.form.get("addtocart")
            item_obj = Product.query.filter_by(name=item).first()
            item_price = float(item_obj.unit_price)
            item_quantity = int(addtocart.quantity.data)
            item_total_price = 0
            item_total = int(item_price) * int(item_quantity)
            item_total_price = item_total_price + item_total
            active_cart.total_price = active_cart.total_price + item_total_price
            item_exists_obj = Lineitem.query.filter_by(name=item, cart_id=active_cart.id).first()
            if item_exists_obj:
                difference = 10 - item_exists_obj.quantity
                if item_quantity > difference:
                    flash(f"Maximum quantity of 10 can be ordered. Your cart exceeded this limit.", "warning")
                    return redirect(url_for("snack_page"))
                elif item_quantity <= difference:
                    item_exists_obj.quantity = item_exists_obj.quantity + item_quantity
                    flash(f"{item_exists_obj.name} ({item_exists_obj.quantity}) has been successfully added to cart.", "success")
                    db.session.commit()
                return redirect(url_for("snack_page"))
            else:
                new_lineitem = Lineitem(name=item, quantity=item_quantity, unit_price=item_price, cart_id=active_cart.id, product_id=item_obj.id)
                db.session.add(new_lineitem)
                db.session.commit()
                flash(f"{new_lineitem.name} (Quantity: {new_lineitem.quantity}) has been successfully added to cart.", "success")
            return redirect(url_for("snack_page"))
        
        if request.form.get("emptycartbutton"):
            active_cart = current_cart()
            items_in_cart = Lineitem.query.filter_by(cart_id=active_cart.id).all()
            for item in items_in_cart:
                db.session.delete(item)
                db.session.commit()
            active_cart.total_price = 0
            db.session.commit()
            return redirect(url_for("snack_page"))

        if request.form.get("deleteallofproduct"):
            removal_item = request.form.get("deleteallofproduct")
            active_cart = current_cart()
            removal_item_obj = Product.query.filter_by(name=removal_item).first()
            db_removal_item = Lineitem.query.filter_by(cart_id=active_cart.id, product_id=removal_item_obj.id).first()
            db.session.delete(db_removal_item)
            db.session.commit()
            return redirect(url_for("snack_page"))

        if request.form.get('savenewquantitybutton'):
            if edit_quantity_form.validate_on_submit():
                active_cart = current_cart()
                new_quantity_user = request.form.get("new_quantity_input")
                item_name = request.form.get("savenewquantitybutton")
                original_lineitem_obj = Lineitem.query.filter_by(name=item_name).first()
                original_lineitem_obj.quantity = new_quantity_user
                db.session.commit()

            return redirect(url_for("snack_page"))

    elif request.method == "GET":
        specials = Product.query.filter_by(category="specials")
        sweets = Product.query.filter_by(category="sweets")
        khakharas = Product.query.filter_by(category="khakharas")
        drysnacks = Product.query.filter_by(category="drysnacks")
        removeallform = RemoveAllQuantityOfProduct()
        empty_cart_form = EmptyCartForm()
        edit_quantity_form = EditItemQuantityForm()
        item_counter = 0
        total_price = 0.0
        products = {}
        user_items = ""
        if current_user.is_authenticated:
            active_cart = current_cart()
            item_counter = item_count()
            
            total_price, products, user_items = all_products()
        return render_template("index.html", edit_quantity_form=edit_quantity_form, empty_cart_form=empty_cart_form, removeallform=removeallform, total_price=total_price, products=products, specials=specials, sweets=sweets, khakharas=khakharas, drysnacks=drysnacks, addtocart=addtocart, user_cart=user_items, item_counter=item_counter, filter_form=filter_form)

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    active_cart = current_cart()
    form = EditInformationForm()
    item_counter = 0
    total_price = 0.0
    item_counter = item_count()

    total_price, products, user_items = all_products()

    if request.method == "POST":
        if request.form.get("SaveBillingInformation"):
            current_user.creditcardnum = form.creditcardnum.data
            current_user.securitycode = form.securitycode.data
            current_user.expirationdate = form.expirationdate.data
            current_user.street = form.street.data
            current_user.city = form.city.data
            current_user.state = form.state.data
            current_user.postalzip = form.postalzip.data
            current_user.billing_information_saved = True
            db.session.commit()
            flash("Information has been saved.", "success")
            return redirect(url_for("checkout"))
        if request.form.get("PlaceOrderConfirm"):
            lineitems_exist = Lineitem.query.filter_by(cart_id=active_cart.id).all()
            if lineitems_exist:
                lineitems_exist_boolean_check = True
            else:
                flash("Your cart is empty. Please add items to your cart first.", "warning")
                return redirect(url_for("snack_page"))
            if current_user.billing_information_saved == True:
                billing_information_boolean_check = True
            else:
                flash("Please fill out all of your billing information.", "warning")
                return redirect("checkout")
            if current_user.confirmed == True:
                user_confirmed_boolean_check = True
            else:
                token = s.dumps(current_user.email, salt="email-confirm")
                send_authentication_email(current_user, token)
                flash("Your account has not been activated yet. An email has been sent with instructions to activate your account.", "warning")
                return redirect(url_for("checkout"))
            
            if lineitems_exist_boolean_check and billing_information_boolean_check and user_confirmed_boolean_check == True:
                active_cart.purchase_confirmed = True
                active_cart.purchase_confirmed_date = datetime.date.today()
                active_cart.active = False
                db.session.commit()
                send_order_confirmation_email(current_user, total_price)
                flash("Thank you for your order!", "success")
                return redirect(url_for("snack_page"))

    elif request.method == "GET":
        form.creditcardnum.data = current_user.creditcardnum
        form.securitycode.data = current_user.securitycode
        form.expirationdate.data = current_user.expirationdate
        form.street.data = current_user.street
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.postalzip.data = current_user.postalzip
        db.session.commit()

    return render_template("checkout.html", products=products, item_counter=item_counter, form=form, user_cart=user_items, total_price=total_price, current_user=current_user)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('snack_page'))
    form = RegistrationForm()
    if request.method == "POST":
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
            user = User(email=form.email.data, phonenumber=form.phonenumber.data, password=hashed_password, creditcardnum="N/A", securitycode="N/A", expirationdate="N/A", street="N/A", city="N/A", state="N/A", postalzip="N/A", billing_information_saved=False)
            db.session.add(user)
            db.session.commit()
            user_obj = User.query.filter_by(email=form.email.data).first()
            token = s.dumps(form.email.data, salt="email-confirm")
            send_authentication_email(user_obj, token)
            flash("To activate your account, follow the instructions in an email that has been sent.", "info")
    return render_template("register.html", title="Register", form=form)

@app.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)
    except SignatureExpired and BadTimeSignature:
        return "This token does not work, either it was malicious or the token expired"
    user_obj = User.query.filter_by(email=email).first()
    user_obj.confirmed = True
    db.session.commit()
    login_user(user_obj)
    flash(f"Welcome, {current_user.email}. You are successfully logged in!", "success")
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for("snack_page"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('snack_page'))
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash(f"Welcome, {current_user.email}. You are successfully logged in!", "success")
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for("snack_page"))
            else:
                flash("Login unsucessful. Please check email and password.", "danger")
            
    return render_template("login.html", title="Login", form=form)

@app.route("/logout")
def logout():
    current_user.is_admin = False
    db.session.commit()
    logout_user()
    return redirect(url_for("snack_page"))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + str(f_ext)
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    account_activated = current_user.confirmed
    form = UpdateAccountForm()
    history_of_carts = Cart.query.filter_by(buyer_id=current_user.id, active=False, purchase_confirmed=True).all()
    lineitem_objs = {}
    for cart in history_of_carts:
        lineitems = Lineitem.query.filter_by(cart_id=cart.id)
        for li in lineitems:
            lineitem_objs[li] = cart.id
    if request.method == "POST":
        if form.validate_on_submit():
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                current_user.image_file = picture_file

            current_user.phonenumber = form.phonenumber.data
            current_user.creditcardnum = form.creditcardnum.data
            current_user.securitycode = form.securitycode.data
            current_user.expirationdate = form.expirationdate.data
            current_user.street = form.street.data
            current_user.city = form.city.data
            current_user.state = form.state.data
            current_user.postalzip = form.postalzip.data
            current_user.billing_information_saved = True
            db.session.commit()
            flash("Your account has been updated!", "success")
            return redirect(url_for("account"))

    elif request.method == "GET":
        form.phonenumber.data = current_user.phonenumber
        form.creditcardnum.data = current_user.creditcardnum
        form.securitycode.data = current_user.securitycode
        form.expirationdate.data = current_user.expirationdate
        form.street.data = current_user.street
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.postalzip.data = current_user.postalzip
        db.session.commit()
        
    image_file = url_for('static', filename='profile_pics/' + str(current_user.image_file))
    return render_template("account.html", account_activated=account_activated, lineitems=lineitem_objs, history_of_carts=history_of_carts, title="Account", image_file=image_file, form=form)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender="aaravshah.300@gmail.com", recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for("reset_token", token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("snack_page"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("An email has been sent with instructions to reset your password.", "info")
        return redirect(url_for("login"))
    return render_template("reset_request.html", title="Reset Password", form=form)

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("snack_page"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been reset! You are now able to login.", "success")
        return redirect(url_for('login'))

    return render_template("reset_token.html", title="Reset Password", form=form)

@app.route("/clear_order_history", methods=["GET", "POST"])
def clear_order_history():
    history_of_carts = Cart.query.filter_by(buyer_id=current_user.id, active=False, purchase_confirmed=True).all()
    for cart in history_of_carts:
        db.session.delete(cart)
        db.session.commit()
    flash("Your Order History has been cleared.", "success")
    return redirect(url_for("account"))

@app.route("/change_email", methods=["GET", "POST"])
@login_required
def change_email():
    form = ChangeEmailForm()
    if request.method == "POST":
        if form.validate_on_submit():
            global form_new_email_data
            form_new_email_data = form.new_email.data
            send_changed_email_confirmation(form.new_email.data)
            return redirect(url_for("confirm_changed_email"))
    elif request.method == "GET":
        form.new_email.data = current_user.email
        db.session.commit()
    return render_template("change_email.html", form=form)

@app.route("/confirm_changed_email/", methods=["GET", "POST"])
@login_required
def confirm_changed_email():
    form = SixDigitPinForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user_input = str(form.sixdigitcode.data)
            correct_code = str(sixdigitcode)
            if user_input == correct_code:
                current_user.email = form_new_email_data
                db.session.commit()
                flash(f"Your email has been successfully changed. Welcome, {current_user.email}.", "success")
                return redirect(url_for("snack_page"))
            else:
                flash("That is an incorrect code. Please try again.", "warning")
                return redirect(url_for("confirm_changed_email"))
    return render_template("confirm_changed_email.html", form=form, form_new_email_data=form_new_email_data)

@app.route("/resend_email_confirmation_email", methods=["GET", "POST"])
@login_required
def resend_email_confirmation_email():
    send_changed_email_confirmation(form_new_email_data)
    flash("A new email has been successfully sent to the email provided.", "info")
    return redirect(url_for("confirm_changed_email"))

@app.route("/send_activate_account_email", methods=["GET", "POST"])
@login_required
def send_activate_account_email():
    account_activation_email(current_user.email)
    flash("An account activation email has been sent. Follow the instructions given in the email to finish activating your account.", "info")
    return redirect("account")

@app.route("/activate_account", methods=["GET", "POST"])
@login_required
def activate_account():
    current_user.confirmed = True
    db.session.commit()
    flash("Your account has been successfully activated!", "success")
    return redirect(url_for("account"))

@app.route("/redirect_to_admin_panel", methods=["GET", "POST"])
def redirect_to_admin_panel():
    token = uuid.uuid1()
    return redirect(url_for("admin_panel", token=token))

@app.route("/authenticate_admin", methods=["GET", "POST"])
@login_required
def authenticate_admin():
    if current_user.is_admin is False:
        form = AuthenticateAdminForm()
        if request.method == "POST":
            if form.validate_on_submit():
                if str(form.admin_pin.data) == str(ADMIN_PIN) and bcrypt.check_password_hash(current_user.password, form.password.data):
                    current_user.is_admin = True
                    db.session.commit()
                    token = uuid.uuid1()
                    flash("You have been successfully authorized as an admin.", "success")
                    return redirect(url_for("admin_panel", token=token))
                else:
                    flash(f"Those are incorrect values. Please try again.", "warning")
                    return redirect(url_for("authenticate_admin"))
    else:
        return redirect(url_for("redirect_to_admin_panel"))

    return render_template("authenticate_admin.html", form=form)

@app.route("/admin_panel/<token>", methods=["GET", "POST"])
@login_required
def admin_panel(token):
    if current_user.is_admin and current_user.confirmed is True:
    
        orders = Cart.query.all()
        users = User.query.filter_by(is_admin=False).all()
        admins = User.query.filter_by(is_admin=True).all()
        orders_objs_with_user_email = {}
        for order in orders:
            if order.purchase_confirmed == True:
                orders_user_id = order.buyer_id
                for user in users:
                    if user.id == orders_user_id:
                        orders_objs_with_user_email[order] = user.email

        return render_template("admin_panel.html", orders_dict=orders_objs_with_user_email, users=users, admins=admins)

    else:
        flash("You are not authorized to access this page. Please make sure you have activated your account and are an admin.", "warning")
        return redirect(url_for("snack_page"))

@app.route("/admin_edit_products", methods=["GET", "POST"])
@login_required
def admin_edit_products():
    if current_user.is_admin and current_user.confirmed is True:
        
        all_products = Product.query.all()
        delete_product_form = AdminDeleteProductForm()
        edit_initialize_product_form = AdminEditInitializeForm()
        product_counter = len(Product.query.all())

        if request.method == "POST":
            if request.form.get('delete_product_btn'):
                name_of_product = request.form.get('delete_product_btn')
                to_be_deleted_obj = Product.query.filter_by(name=name_of_product).first()

                db.session.delete(to_be_deleted_obj)
                db.session.commit()
                flash(f"{name_of_product} has been deleted.", "success")
                all_products = Product.query.all()
                return redirect(url_for("redirect_to_admin_panel"))
            
            if request.form.get('edit_initialize_product_btn'):
                edit_product = request.form.get('edit_initialize_product_btn')

                return redirect(url_for("admin_edit_specific_product", product=edit_product))


        return render_template("admin_edit_products.html", all_products=all_products, delete_product_form=delete_product_form, product_counter=product_counter, edit_initialize_product_form=edit_initialize_product_form)

    else:
        flash("You are not authorized to access this page. Please make sure you have activated your account and are an admin.", "warning")
        return redirect(url_for("snack_page"))

def save_product_image(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/new_product_pics/', picture_fn)
    form_picture.save(picture_path)
    return picture_fn

@app.route("/admin_add_products", methods=["GET", "POST"])
@login_required
def admin_add_products():
    if current_user.is_admin and current_user.confirmed is True:
        
        form = AdminAddProductForm()
        
        if request.method == "POST":
            if form.validate_on_submit():
                image_of_product = save_product_image(form.image_file.data)
                name_of_product = form.name.data.strip()
                size_of_product = form.size.data.strip()
                unit_price_of_product = str(form.unit_price.data)
                category_of_product = str(request.form.get('category_input')).strip()
                
                image_of_product = "/static/new_product_pics/" + image_of_product

                new_product = Product(image_file=image_of_product, name=name_of_product, size=size_of_product, unit_price=unit_price_of_product, category=category_of_product)
                db.session.add(new_product)
                db.session.commit()

                flash(f"{name_of_product} successfully added to database.", "success")
                return redirect(url_for("redirect_to_admin_panel"))

        return render_template("admin_add_products.html", form=form)

    else:
        flash("You are not authorized to access this page. Please make sure you have activated your account and are an admin.", "warning")
        return redirect(url_for("snack_page"))

@app.route("/admin_edit_specific_product/<product>", methods=["GET", "POST"])
@login_required
def admin_edit_specific_product(product):
    if current_user.is_admin and current_user.confirmed is True:
        
        product_obj = Product.query.filter_by(name=product).first()
        form = AdminEditProductForm()
        
        if request.method == "POST":
            if form.validate_on_submit():
                product_obj.name = form.name.data
                product_obj.size = form.size.data
                product_obj.unit_price = form.unit_price.data
                product_obj.category = request.form.get('category_input')
                
                db.session.commit()

                flash(f"{form.name.data} has been successfully edited.", "success")
                return redirect(url_for("redirect_to_admin_panel"))

        elif request.method == "GET":
            form.name.data = product_obj.name
            form.size.data = product_obj.size
            form.unit_price.data = product_obj.unit_price
            product_category = product_obj.category
            
            return render_template("admin_edit_specific_product.html", form=form, product_obj=product_obj, product_category=product_category)

    else:
        flash("You are not authorized to access this page. Please make sure you have activated your account and are an admin.", "warning")
        return redirect(url_for("snack_page"))

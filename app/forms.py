from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, BooleanField, IntegerField, PasswordField, SelectField, FloatField
from wtforms import validators
from wtforms.validators import DataRequired, Length, Email, ValidationError, NumberRange, EqualTo
from wtforms.widgets.core import SubmitInput
from app.models import User
from flask_login import current_user
import random

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    phonenumber = StringField("Phone Number", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

    submit = SubmitField("Submit")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email already exists. Please choose a different one.")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class UpdateAccountForm(FlaskForm):
    phonenumber = StringField("Phone Number")
    picture = FileField("Upload Profile Picture", validators=[FileAllowed(['jpg', 'png'])])

    creditcardnum = StringField("Credit Card Number")
    securitycode = StringField("CVV Code")
    expirationdate = StringField("Credit Card Expiration Date")
    street = StringField("Street")
    city = StringField("City")
    state = StringField("State / Province")
    postalzip = StringField("Postal / Zip Code")

    submit = SubmitField("Update Account")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("That email already exists. Please choose a different one.")

class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no account with that email. You must register first.")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), EqualTo("confirm_password")])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Reset Password")

class AddToCart(FlaskForm):
    quantity = SelectField("Quantity", validators=[DataRequired()], choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
    addbtn = SubmitField("Add To Cart")

class RemoveAllQuantityOfProduct(FlaskForm):
    remove = SubmitField("Remove Item")

class EditInformationForm(FlaskForm):
    creditcardnum = StringField("Credit Card Number", validators=[DataRequired()])
    securitycode = StringField("CVV Code", validators=[DataRequired()])
    expirationdate = StringField("Expiration Date", validators=[DataRequired()])
    street = StringField("Street", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    state = StringField("State / Province", validators=[DataRequired()])
    postalzip = StringField("Postal / Zip Code", validators=[DataRequired()])
    submit = SubmitField("Save Billing Information")

    def validate_creditcardnum(self, creditcardnum):
        creditcardnum = str(creditcardnum.data)
        ccnum = list(creditcardnum.data.strip())
        check_digit = ccnum.pop()
        ccnum.reverse()
        processed_digits = []
        for index, digit in enumerate(ccnum):
            if index % 2 == 0:
                doubled_digit = int(digit) * 2
                if doubled_digit > 9:
                    doubled_digit = doubled_digit - 9
                processed_digits.append(doubled_digit)
            else:
                processed_digits.append(int(digit))
        total = int(check_digit) + sum(processed_digits)
        if total % 10 != 0:
            raise ValidationError("That is an invalid Credit Card number. Please check your input.")

class EmptyCartForm(FlaskForm):
    empty_cart = SubmitField("Empty Cart")

class EditItemQuantityForm(FlaskForm):
    save_new_quantity = SubmitField("Save Quantity")

class ChangeEmailForm(FlaskForm):
    new_email = StringField("New Email Address", validators=[DataRequired()])
    submit = SubmitField("Save Changes")

    def validate_new_email(self, new_email):
            if new_email.data != current_user.email:
                user = User.query.filter_by(email=new_email.data).first()
                if user:
                    raise ValidationError("That email already exists. Please choose a different one.")

class SixDigitPinForm(FlaskForm):
    sixdigitcode = StringField("Six Digit Code", validators=[Length(6,6, "The code must be six digits long."), DataRequired()])
    submit = SubmitField("Save Changes")

class AuthenticateAdminForm(FlaskForm):
    admin_pin = IntegerField("Admin Pin", validators=[DataRequired("Please input the correct value.")])
    password = StringField("Account Password", validators=[DataRequired("Please input the correct value.")])
    submit = SubmitField("Submit")

class AdminDeleteProductForm(FlaskForm):
    delete = SubmitField("Delete")

class AdminAddProductForm(FlaskForm):
    image_file = FileField("Upload Image of Product", validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'])])
    name = StringField("Name", validators=[DataRequired("That is an incorrect value.")])
    size = StringField("Size with Measurment (Grams, Ounces, etc.)", validators=[DataRequired("That is an incorrect value.")])
    unit_price = FloatField("Unit Price in Float Form (ex. 1.00, do not add dollar sign)", validators=[DataRequired("That is an incorrect value.")])

    save = SubmitField("Save Changes")

class AdminEditInitializeForm(FlaskForm):

    edit = SubmitField("Edit")

class AdminEditProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("That is an incorrect value.")])
    size = StringField("Size with Measurment (Grams, Ounces, etc.)", validators=[DataRequired("That is an incorrect value.")])
    unit_price = FloatField("Unit Price in Float Form (ex. 1.00, do not add dollar sign)", validators=[DataRequired("That is an incorrect value.")])

    save = SubmitField("Save Changes")

class FilterForm(FlaskForm):
    name = StringField("Name")
    minimum_unit_price = FloatField("Minimum Unit Price")
    maximum_unit_price = FloatField("Maximum Unit Price")
    category = StringField("Category")

    filter = SubmitField("Filter")


from flask import Flask,render_template,redirect,request,url_for,abort,flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,login_user,LoginManager,current_user,logout_user,login_required
from sqlalchemy.orm import relationship
from forms import Login_form,Signup_form,Config_product,Edit_profile_form,Select_status
from werkzeug.security import generate_password_hash,check_password_hash
from functools import wraps
import stripe
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap5(app)

"""_____________________________________________________________________ABOUT THIS PROJECT:
this is an ecommerce website that has most of the essential abilities to add,delete,and manage products in some view modes,
 it uses relational database with 3 table to store User details,Products,and Purchase details 
seperately with needed relation between each other.
i used stripe test mode with its webhooks and test card to check every things works properly.
it also has a Admin_panel with address of /dashboard to manage .
all the UI needs much more working and fixing But i focused on Logics and functions to create my first ecommerce website.

________________________________________________________________________________________"""


"""_____________________________________________________________________AUTHENTICATION_____________________________________________________________________________"""

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User,user_id)

"""________________________________________________________________________DATABASE________________________________________________________________________________"""



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
db = SQLAlchemy()
db.init_app(app)


#CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    email =db.Column(db.String(100),unique=True)
    address = db.Column(db.String(250))
    phone_number = db.Column(db.String(100))
    password = db.Column(db.String(100))

    person = relationship("Purchase",back_populates="buyer")


class Product(UserMixin, db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(100))
    decription = db.Column(db.String(250))
    price = db.Column(db.Float)
    image_url = db.Column(db.String(250))
    quantity = db.Column(db.Integer)

    prdc = relationship("Purchase", back_populates="thing")


class Purchase(db.Model):
    __tablename__ = "purchase"
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer,db.ForeignKey("users.id"))
    product_id = db.Column(db.Integer,db.ForeignKey("product.id"))
    thing = relationship("Product",back_populates="prdc")
    buyer = relationship("User",back_populates="person")
    # status = db.Column(ENUM('pending', 'shipped', 'delivered', 'cancelled', name='order_status'))
    status = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)


with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


@login_manager.unauthorized_handler
def custom_unauthorized_message():

    return abort(403)

"""_________________________________________________________________________ROUTES_________________________________________________________________________________"""


@app.route("/", methods=['GET','POST'])
def Home():
    result = db.session.execute(db.select(Product))
    all_product = result.scalars().all()
    if current_user.is_authenticated:
        purchases = len(Purchase.query.filter_by(buyer_id=current_user.id,status="pending").all())
    else:
        purchases = 0

    return render_template("index.html",current_user=current_user,all_product=all_product,purchases=purchases)


@app.route("/all-products", methods=['GET', 'POST'])
def All_products():
    result = db.session.execute(db.select(Product))
    all_product = result.scalars().all()
    if current_user.is_authenticated:
        purchases = len(Purchase.query.filter_by(buyer_id=current_user.id,status="pending").all())
    else:
        purchases = 0

    return render_template("all-products.html", current_user=current_user, all_product=all_product, purchases=purchases)

@app.route("/login", methods=['GET','POST'])
def Login():
    form = Login_form()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('Login'))
        elif not check_password_hash(user.password,password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('Login'))
        else:
            login_user(user)
            return redirect(url_for("Home"))


    return render_template("login.html",form=form,current_user=current_user)



@app.route("/sign_up", methods=['GET','POST'])
def Sign_up():
    form = Signup_form()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted = generate_password_hash(
            form.password.data,method= 'pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(

            name= form.name.data,
            email = form.email.data,
            address = form.address.data,
            phone_number = form.number.data,
            password = hash_and_salted ,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("Home"))

    return render_template("signup.html",form=form,current_user=current_user)



@app.route("/add_product", methods=['GET','POST'])
@login_required
@admin_only
def Add():
    form = Config_product()
    if form.validate_on_submit():
        if form.image_url.data != "":
            url = form.image_url.data
            flash(f"uploaded successfully!", "success")
            print(url)
        else:
            file = request.files['upload']

            flash(f"File '{file.filename}' uploaded successfully!", "success")
            url = f"static/assets/img/{file.filename}"  # creating address to server
            print(url)
            file.save(url)

        new_product = Product(

            name= form.name.data,
            category = form.category.data,
            decription = form.decription.data,
            price = form.price.data,
            image_url = url,
            quantity = form.quantity.data,
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('Add'))
    return render_template("add.html",form=form)


@app.route("/edit", methods=['GET','POST'])
@login_required
@admin_only
def Edit():
    id = request.args.get("id")
    form = Config_product()
    if request.method == "GET":
        result = Product.query.filter_by(id=id).first()
        form.name.data = result.name
        form.price.data = result.price
        form.quantity.data = result.quantity
        form.decription.data = result.decription
        form.category.data = result.category
        form.image_url.data = result.image_url

    if form.validate_on_submit():
        if form.image_url.data != "":
            url = form.image_url.data
            flash(f"uploaded successfully!", "success")
            print(url)
        else:
            file = request.files['upload']

            flash(f"File '{file.filename}' uploaded successfully!", "success")
            url = f"static/assets/img/{file.filename}"  # creating address to server
            print(url)
            file.save(url)

        result = Product.query.filter_by(id=id).first()
        result.name = form.name.data
        result.category = form.category.data
        result.decription = form.decription.data
        result.price = form.price.data
        result.image_url = url
        result.quantity = form.quantity.data
        db.session.commit()

        return redirect(url_for("All_products"))

    return render_template("add.html",form=form)


# result_pending = Purchase.query.filter_by(status="pending").all()
@app.route("/dashboard", methods=['GET','POST'])
@login_required
@admin_only
def Admin_panel():
    form = Select_status()
    form_two = Select_status()
    if form.validate_on_submit():
        asked = form.select.data
        print(asked)
        result = Purchase.query.filter_by(status=asked).all()
        print(result)
        return render_template("dashboard.html", form=form,result=result,form_two=form_two)



    return render_template("dashboard.html", form=form,form_two=form_two)



@app.route("/user_page", methods=['GET','POST'])
@login_required
@admin_only
def User_page():
    id = request.args.get("id")
    print(id)
    user = User.query.filter_by(id=id).first()

    return render_template("user_page.html",user=user)


@app.route("/Change_status", methods=['GET','POST'])
@login_required
@admin_only
def Change_status():
    id = request.args.get("purchased_id")
    status = request.form.get('status')
    purchase_selected = Purchase.query.filter_by(id=id).first()
    print(id)
    print(status)
    print(purchase_selected)
    purchase_selected.status = status
    db.session.commit()
    return redirect(url_for("Admin_panel"))


@app.route("/profile", methods=['GET','POST'])
@login_required
def Profile():
    resultt = Purchase.query.filter_by(buyer_id=current_user.id).all()

    form = Edit_profile_form()
    if request.method == "GET":
        result = db.get_or_404(User,current_user.id)
        form.name.data = result.name
        form.email.data = result.email
        form.number.data = result.phone_number
        form.address.data = result.address


    if form.validate_on_submit():
        result = db.get_or_404(User,current_user.id)
        result.name = form.name.data
        result.email = form.email.data
        result.phone_number = form.number.data
        result.address = form.address.data

        db.session.commit()

        return redirect(url_for("Profile"))

    if current_user.is_authenticated:
        purchases = len(Purchase.query.filter_by(buyer_id=current_user.id,status="pending").all())
    else:
        purchases = 0

    return render_template("profile.html",form=form,purchases=purchases,resultt=resultt)

@app.route("/delete_product", methods=['GET','POST'])
@login_required
@admin_only
def Delete_product():
    id = request.args.get("id")
    result = db.get_or_404(Product, id)
    db.session.delete(result)
    db.session.commit()
    return redirect(url_for('All_products'))



@app.route("/log_out")
def log_out():
    logout_user()
    return redirect(url_for("Home"))


@app.route("/product", methods=["GET", "POST"])
def Product_page():
    id = request.args.get("id")
    result = db.get_or_404(Product,id)
    if current_user.is_authenticated:
        purchases = len(Purchase.query.filter_by(buyer_id=current_user.id,status="pending").all())
    else:
        purchases = 0

    return render_template("product_page.html",prdc=result,current_user=current_user,purchases=purchases)

@app.route("/add_to_card")
def Add_to_card():
    if current_user.is_authenticated:
        id = request.args.get("id")
        purchase_amount = Purchase.query.filter_by(product_id=id,buyer_id=current_user.id).first()
        if purchase_amount:

            purchase_amount.quantity += 1
            db.session.commit()
            return redirect(url_for('Purhcase_page'))


        else:
            new_purchase = Purchase(

                buyer_id=current_user.id,  # Use current_user for the logged-in user
                product_id=id,  # Use the fetched product
                status='pending',
                quantity=1
            )
            db.session.add(new_purchase)
            db.session.commit()


            return redirect(url_for("Home"))

    else:
        return redirect(url_for("Login"))

@app.route("/minus_from_card")
def Minus_from_card():
    id = request.args.get("id")
    purchase_amount = Purchase.query.filter_by(product_id=id, buyer_id=current_user.id).first()
    if purchase_amount.quantity > 1:
        purchase_amount.quantity -= 1
        db.session.commit()
    elif purchase_amount.quantity == 1:
        db.session.delete(purchase_amount)
        db.session.commit()

    return redirect(url_for('Purhcase_page'))

@app.route("/purhcase_page")
def Purhcase_page():
    pending_purchases = Purchase.query.filter_by(buyer_id=current_user.id, status='pending').all()

    # calculating total price
    total_amount = 0
    for single in pending_purchases:
        price = single.quantity * single.thing.price
        total_amount += price

    if len(pending_purchases) == 0:
        pending_purchases = 0

    # amount of added to cart to show in header
    if current_user.is_authenticated:
        purchases = len(Purchase.query.filter_by(buyer_id=current_user.id,status="pending").all())
    else:
        purchases = 0

    return render_template("purchase_page.html", products=pending_purchases, purchases=purchases,total_amount=total_amount)



@app.route("/delete_purchase", methods=['GET','POST'])
def Delete_purhcase():
    id = request.args.get("id")
    print(id)
    result = Purchase.query.filter_by(product_id=id).all()
    for rsl in result:
        db.session.delete(rsl)
    db.session.commit()
    return redirect(url_for('Purhcase_page'))



"""________________________________________________________________Stripe__________________________________________________________________________________"""
api_key = os.getenv("api_key")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
stripe.api_key = api_key


@app.route('/success')
def success():
    return "Payment successful! Thank you for your purchase."


@app.route('/create_checkout_session', methods=['POST'])
@login_required
def create_checkout_session():

    user_cart = Purchase.query.filter_by(buyer_id=current_user.id, status="pending").all()


    line_items = []
    for item in user_cart:
        product = Product.query.filter_by(id=item.product_id).first()
        if product:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                        'description': product.decription,
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': item.quantity,
            })


    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('success', _external=True),
            cancel_url=url_for('Purhcase_page', _external=True),
            metadata={
                "user_id": current_user.id
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        print("faild")
        return redirect(url_for('Purhcase_page'))






@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:

        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError as e:

        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:

        return "Invalid signature", 400


    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        user_id = session.get("metadata", {}).get("user_id")
        if user_id:
            purchases = Purchase.query.filter_by(buyer_id=user_id, status="pending").all()
            if purchases:
                for purchase in purchases:
                    purchase.status = "paid"
                db.session.commit()
                print(f"Payment completed for user`s id: {user_id} and purchases updated.")
            else:
                print("couldnt done this")

        print("Payment successful for session:", session)

    return "Success", 200


if __name__ == "__main__":
    app.run(debug=True,port=9786)

from flask import render_template, abort
from models import Order, Category
from flask_login import current_user, login_required
from flask import redirect, url_for, request, flash
from flask_login import login_user, logout_user
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from forms import MessageForm
from forms import WishlistForm
from models import Product, WishlistItem, db
from models import User, ChatMessage



@app.route('/')
def index():
    from models import Product, Category
    featured_products = Product.query.filter_by(featured=True).limit(6).all()
    categories = Category.query.all()
    return render_template('index.html', featured_products=featured_products, categories=categories)


@app.route('/products')
def products():
    from models import Product, Category
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)

    query = Product.query
    if category_id:
        query = query.filter_by(category_id=category_id)

    products = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.all()

    return render_template('products.html', products=products, categories=categories, selected_category=category_id)



@app.route('/product/<int:id>')
def product_detail(id):
    from models import Product
    from forms import AddToCartForm, WishlistForm

    product = Product.query.get_or_404(id)
    related_products = Product.query.filter_by(category_id=product.category_id).filter(Product.id != id).limit(4).all()

    form = AddToCartForm()
    wishlist_form = WishlistForm()

    return render_template(
        'product_detail.html',
        product=product,
        related_products=related_products,
        form=form,  # ✅ ეს იყო cart_form შეცდომით
        wishlist_form=wishlist_form,
        current_user_wishlist=current_user.wishlist if current_user.is_authenticated else []
    )



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    from models import Contact
    from forms import ContactForm
    form = ContactForm()
    if form.validate_on_submit():
        contact_msg = Contact(
            name=form.name.data,
            email=form.email.data,
            message=form.message.data
        )
        db.session.add(contact_msg)
        db.session.commit()
        flash('თქვენი შეტყობინება წარმატებით გაიგზავნა!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import User
    from forms import LoginForm
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('არასწორი მომხმარებლის სახელი ან პაროლი!', 'danger')
    return render_template('auth/login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    from models import User
    from forms import RegisterForm
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('ამ მომხმარებლის სახელით უკვე რეგისტრირებულია მომხმარებელი!', 'danger')
            return render_template('auth/register.html', form=form)

        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('ამ ელ-ფოსტით უკვე რეგისტრირებულია მომხმარებელი!', 'danger')
            return render_template('auth/register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('რეგისტრაცია წარმატებით დასრულდა!', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    from models import User
    from forms import ResetPasswordForm

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('ამ ელფოსტით არ მოიძებნა მომხმარებელი.', 'danger')
            return redirect(url_for('reset_password'))

        # შეცვლა პაროლის
        user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('პაროლი წარმატებით შეიცვალა!', 'success')
        return redirect(url_for('login'))

    return render_template('auth/reset_password.html', form=form)



# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    from models import Product, Category, User, Contact
    from sqlalchemy import func
    from datetime import datetime, timedelta

    if not current_user.is_admin:
        abort(403)

    # Counts
    products_count = Product.query.count()
    categories_count = Category.query.count()
    users_count = User.query.count()
    messages_count = Contact.query.count()

    # Recent content
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    recent_messages = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    recent_categories = Category.query.order_by(Category.id.desc()).limit(5).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()

    # 👇 User registration stats (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=6)
    user_stats = (
        db.session.query(func.date(User.created_at), func.count(User.id))
        .filter(User.created_at >= seven_days_ago)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )

    registration_dates = [(seven_days_ago + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    registration_counts = [0 for _ in range(7)]
    for date_str, count in user_stats:
        if date_str in registration_dates:
            index = registration_dates.index(date_str)
            registration_counts[index] = count

    return render_template('admin/dashboard.html',
                           products_count=products_count,
                           categories_count=categories_count,
                           users_count=users_count,
                           messages_count=messages_count,
                           recent_products=recent_products,
                           recent_messages=recent_messages,
                           recent_categories=recent_categories,
                           orders=orders,
                           registration_dates=registration_dates,
                           registration_counts=registration_counts)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    from models import Product
    from forms import ProductForm
    if not current_user.is_admin:
        abort(403)

    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=form.image_url.data,
            category_id=form.category_id.data,
            in_stock=form.in_stock.data,
            featured=form.featured.data
        )
        db.session.add(product)
        db.session.commit()
        flash('პროდუქტი წარმატებით დაემატა!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_product.html', form=form)


@app.route('/admin/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    from models import Category
    from forms import CategoryForm
    if not current_user.is_admin:
        abort(403)

    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('კატეგორია წარმატებით დაემატა!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_category.html', form=form)

@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_product(id):
    from models import Product
    if not current_user.is_admin:
        abort(403)

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('პროდუქტი წარმატებით წაიშალა!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    from models import Product, Category
    from forms import ProductForm

    if not current_user.is_admin:
        abort(403)

    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)

    # ვუწერთ კატეგორიების სია ფორმაში
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        flash('პროდუქტი წარმატებით განახლდა!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_product.html', form=form, product=product)














@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    form = MessageForm()
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        abort(404, description="Admin user not found")

    if form.validate_on_submit():
        new_message = ChatMessage(
            sender_id=current_user.id,
            recipient_id=admin.id,
            message=form.message.data
        )
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('chat'))

    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == admin.id)) |
        ((ChatMessage.sender_id == admin.id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp.asc()).all()



    return render_template('chat.html', form=form, messages=messages)


@app.route('/admin/support/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_support(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)
    form = MessageForm()

    if form.validate_on_submit():
        new_message = ChatMessage(
            sender_id=current_user.id,
            recipient_id=user.id,
            message=form.message.data
        )
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('admin_support', user_id=user.id))

    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == user.id)) |
        ((ChatMessage.sender_id == user.id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp.asc()).all()



    return render_template('admin/admin_support.html', form=form, messages=messages, user=user)


@app.route('/admin/chat_users')
@login_required
def chat_users():
    if not current_user.is_admin:
        abort(403)

    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/chat_users.html', users=users)



@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    from models import Product, CartItem
    product = Product.query.get_or_404(product_id)

    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if existing:
        existing.quantity += 1
    else:
        new_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=1)
        db.session.add(new_item)

    db.session.commit()
    flash('პროდუქტი დაემატა კალათაში.', 'success')
    return redirect(url_for('product_detail', id=product.id))




@app.route('/cart')
@login_required
def cart():
    from models import CartItem
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    csrf_token = generate_csrf()
    return render_template('cart.html', cart_items=cart_items, total_price=total_price, csrf_token=csrf_token)


@app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    from models import CartItem
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('პროდუქტი წაიშალა კალათიდან.', 'success')
    return redirect(url_for('cart'))

@app.route("/account")
@login_required
def account_settings():
    return render_template("account.html", user=current_user)

@app.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    existing = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash(f"{product.name} ამოღებულია სურვილების სიიდან.", "info")
    else:
        item = WishlistItem(user_id=current_user.id, product_id=product.id)
        db.session.add(item)
        db.session.commit()
        flash(f"{product.name} დაემატა სურვილების სიაში.", "success")

    return redirect(request.referrer or url_for('index'))





@app.route('/wishlist')
@login_required
def wishlist():
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    wishlist_form = WishlistForm()  # <-- აქ შეგიძლია შექმნა ფორმა
    return render_template("wishlist.html", items=items, wishlist_form=wishlist_form)


@app.context_processor
def inject_counts():
    cart_count = 0
    wishlist_count = 0
    if current_user.is_authenticated:
        cart_count = sum(item.quantity for item in current_user.cart_items)
        wishlist_count = len(current_user.wishlist)
    return dict(cart_count=cart_count, wishlist_count=wishlist_count)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    from models import CartItem, Order, OrderItem
    from forms import CheckoutForm

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("კალათა ცარიელია.", "warning")
        return redirect(url_for('cart'))

    form = CheckoutForm()
    if form.validate_on_submit():
        order = Order(
            user_id=current_user.id,
            full_name=form.full_name.data,
            address=form.address.data,
            phone=form.phone.data
        )
        db.session.add(order)
        db.session.commit()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.session.add(order_item)

        # გაწმინდეთ კალათა
        for item in cart_items:
            db.session.delete(item)

        db.session.commit()
        flash("შეკვეთა წარმატებით შესრულდა!", "success")
        return redirect(url_for("index"))

    return render_template("checkout.html", form=form, cart_items=cart_items)

@app.route('/my-orders')
@login_required
def user_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('user_orders.html', orders=orders)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        abort(403)
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/admin_orders.html', orders=orders)

@app.route('/admin/update-order-status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        abort(403)

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    order.status = new_status
    db.session.commit()
    flash('შეკვეთის სტატუსი განახლდა!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route("/admin/order/<int:order_id>")
@login_required
def order_detail(order_id):
    if not current_user.is_admin:
        abort(403)

    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", order=order)



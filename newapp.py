from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import io
import os
import logging
from werkzeug.utils import secure_filename  # Import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
logging.basicConfig(level=logging.DEBUG)  # Enable debugging logs

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'V@r$ha#123'
app.config['MYSQL_DB'] = 'login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# Navigation or landing page
@app.route('/')
def navigatereg():
    return render_template('navigatereg.html')

@app.route('/sellerreg', methods=['GET', 'POST'])
def sellerreg():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'business_name' in request.form:
        business_name = request.form['business_name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if account exists
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM sellers WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email or not business_name:
            msg = 'Please fill out all the fields!'
        else:
            # Account doesn't exist, proceed to insert into 'sellers' table
            cursor.execute('INSERT INTO sellers (business_name, username, password, email) VALUES (%s, %s, %s, %s)',
                           (business_name, username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered as a seller!'
            return redirect(url_for('sellerlog'))  # Redirect to seller login
    elif request.method == 'POST':
        msg = 'Please fill out all the fields!'
    return render_template('sellerregister.html', msg=msg)


@app.route('/sellerlog', methods=['GET', 'POST'])
def sellerlog():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM sellers WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['seller_loggedin'] = True
            session['seller_id'] = account['seller_id']
            session['seller_username'] = account['username']
            msg = 'Logged in successfully as seller!'
            return redirect(url_for('sellerhome'))  # Corrected redirect
        else:
            msg = 'Incorrect username or password!'
    return render_template('seller_login.html', msg=msg)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only letters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    return render_template('register.html', msg=msg)


# Upload product image
logging.basicConfig(level=logging.DEBUG)


@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if 'seller_loggedin' not in session:
        return redirect(url_for('sellerlog'))

    if request.method == 'POST':
        logging.debug("Handling POST request for /upload")
        if 'product_image' not in request.files:
            logging.error("No file part in the request")
            return 'No file part'
        file = request.files['product_image']
        if file.filename == '':
            logging.warning("No selected file")
            return 'No selected file'

        if file:
            try:
                img_data = file.read()
                product_name = request.form.get('product_name')
                product_price = request.form.get('product_price')
                product_description = request.form.get('product_description')
                product_quantity = request.form.get('product_quantity')
                user_provided_name = request.form.get('image_name')
                category = request.form.get('category')  # Get the category from the form
                seller_id = session['seller_id']  # Get the seller ID from the session

                logging.debug(
                    f"Product details: Name={product_name}, Price={product_price}, Filename={user_provided_name}, Size={len(img_data)}, Category={category}, Seller ID={seller_id}")

                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO product (seller_id, product_name, product_price, product_description, product_image_name, product_image_data, product_quantity, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (seller_id, product_name, product_price, product_description, user_provided_name, img_data,
                      product_quantity, category))
                mysql.connection.commit()
                cur.close()
                logging.info(
                    f"Product '{product_name}' uploaded successfully to category '{category}' by seller {seller_id}")
                return redirect(url_for('sellerdashboard'))
            except Exception as e:
                logging.error(f"Error uploading product: {e}")
                return f'Error uploading product: {e}'

    logging.debug("Handling GET request for /upload")
    return render_template('upload.html')  # Make sure your upload.html has a field to select the category


@app.route('/home')
def home():
    logging.debug("Handling request for /")
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, product_name, product_price, product_image_name, category FROM product")
        products = cur.fetchall()
        cur.close()
        logging.debug(f"Fetched {len(products)} products for homepage")
        return render_template('index.html', products=products, active_tab='home',
                               username=session.get('username'))
    except Exception as e:
        logging.error(f"Error fetching products for homepage: {e}")
        return f'Error fetching products: {e}'


@app.route('/image/<int:product_id>')
def get_image(product_id):
    logging.debug(f"Handling request for /image/{product_id}")
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT product_image_name, product_image_data FROM product WHERE id = %s", (product_id,))
        product_data = cur.fetchone()
        cur.close()
        if product_data:
            image_name = product_data['product_image_name']
            image_data = product_data['product_image_data']
            if image_data:
                return send_file(io.BytesIO(image_data), mimetype=f"image/{image_name.rsplit('.', 1)[-1].lower()}")
            else:
                return "No image data found", 404
        else:
            logging.warning(f"Image not found for product ID: {product_id}")
            abort(404)
    except Exception as e:
        logging.error(f"Error fetching image for product {product_id}: {e}")
        abort(500)


# Serve product image for the homepage (redundant with /image/<id>, but kept for template consistency if used elsewhere)
@app.route('/product_image/<int:product_id>')
def get_product_image(product_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT product_image_name, product_image_data FROM product WHERE id = %s", (product_id,))
        product_data = cur.fetchone()
        cur.close()
        if product_data:
            ext = product_data['product_image_name'].rsplit('.', 1)[-1].lower()
            return send_file(io.BytesIO(product_data['product_image_data']), mimetype=f'image/{ext}')
        return 'Image not found', 404
    except Exception as e:
        return f'Error fetching product image: {e}', 500


# Product details page
@app.route('/product/<int:product_id>')
def product_details(product_id):
    logging.debug(f"Handling request for /product/{product_id}")
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM product WHERE id = %s", (product_id,))
        product = cur.fetchone()
        cur.close()

        if product:
            return render_template('productdetails.html', product=product)
        else:
            logging.warning(f"Product with ID {product_id} not found")
            abort(404)
    except Exception as e:
        logging.error(f"Error fetching product details: {e}")
        abort(500)


# --- ADD THESE NEW ROUTES AND FUNCTIONS ---
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Logic to add the product to the user's shopping cart
    # You'll likely need to work with session data or a database for the cart
    logging.info(f"Product ID {product_id} added to cart")
    flash(f"Product ID {product_id} added to cart!", 'info')
    # For now, let's just redirect back to the product details page
    return redirect(url_for('product_details', product_id=product_id))


@app.route('/buy_now/<int:product_id>', methods=['GET', 'POST'])
def buy_now(product_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT product_name, product_price FROM product WHERE id = %s", (product_id,))
        product = cur.fetchone()
        cur.close()

        if product:
            return render_template('place_order.html', product_name=product['product_name'],
                                   total_price=product['product_price'], quantity=1, product_id=product_id)
        else:
            flash('Product not found!', 'danger')
            return redirect(url_for('home'))
    except Exception as e:
        logging.error(f"Error fetching product details for buy now: {e}")
        flash('Error fetching product details!', 'danger')
        return redirect(url_for('home'))


@app.route('/process_order', methods=['POST'])
def process_order():
    """
    Handles the submission of the order form and stores the order in the database.
    """
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        payment_method = request.form['payment_method']  # Get payment method
        product_name = request.form['productName']
        quantity = int(request.form['productQuantity'])
        total_price = float(request.form['total_price'])
        product_id = request.form.get('product_id')  # Get product_id from the form

        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("""
                INSERT INTO orders (name, email, phone, shipping_address, product_name, quantity, total_price, order_date, payment_method, product_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
            """, (name, email, phone, address, product_name, quantity, total_price, payment_method, product_id))  # Include payment_method and product_id
            mysql.connection.commit()
            order_id = cur.lastrowid  # Get the ID of the newly inserted order
            cur.close()
            flash('Order placed successfully!', 'success')
            logging.info(f"Order placed for {quantity} x {product_name} by {name} ({email})")
            return redirect(url_for('receipt', order_id=order_id))  # Redirect to receipt with order ID
        except Exception as e:
            logging.error(f"Error processing order: {e}")
            flash('Error processing your order. Please try again.', 'danger')
            # Redirect to the buy_now page, passing the product_id
            return redirect(url_for('buy_now', product_id=product_id))

    # This part of the code will be reached if the request method is not POST.
    # It's good to have it, but it might not be the most common scenario.
    return redirect(url_for('home'))  # Consider redirecting to a more appropriate page



@app.route('/receipt/<int:order_id>')
def receipt(order_id):
    """
    Renders the receipt page (receipt.html) and passes the order data from the database.
    """
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, name, email, phone, shipping_address, product_name, quantity, total_price, order_date, payment_method, product_id
            FROM orders
            WHERE id = %s
        """, (order_id,))
        order = cur.fetchone()  # Fetch the order details as a dictionary
        cur.close()

        if order:
            return render_template('receipt.html', order=order)
        else:
            flash('Order not found.', 'danger')
            return redirect(url_for('home'))  # Redirect to home or order history
    except Exception as e:
        logging.error(f"Error fetching order details: {e}")
        flash('Error fetching order details. Please try again.', 'danger')
        return redirect(url_for('home'))

# Recipe submission
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


@app.route('/category/<category_name>')
def category_products(category_name):
    logging.debug(f"Fetching products for category: {category_name}")
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT id, product_name, product_price, product_image_name, category FROM product WHERE category = %s",
                    (category_name,))
        products = cur.fetchall()
        cur.close()
        logging.debug(f"Found {len(products)} in category: {category_name}")
        return render_template('category_page.html', products=products, category_name=category_name)
    except Exception as e:
        logging.error(f"Error fetching products for category {category_name}: {e}")
        return f'Error fetching products for category {category_name}: {e}'


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/submit_recipe', methods=['GET', 'POST'])
def submit_recipe():
    if request.method == 'POST':
        title = request.form['recipe-title']
        description = request.form['description']
        ingredients = request.form.getlist('ingredient')
        instructions = request.form.getlist('instruction')
        image = request.files['file-upload']

        # Initialize a variable to track validation success
        valid = True

        if not title:
            flash('Recipe title is required.', 'danger')
            valid = False
        if not description:
            flash('Description is required.', 'danger')
            valid = False
        if not ingredients or not any(ingredients):
            flash('At least one ingredient is required.', 'danger')
            valid = False
        if not instructions or not any(instructions):
            flash('At least one instruction step is required.', 'danger')
            valid = False
        if not image:
            flash('Recipe image is required.', 'danger')
            valid = False
        elif not allowed_file(image.filename):  # Combine file check
            flash('Invalid file type. Allowed types are: png, jpg, jpeg, gif.', 'warning')
            valid = False

        if valid:  # Check the validation flag
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image.save(filepath)

            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO recipes (title, description, ingredients, instructions, image_path)
                    VALUES (%s, %s, %s, %s, %s)
                """, (title, description, ','.join(ingredients), '\n'.join(instructions), filepath))
                mysql.connection.commit()
                cur.close()
                flash('Recipe submitted successfully!', 'success')
                return redirect(url_for('recipe_submitted_success'))
            except Exception as e:
                flash(f'Error submitting recipe: {str(e)}', 'danger')
                return redirect(url_for('submit_recipe'))

    return render_template('submit_recipe_form.html')


@app.route('/recipes')
def recipe_list():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, title, description, image_path FROM recipes")  # Adjust columns
        recipes = cur.fetchall()
        cur.close()
        return render_template('recipe_list.html', recipes=recipes)
    except Exception as e:
        return f"Error fetching recipes: {str(e)}"


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


@app.route('/sellerhome')
def sellerhome():
    if 'seller_loggedin' in session:
        return render_template('seller_home.html', seller_username=session['seller_username'])  # Updated template name
    return redirect(url_for('sellerlog'))


@app.route('/sellerdashboard')
def sellerdashboard():
    if 'seller_loggedin' in session:
        seller_id = session['seller_id']
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Fetch products uploaded by the logged-in seller
            cur.execute("SELECT * FROM product WHERE seller_id = %s", (seller_id,))
            products = cur.fetchall()
            cur.close()

            # Basic out-of-stock check (can be enhanced)
            out_of_stock_notifications = []
            for product in products:
                if product['product_quantity'] == 0:
                    out_of_stock_notifications.append(product['product_name'])

            return render_template('seller_dashboard.html',
                                   seller_username=session['seller_username'],
                                   products=products,
                                   out_of_stock_notifications=out_of_stock_notifications)

        except Exception as e:
            logging.error(f"Error fetching seller dashboard data: {e}")
            return f"Error fetching dashboard data: {e}"

    return redirect(url_for('sellerlog'))  # Redirect to login if not logged in

# Admin registration
@app.route('/adminreg', methods=['GET', 'POST'])
def adminreg():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        admin_code = request.form.get('admin_code', '')  # Optional admin registration code for security

        # Check if account exists
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        # You might want to add validation for an admin code
        # admin_code != 'your_secret_code' could be added as a condition below

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out all the fields!'
        else:
            # Account doesn't exist, insert into 'admins' table
            cursor.execute('INSERT INTO accounts (username, password, email) VALUES (%s, %s, %s)',
                           (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered as an admin!'
            return redirect(url_for('adminlog'))  # Redirect to admin login

    elif request.method == 'POST':
        msg = 'Please fill out all the fields!'

    return render_template('admin_register.html', msg=msg)


# Admin login
@app.route('/adminlog', methods=['GET', 'POST'])
def adminlog():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()

        if account:
            session['admin_loggedin'] = True
            session['id'] = account['id']
            session['admin_username'] = account['username']
            msg = 'Logged in successfully as admin!'
            return redirect(url_for('admin_dashboard'))
        else:
            msg = 'Incorrect username or password!'

    return render_template('admin_login.html', msg=msg)


# Admin logout
@app.route('/admin_logout')
def admin_logout():
    # Remove admin session data
    session.pop('admin_loggedin', None)
    session.pop('id', None)
    session.pop('admin_username', None)
    return redirect(url_for('adminlog'))


# Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_loggedin' not in session:
        return redirect(url_for('adminlog'))

    # Get stats for the dashboard
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get total users
    cursor.execute('SELECT COUNT(*) as total_users FROM accounts')
    total_users = cursor.fetchone()['total_users']

    # Get total sellers
    cursor.execute('SELECT COUNT(*) as total_sellers FROM sellers')
    total_sellers = cursor.fetchone()['total_sellers']

    # Get total products
    cursor.execute('SELECT COUNT(*) as total_products FROM product')
    total_products = cursor.fetchone()['total_products']

    # Get total orders
    cursor.execute('SELECT COUNT(*) as total_orders FROM orders')
    total_orders = cursor.fetchone()['total_orders']

    # Get total sales amount
    cursor.execute('SELECT SUM(total_price) as total_sales FROM orders')
    result = cursor.fetchone()
    total_sales = result['total_sales'] if result['total_sales'] else 0

    # Get recent orders
    cursor.execute('SELECT * FROM orders ORDER BY order_date DESC LIMIT 5')
    recent_orders = cursor.fetchall()

    # Get low stock products (less than 5 in quantity)
    cursor.execute('SELECT * FROM product WHERE product_quantity < 5')
    low_stock_products = cursor.fetchall()

    cursor.close()

    return render_template('admin_dashboard.html',
                           username=session['admin_username'],
                           total_users=total_users,
                           total_sellers=total_sellers,
                           total_products=total_products,
                           total_orders=total_orders,
                           total_sales=total_sales,
                           recent_orders=recent_orders,
                           low_stock_products=low_stock_products)


# Admin - View all users
@app.route('/admin/users')
def admin_users():
    if 'admin_loggedin' not in session:
        return redirect(url_for('adminlog'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts')
    users = cursor.fetchall()
    cursor.close()

    return render_template('admin_users.html', users=users)


# Admin - View all sellers
@app.route('/admin/sellers')
def admin_sellers():
    if 'admin_loggedin' not in session:
        return redirect(url_for('adminlog'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM sellers')
    sellers = cursor.fetchall()
    cursor.close()

    return render_template('admin_sellers.html', sellers=sellers)


# Admin - View all products
@app.route('/admin/products')
def admin_products():
    if 'admin_loggedin' not in session:
        return redirect(url_for('adminlog'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT p.*, s.business_name
        FROM product p
        JOIN sellers s ON p.seller_id = s.seller_id
    ''')
    products = cursor.fetchall()
    cursor.close()

    return render_template('admin_products.html', products=products)


# Admin - View all orders
@app.route('/admin/orders')
def admin_orders():
    if 'admin_loggedin' not in session:
        return redirect(url_for('adminlog'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders ORDER BY order_date DESC')
    orders = cursor.fetchall()
    cursor.close()

    return render_template('admin_orders.html', orders=orders)


# Admin - Edit Order Tracking
@app.route('/admin/order/edit_tracking/<int:order_id>', methods=['GET', 'POST'])
def admin_edit_order_tracking(order_id):
    if 'admin_loggedin' not in session:
        return redirect(url_for('adminlog'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('admin_orders'))

    if request.method == 'POST':
        tracking_number = request.form['tracking_number']
        shipping_carrier = request.form['shipping_carrier']
        order_status = request.form['order_status']

        cursor.execute('''
            UPDATE orders
            SET tracking_number = %s,
                shipping_carrier = %s,
                order_status = %s
            WHERE id = %s
        ''', (tracking_number, shipping_carrier, order_status, order_id))
        mysql.connection.commit()
        flash('Order tracking details updated successfully!', 'success')
        return redirect(url_for('admin_orders'))

    cursor.close()
    return render_template('admin_edit_tracking.html', order=order)

# User - View Order History with Tracking
@app.route('/order_history')
def order_history():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders WHERE email = (SELECT email FROM accounts WHERE id = %s) ORDER BY order_date DESC', (user_id,))
    orders = cursor.fetchall()
    cursor.close()
    return render_template('order_history.html', orders=orders)

# User - Track Specific Order
@app.route('/track_order/<int:order_id>')
def track_order(order_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders WHERE id = %s AND email = (SELECT email FROM accounts WHERE id = %s)', (order_id, session['id']))
    order = cursor.fetchone()
    cursor.close()

    if order:
        return render_template('track_order.html', order=order)
    else:
        flash('Order not found or does not belong to your account.', 'danger')
        return redirect(url_for('order_history'))

# ... (your route for order confirmation, assuming it passes the 'order' object to the template) ...
@app.route('/order/confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders WHERE id = %s AND email = (SELECT email FROM accounts WHERE id = %s)', (order_id, session['id']))
    order = cursor.fetchone()
    cursor.close()
    if order:
        return render_template('order_confirmation.html', order=order)
    else:
        flash('Order not found.', 'danger')
        return redirect(url_for('order_history'))

# ... (rest of your code - you'll need to ensure 'seller_id' is stored when a seller uploads a product) ...
@app.route('/textiles')
def textiles():
    return render_template('textiles.html')


@app.route('/jewellery')
def jewellery():
    return render_template('jewellery.html')


@app.route('/pottery')
def pottery():
    return render_template('pottery.html')


@app.route('/culture')
def culture():
    return render_template('culture.html')


@app.route('/natural_oils')
def natural_oils():
    return render_template('natural_oils.html')


@app.route('/herbal_soaps')
def herbal_soaps():
    return render_template('herbal_soaps.html')


@app.route('/ayurvedic_products')
def ayurvedic_products():
    return render_template('ayurvedic_products.html')


@app.route('/dishes')
def dishes():
    return render_template('dishes.html')


if __name__ == '__main__':
    app.run(debug=True)

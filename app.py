from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import io
import os
import logging

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
def nav():
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
            cursor.execute('INSERT INTO sellers (business_name, username, password, email) VALUES (%s, %s, %s, %s)', (business_name, username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered as a seller!'
            return redirect(url_for('sellerlog')) # Redirect to seller login
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
            session['seller_id'] = account['id']
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
                category = request.form.get('category') # Get the category from the form
                seller_id = session['seller_id'] # Get the seller ID from the session

                logging.debug(f"Product details: Name={product_name}, Price={product_price}, Filename={user_provided_name}, Size={len(img_data)}, Category={category}, Seller ID={seller_id}")

                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO product (seller_id, product_name, product_price, product_description, product_image_name, product_image_data, product_quantity, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (seller_id, product_name, product_price, product_description, user_provided_name, img_data, product_quantity, category))
                mysql.connection.commit()
                cur.close()
                logging.info(f"Product '{product_name}' uploaded successfully to category '{category}' by seller {seller_id}")
                return redirect(url_for('sellerdashboard'))
            except Exception as e:
                logging.error(f"Error uploading product: {e}")
                return f'Error uploading product: {e}'

    logging.debug("Handling GET request for /upload")
    return render_template('upload.html') # Make sure your upload.html has a field to select the category

@app.route('/home')
def home():
    logging.debug("Handling request for /")
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, product_name, product_price, product_image_name, category FROM product")
        products = cur.fetchall()
        cur.close()
        logging.debug(f"Fetched {len(products)} products for homepage")
        return render_template('index.html', products=products, active_tab='home', username=session.get('username'))
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
            return render_template('place_order.html', product_name=product['product_name'], total_price=product['product_price'], quantity=1) # Assuming quantity is 1 for buy now
        else:
            flash('Product not found!', 'danger')
            return redirect(url_for('home'))
    except Exception as e:
        logging.error(f"Error fetching product details for buy now: {e}")
        flash('Error fetching product details!', 'danger')
        return redirect(url_for('home'))

@app.route('/process_order', methods=['POST'])
def process_order():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        product_name = request.form['productName']
        quantity = int(request.form['productQuantity'])
        total_price = float(request.form['total_price'])

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO orders (name, email, phone, shipping_address, product_name, quantity, total_price, order_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (name, email, phone, address, product_name, quantity, total_price))
            mysql.connection.commit()
            cur.close()
            flash('Order placed successfully!', 'success')
            logging.info(f"Order placed for {quantity} x {product_name} by {name} ({email})")
            return redirect(url_for('home')) # Redirect to a confirmation page or home
        except Exception as e:
            logging.error(f"Error processing order: {e}")
            flash('Error processing your order. Please try again.', 'danger')
            return redirect(url_for('buy_now', product_id=1)) # Redirect back to buy now or an error page
    return redirect(url_for('home')) # Redirect if accessed directly
# --- END OF NEW ROUTES AND FUNCTIONS ---

# Recipe submission
@app.route('/submit_recipe', methods=['GET', 'POST'])
def submit_recipe():
    if request.method == 'POST':
        recipe_title = request.form.get('recipe_title')  # Use the correct name
        description = request.form.get('description')
        ingredients = request.form.getlist('ingredients')
        instructions = request.form.getlist('instructions')
        recipe_image = request.files.get('recipe_image')

        if recipe_title and description and ingredients and instructions and recipe_image:
            try:
                img_data = recipe_image.read()
                img_filename = recipe_image.filename

                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO recipes (title, description, ingredients, instructions, image_name, image_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (recipe_title, description, ','.join(ingredients), '\n'.join(instructions), img_filename, img_data))
                mysql.connection.commit()
                cur.close()
                logging.info(f"Recipe '{recipe_title}' submitted successfully")
                return "Recipe submitted successfully!"
            except Exception as e:
                logging.error(f"Error submitting recipe: {e}")
                return f"Error submitting recipe: {e}"
        else:
            return "Please fill in all the required fields."
    return render_template('submit_recipe_form.html')

@app.route('/recipe_image/<int:recipe_id>')
def get_recipe_image(recipe_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT image_name, image_data FROM recipes WHERE id = %s", (recipe_id,))
        recipe = cur.fetchone()
        cur.close()
        if recipe and recipe['image_data']:
            return send_file(io.BytesIO(recipe['image_data']), mimetype='image/*') # Adjust mimetype as needed
        return 'Recipe image not found', 404
    except Exception as e:
        return f'Error fetching recipe image: {e}', 500

@app.route('/recipes')
def view_recipes():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT id, title, description FROM recipes")
        recipes = cur.fetchall()
        cur.close()
        return render_template('recipes.html', recipes=recipes) # Create a recipes.html to display the list
    except Exception as e:
        return f'Error fetching recipes: {e}', 500

@app.route('/recipe/<int:recipe_id>')
def view_recipe_details(recipe_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM recipes WHERE id = %s", (recipe_id,))
        recipe = cur.fetchone()
        cur.close()
        if recipe:
            recipe['ingredients'] = recipe['ingredients'].split(',')
            recipe['instructions'] = recipe['instructions'].split('\n')
            return render_template('recipe_details.html', recipe=recipe) # Create recipe_details.html
        return 'Recipe not found', 404
    except Exception as e:
        return f'Error fetching recipe details: {e}', 500

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
        cur.execute("SELECT id, product_name, product_price, product_image_name, category FROM product WHERE category = %s", (category_name,))
        products = cur.fetchall()
        cur.close()
        logging.debug(f"Found {len(products)} in category: {category_name}")
        return render_template('category_page.html', products=products, category_name=category_name)
    except Exception as e:
        logging.error(f"Error fetching products for category {category_name}: {e}")
        return f'Error fetching products for category {category_name}: {e}'

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/sellerhome')
def sellerhome():
    if 'seller_loggedin' in session:
        return render_template('seller_home.html', seller_username=session['seller_username']) # Updated template name
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

    return redirect(url_for('sellerlog')) # Redirect to login if not logged in

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
    
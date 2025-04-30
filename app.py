from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from flask_mysqldb import MySQL
import bcrypt
import re

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session and CSRF

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'V@r$ha#123'
app.config['MYSQL_DB'] = 'desi'

# Initialize MySQL
mysql = MySQL(app)

# Custom Validators
def only_letters(form, field):
    if not re.match("^[A-Za-z ]+$", field.data):
        raise ValidationError("Name must contain only letters and spaces.")

def email_ends_with_com(form, field):
    if not field.data.endswith('.com'):
        raise ValidationError("Email must end with '.com'.")

# Register Form
class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50), only_letters])
    email = StringField('Email', validators=[DataRequired(), Email(), email_ends_with_com])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), email_ends_with_com])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Routes

@app.route('/')
def index():
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    success = None
    error = None

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "Email is already registered."
        else:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
            mysql.connection.commit()
            cursor.close()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))

        cursor.close()
    
    return render_template('register.html', form=form, success=success, error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    success = None

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cursor.fetchone()
        cursor.close()

        if user:
            stored_password = user[3]  # Assuming password is in column index 3
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                session['user'] = user[1]  # Assuming user[1] is the name
                success = "Login successful!"
                return redirect(url_for('dashboard'))  # Or render with success if you want to stay
            else:
                error = "Incorrect password."
        else:
            error = "Email ID does not exist!"

    return render_template("login.html", form=form, error=error, success=success)


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Run app
if __name__ == '__main__':
    app.run(debug=True)

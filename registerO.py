#register code without flask-wtf
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Register</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #ecf0f3;
            margin: 0;
            padding: 0;
        }

        .container {
            max-width: 420px;
            margin: 60px auto;
            background-color: #ffffff;
            padding: 40px 30px;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
        }

        h2 {
            text-align: center;
            margin-bottom: 25px;
            color: #2c3e50;
            font-size: 26px;
        }

        .form-group {
            margin-bottom: 18px;
        }

        .form-label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: #34495e;
        }

        .form-control {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid #ccd1d9;
            border-radius: 6px;
            font-size: 15px;
            transition: border-color 0.3s;
        }

        .form-control:focus {
            border-color: #3498db;
            outline: none;
        }

        .alert {
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
            text-align: center;
        }

        .alert-error {
            background-color: #ffe6e6;
            color: #c0392b;
            border: 1px solid #e74c3c;
        }

        .alert-success {
            background-color: #eaffea;
            color: #27ae60;
            border: 1px solid #2ecc71;
        }

        button {
            width: 100%;
            padding: 12px;
            background-color: #3498db;
            color: white;
            font-size: 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        button:hover {
            background-color: #2980b9;
        }

        p {
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
        }

        a {
            color: #3498db;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Register</h2>

        {% if error %}
            <div class="alert alert-error">{{ error }}</div>
        {% endif %}

        {% if success %}
            <div class="alert alert-success">{{ success }}</div>
        {% endif %}

        <form method="POST">
            <div class="form-group">
                <label class="form-label" for="name">Name</label>
                <input type="text" class="form-control" id="name" name="name" required>
            </div>

            <div class="form-group">
                <label class="form-label" for="email">Email</label>
                <input type="email" class="form-control" id="email" name="email" required>
            </div>

            <div class="form-group">
                <label class="form-label" for="password">Password</label>
                <input type="password" class="form-control" id="password" name="password" required minlength="6">
            </div>

            <button type="submit">Register</button>
        </form>

        <p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
    </div>
</body>
</html>

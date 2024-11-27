import sys
from pathlib import Path
# Add parent directory to path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

import os
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from tinydb import TinyDB, Query
import plotly.express as px
import yaml
from functools import wraps

from src.app.app_utils import predict_song
from src.app.reco_monitoring import merge_reco_data, cosine_similarity_trend


import re
from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, session

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

#céation d'une instance limiter
limiter = Limiter(get_remote_address, app=app)

# Configurer Flask-Limiter pour suivre l'adresse IP de chaque requête
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]  # Limites globales par IP
)

# Initialize TinyDB
db_path = "users/users.json"
db = TinyDB(db_path)
user_table = db.table("users")

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'homepage'
login_manager.login_message = "Please login or register to access this page."

# Load parameters from a yaml file
params_path = "src/models_module_def/params.yaml"

def load_params():   
    with open(params_path, 'r') as file:
        params = yaml.safe_load(file)
    return params

# Update parameters and write to a YAML file
def update_params(new_params):
    with open(params_path, 'w') as file:
        yaml.safe_dump(new_params, file)

# User model for FLask-Login
class Users(UserMixin):
    def __init__(self, user_id, username, password, role='user'):
        self.id = user_id
        self.username = username
        self.password = password
        self.role = role

@login_manager.user_loader
def loader_user(user_id):
    user_entry = user_table.get(doc_id=int(user_id))
    if user_entry:
        return Users(user_entry.doc_id, user_entry['username'], user_entry['password'], user_entry.get('role', 'user'))
    return None

# Admin-only route decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.role == 'admin':
            return f(*args, **kwargs)
        else:
            flash("You do not have permission to access this page.")
            return render_template("homepage.html")
    return decorated_function

# --- Security: Password Validation ---
# Ensures the password meets security requirements (length, upper case, digits, special chars)
def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*()]", password):
        return False
    return True

@app.route('/register', methods=["GET", "POST"])
def register():
    # If the user made a POST request, create a new user
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Password validation check
        if not is_valid_password(password):
            flash("Password must be at least 8 characters long, include an uppercase letter, a digit, and a special character.")
            return redirect(url_for("register"))
        
        hashed_password = generate_password_hash(password)

        # Check if user already exists
        if user_table.search(Query().username == username):
            flash("Username already taken. Please choose another.")
            return redirect(url_for("register"))
        
        # Add the new user to TinyDB
        user_table.insert({"username": username, "password": hashed_password, "role": "user"})

        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("sign_up.html")

@app.route("/", methods=["GET", "POST"])
# --- Security: Rate Limiting for Login Attempts ---
# Limits the number of login attempts to prevent brute-force attacks
@limiter.limit("5 per 15 minutes", error_message="Too many login attempts. Please try again in 15 minutes.")
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user_entry = user_table.get(Query().username == username)
        if user_entry and check_password_hash(user_entry['password'], password):
            user = Users(user_entry.doc_id, user_entry['username'], user_entry['password'], user_entry.get('role', 'user'))
            remember = True if request.form.get("remember") else False
            login_user(user, remember=remember)
            return redirect(url_for("welcome"))
        else:
            flash("Login failed. Check your username and password.")

    return render_template("homepage.html")


@app.route("/logout")
# @login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/welcome")
@login_required
def welcome():
    # render the home page
    return render_template('welcome.html')


@app.route("/about")
def about():
    # render the about page
    return render_template('about.html')


@app.route('/recommend', methods=['POST'])
@login_required # Ensures user is logged in
@limiter.limit("5 per minute", error_message="Too many recommendations requested. Please wait a moment and try again.")  # Custom error message
def recommend():
    # requesting the playist reference (URL of Index) form the HTML form
    playlist_ref = request.form['URL']
    # Number of recommendations songs to provide
    number_of_recs = int(request.form['number-of-recs'])

    playlist_name, predicted_genre, recommended_songs, score = predict_song(playlist_ref)

    return render_template(
        'results.html',
        songs=recommended_songs[:number_of_recs],
        playlist_name=playlist_name,
        playlist_genre=predicted_genre,
        score=round(score, 3)
    )


@app.route('/update_params', methods=['GET', 'POST'])
@login_required
@admin_required
def update_parameters():
    params = load_params()
    if request.method == 'POST':
        # Update GradientBoostingClassifier params
        params['GradientBoostingClassifier']['learning_rate'] = float(request.form['learning_rate'])
        params['GradientBoostingClassifier']['max_depth'] = int(request.form['max_depth'])
        params['GradientBoostingClassifier']['n_estimators'] = int(request.form['n_estimators'])

        # Update GaussianMixture params
        params['GaussianMixture']['n_components'] = list(map(int, request.form['n_components'].split(',')))
        params['GaussianMixture']['covariance_type'] = request.form['covariance_type']
        params['GaussianMixture']['random_state'] = int(request.form['random_state'])

        # Save updated params to params.yaml
        update_params(params)

        flash('Parameters updated successfully!', 'success')
        return redirect(url_for('update_parameters'))

    return render_template('update_params.html', params=params)


@app.route("/train", methods=['GET','POST'])
@login_required
@admin_required
def retrain():
    if request.method == 'POST':
        try:
            # Commande pour exécuter le script Python
            os.system('python main.py')
            # dvc repro
            flash(
                'Re-training was successful- Results at: https://dagshub.com/micheldpd24/mlflow_tracking .' , 
                'success'
            )
        except Exception as e:
            flash(f"Erreur lors du déclenchement de l'entraînement : {e}", 'danger')

    return render_template('train_form.html')


@app.route("/monitoring")
@login_required
@admin_required
def show_cosine_similarity():
    graph_html = cosine_similarity_trend()
    return render_template("monitoring.html", graph_html=graph_html)


@app.route('/delete_user', methods=["GET", "POST"])
@login_required
@admin_required
def delete_user():
    # If it's a POST request (form submission)
    if request.method == "POST":
        # Get the username from the form input
        username_to_delete = request.form.get("username")

        # Search for the user in the TinyDB
        user_entry = user_table.get(Query().username == username_to_delete)

        if user_entry:
            # Delete the user from the database
            user_table.remove(Query().username == username_to_delete)
            flash(f"User '{username_to_delete}' has been successfully deleted.", "success")
        else:
            flash(f"User '{username_to_delete}' not found.", "danger")

        # Redirect after handling POST request
        return redirect(url_for('welcome'))  # Redirect to a page (e.g., welcome)

    # If it's a GET request, render the delete user form
    return render_template('delete_user_form.html')


if __name__ == '__main__':

    # Session cookie configuration
    app.config['SESSION_COOKIE_SECURE'] = True  # Ensures cookies are sent only over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevents JavaScript access to cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Restricts cross-site usage of cookies

    # Session expiration configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = 30 * 60  # Sets session lifetime to 30 minutes


    app.run(host="0.0.0.0", debug=True)
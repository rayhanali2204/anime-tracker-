from flask import Flask, request,  render_template, redirect, url_for, flash
import requests  #REQUEST IS A DATA COMING INTO THE FLAKS APP AND REQUESTS IS HTTP REQUESTS OUT TO THE INTERNET.
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import secrets
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
import resend
import os
from resend.exceptions import ResendError
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from flask_wtf import CSRFProtect


load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

ANIME_API_URL  = "https://api.tenrai.org/v1/anime"
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Anime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    image = db.Column(db.String(300))
    mal_id = db.Column(db.Integer, nullable=False)
    

    airing_status = db.Column(db.String(50))
    content_rating = db.Column(db.String(50))
    total_episodes = db.Column(db.Integer)

    watch_status = db.Column(db.String(30), nullable=False, default="Plan to Watch")
    episodes_watched = db.Column(db.Integer, nullable=False, default=0)
    user_rating = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expires = db.Column(db.DateTime(timezone=True))

class AnimeCatalog(db.Model):
    __tablename__ = "anime_catalog"

    id = db.Column(db.Integer, primary_key=True)

    mal_id = db.Column(db.Integer, unique=True, nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    title_english = db.Column(db.String(250))

    image_url = db.Column(db.String(500))

    type = db.Column(db.String(50))
    episodes = db.Column(db.Integer)
    status = db.Column(db.String(100))

    score = db.Column(db.Float)
    rank = db.Column(db.Integer)
    popularity = db.Column(db.Integer)

    year = db.Column(db.Integer)
    season = db.Column(db.String(20))

    genres = db.Column(db.JSON)
    studio = db.Column(db.String(200))

class PipelineRun(db.Model):
    __tablename__ = "pipeline_runs"

    id = db.Column(db.Integer, primary_key=True)

    started_at = db.Column(db.DateTime, nullable=False)
    finished_at = db.Column(db.DateTime)

    records_extracted = db.Column(db.Integer, default=0)
    records_transformed = db.Column(db.Integer, default=0)
    records_valid = db.Column(db.Integer, default=0)
    records_rejected = db.Column(db.Integer, default=0)

    records_inserted = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)

    status = db.Column(db.String(30), nullable=False)
    runtime_ms = db.Column(db.Float)
    error_message = db.Column(db.Text)


with app.app_context():
    db.create_all()



def send_password_reset_email(user_email, reset_link):
    params: resend.Emails.SendParams = {
        "from": "Anime Tracker <onboarding@resend.dev>",
        "to": [user_email],
        "subject": "Reset your Anime Tracker password",
        "html": f"""
            <h2>Reset your password</h2>

            <p>
                We received a request to reset your Anime Tracker password.
            </p>

            <p>
                <a href="{reset_link}">Reset your password</a>
            </p>

            <p>This link expires in one hour.</p>

            <p>
                If you didn't request this, you can safely ignore this email.
            </p>
        """
    }

    return resend.Emails.send(params)





@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":

        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with that email already exists", "danger")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        new_user = User(email=email, name=name, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Account created successfully", "success")
        return redirect(url_for("login"))
    
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash("Incorrect email or password", "danger")
                return redirect(url_for("login"))
            
        return render_template("login.html")

@app.route("/forgot-password", methods=["GET" , "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            user.reset_token  = secrets.token_urlsafe(32)
            user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
            db.session.commit()

            reset_link = url_for(
                "reset_password",
                token=user.reset_token,
                _external=True
            )

            try:
                send_password_reset_email(user.email, reset_link)
            except ResendError as error:
                print("ResendError:", error)

                flash("We couldnt resend the reset email, please try again later.", "danger")
                return redirect(url_for("forgot_password"))

        flash("if an account exists with that email, a reset link has been set.",
            "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if (not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(UTC)):
        flash("That password-reset link is invalid or has expired.", "danger")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("The passwords do not match.", "danger")
            return render_template("reset_password.html", token=token)
        
        user.password = generate_password_hash(password)

        user.reset_token = None
        user.reset_token_expires = None

        db.session.commit()

        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("login"))
    
    return render_template("reset_password.html", token=token)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("login"))
    





@app.route('/')
@login_required
def home():
    
    
    return render_template("home.html")


@app.route("/top-anime")
@login_required
def top_anime():

    top_anime = (
        AnimeCatalog.query
        .order_by(AnimeCatalog.rank.asc())
        .limit(100)
        .all()
    )

    last_run = (
        PipelineRun.query
        .filter_by(status="SUCCESS")
        .order_by(PipelineRun.finished_at.desc())
        .first()
    )

    return render_template(
        "top_anime.html",
        top_anime=top_anime,
        last_run=last_run
    )


@app.route("/anime", methods=["GET", "POST"])
@login_required
def anime_page():
    print(" HIT /anime METHOD =", request.method)
    anime_list = Anime.query.filter_by(user_id=current_user.id).order_by(Anime.id.asc()).all()
    return render_template("anime.html", anime_list=anime_list)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        anime_name = request.form.get("anime_name", "").strip()

        if len(anime_name) < 3:
            flash("Search must have at least 3 characters", "danger")
            return redirect(url_for("search"))

        try:
            response = requests.get(
                ANIME_API_URL,
                params={"q": anime_name},
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as error:
            print("SEARCH ERROR:", error)
            flash("Something went wrong, please try again later", "danger")
            return redirect(url_for("search"))

        except ValueError as error:
            print("JSON ERROR:", error)
            flash("The anime service returned invalid data", "danger")
            return redirect(url_for("search"))

        results = data.get("data", [])

        return render_template(
            "search.html",
            results=results
        )

    return render_template(
        "search.html",
        results=[]
    )


@app.route("/add_anime", methods=["POST"])
@login_required
def add_anime():
    name = request.form.get("name")
    image = request.form.get("image")
    mal_id = request.form.get("mal_id", type=int)
    airing_status = request.form.get("airing_status")
    content_rating = request.form.get("content_rating")
    total_episodes = request.form.get("total_episodes", type=int)

    if mal_id is None:
        flash("Could not add the anime", "danger")
        return redirect(url_for("anime_page"))


    existing_anime = Anime.query.filter_by(
        mal_id=mal_id,
        user_id=current_user.id
    ).first()

    if existing_anime:
        flash("That anime is already in your list.", "warning")
        return redirect(url_for("anime_page"))

   

    new_anime = Anime(
        mal_id=mal_id,
        name=name,
        image=image,
        airing_status=airing_status,
        content_rating=content_rating,
        total_episodes=total_episodes,
        watch_status="Plan to Watch",
        episodes_watched=0,
        user_id = current_user.id
        )

    db.session.add(new_anime)
    db.session.commit()

    return redirect(url_for("anime_page"))

@app.route("/delete_anime/<int:anime_id>", methods=["POST"])
@login_required
def delete_anime(anime_id):
    anime = Anime.query.filter_by(id=anime_id, user_id=current_user.id).first_or_404()

    db.session.delete(anime)
    db.session.commit()

    flash("Anime removed from your list", "success")
    return redirect(url_for("anime_page"))


@app.route("/anime/<int:anime_id>/edit", methods=["POST"])
@login_required
def edit_anime(anime_id):
    anime = Anime.query.filter_by(id=anime_id, user_id=current_user.id).first_or_404()

    watch_status = request.form.get("watch_status")
    episodes_watched = request.form.get("episodes_watched", type=int)
    user_rating = request.form.get("user_rating", type=int)

    allowed_statuses = {"Plan to Watch",  "Watching","Completed","On Hold","Dropped","Re-Watching"}

    if watch_status not in allowed_statuses:
        flash("Invalid watch status", "danger")
        return redirect(url_for("anime_page"))
    
    if episodes_watched is None or episodes_watched < 0:
        flash("Episodes watched cannot be negative.", "danger")
        return redirect(url_for("anime_page"))

    if (anime.total_episodes is not None and episodes_watched > anime.total_episodes):
        flash("Episodes watched cannot exceed the total epsiode count.", "danger")
        return redirect(url_for("anime_page"))
    
    if user_rating is not None and not 1<=  user_rating <= 10:
        flash("User rating must be a number between 1 and 10", "danger")
        return redirect(url_for("anime_page"))
    
    anime.watch_status = watch_status
    anime.episodes_watched = episodes_watched
    anime.user_rating = user_rating

    db.session.commit()

    flash("Anime update successfully.", "success")
    return redirect(url_for("anime_page"))


    


    
    


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "False") == "True")
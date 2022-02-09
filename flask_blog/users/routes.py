from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_blog import bcrypt, db
from flask_blog.models import Post, User
from flask_blog.users.forms import (
    LoginForm,
    RegistrationForm,
    RequestResetForm,
    ResetPasswordForm,
    UpdateAccount,
)
from flask_blog.users.utils import save_profile_image, send_reset_email
from flask_login import current_user, login_required, login_user, logout_user

users = Blueprint("users", __name__)


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Your account has been created. You may now log in!", "success")
        return redirect(url_for("users.login"))
    return render_template("register.html", title="Register", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")

            return redirect(next_page) if next_page else redirect(url_for("main.home"))

        else:
            flash("Login Unsuccessful. Please check username and password")

    return render_template("login.html", title="Login", form=form)


@users.route("/logout")
def logout():

    logout_user()

    return redirect(url_for("main.home"))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():

    form = UpdateAccount()

    if form.validate_on_submit():
        if form.image.data:
            image_file = save_profile_image(form.image.data)
            current_user.image_file = image_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated", "success")
        return redirect(url_for("users.account"))

    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for("static", filename=f"profile_pics/{current_user.image_file}")

    return render_template(
        "account.html", title="Account", image_file=image_file, form=form
    )


@users.route("/user/<string:username>")
def user_posts(username):

    page = request.args.get("page", 1, type=int)

    user = User.query.filter_by(username=username).first_or_404(
        description=f"There is no data with {username}"
    )
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)

    return render_template("user_posts.html", user=user, posts=posts)


@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RequestResetForm()
    if form.is_submitted():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("Password reset instructions sent", "info")
        return redirect(url_for("users.login"))

    return render_template("reset_request.html", title="Reset Password", form=form)


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):

    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    user = User.verify_reset_token(token)  # from URL
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("users.reset_request"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.password = hashed_password
        db.session.commit()
        flash(f"Your password has been updated. You may now log in!", "success")
        return redirect(url_for("users.login"))

    return render_template("reset_token.html", title="Reset Password", form=form)

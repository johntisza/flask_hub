import pathlib
import secrets

from flask import url_for, current_app
from flask_blog import mail
from flask_blog.models import User
from flask_mail import Message
from PIL import Image


def save_profile_image(form_image):
    random_hex = secrets.token_hex(8)
    image_ext = pathlib.PurePath(form_image.filename).suffix

    new_image_name = f"{random_hex}{image_ext}"

    image_path = str(
        pathlib.PurePath(current_app.root_path).joinpath("static/profile_pics", new_image_name)
    )

    output_size = (125, 125)
    i = Image.open(form_image)
    i.thumbnail(output_size)

    i.save(image_path)

    return new_image_name


def send_reset_email(user: User):

    token = user.get_reset_token()

    msg = Message(
        subject="Your password reset request",
        sender="noreply@demo.com",
        recipients=[user.email],
    )

    msg.body = f"""To reset your password, visit the following link
    {url_for('users.reset_token', token=token, _external=True)}"""

    mail.send(msg)

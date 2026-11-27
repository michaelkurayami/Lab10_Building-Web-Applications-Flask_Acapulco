
import os
import uuid

from werkzeug.utils import secure_filename
from flask import request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegisterForm, LoginForm
from models import db, User, Student

import os

app = Flask(__name__, instance_relative_config=True)

app.config['SECRET_KEY'] = 'my-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(
            email=form.email.data
        ).first()

        if existing_user:
            flash("Email already registered.")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(form.password.data)

        user = User(
            email=form.email.data,
            password=hashed_pw,
            role='viewer'
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful!")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Logged in successfully.")
            return redirect(url_for('students'))

        else:
            flash("Invalid email or password.")

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('home'))

@app.route('/students')
@login_required
def students():

    student_list = Student.query.order_by(
        Student.full_name
    ).all()

    return render_template(
        'students.html',
        students=student_list
    )


@app.route('/add-student', methods=['POST'])
@login_required
def add_student():

    if current_user.role != 'admin':
        flash("Access denied. Admin privileges required.")
        return redirect(url_for('students'))

    name = request.form['name']
    email = request.form['email']

    existing_student = Student.query.filter_by(email=email).first()

    if existing_student:
        flash("Student email already exists.")
        return redirect(url_for('students'))

    student = Student(full_name=name, email=email)

    db.session.add(student)
    db.session.commit()

    flash("Student added successfully!")
    return redirect(url_for('students'))


@app.route('/delete-student/<int:id>')
@login_required
def delete_student(id):

    if current_user.role != 'admin':
        flash("Access denied. Admin privileges required.")
        return redirect(url_for('students'))

    student = Student.query.get_or_404(id)

    db.session.delete(student)
    db.session.commit()

    flash("Student deleted successfully!")
    return redirect(url_for('students'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    upload_folder = os.path.join(
        app.static_folder, 'uploads'
    )

    os.makedirs(upload_folder, exist_ok=True)

    if request.method == 'POST':

        display_name = request.form.get('display_name', '').strip()

        if not display_name:
            flash("Display name cannot be empty.")
            return redirect(url_for('profile'))

        if len(display_name) > 100:
            flash("Display name must not exceed 100 characters.")
            return redirect(url_for('profile'))

        current_user.display_name = display_name

        image = request.files.get('profile_image')

        if image and image.filename:

            filename = secure_filename(image.filename)
            extension = os.path.splitext(filename)[1].lower()

            allowed_extensions = ['.jpg', '.jpeg', '.png']
            allowed_mime_types = ['image/jpeg', 'image/png']

            if extension not in allowed_extensions:
                flash("Only JPG, JPEG, and PNG images are allowed.")
                return redirect(url_for('profile'))

            if image.mimetype not in allowed_mime_types:
                flash("Invalid image file type.")
                return redirect(url_for('profile'))

            image.seek(0)
            signature = image.read(8)
            image.seek(0)

            is_png = (
                extension == '.png'
                and signature.startswith(b'\x89PNG\r\n\x1a\n')
            )

            is_jpeg = (
                extension in ['.jpg', '.jpeg']
                and signature.startswith(b'\xff\xd8\xff')
            )

            if not (is_png or is_jpeg):
                flash("The uploaded file is not a valid matching image.")
                return redirect(url_for('profile'))

            unique_filename = f"{uuid.uuid4().hex}{extension}"

            image.save(
                os.path.join(upload_folder, unique_filename)
            )

            current_user.image_filename = unique_filename

        db.session.commit()

        flash("Profile updated successfully!")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':

    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        db.create_all()

    app.run(debug=True)

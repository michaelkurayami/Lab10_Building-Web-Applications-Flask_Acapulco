
import sys
from app import app
from models import db, User

with app.app_context():

    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Enter the registered email: ")

    user = User.query.filter_by(email=email).first()

    if user:
        user.role = 'admin'
        db.session.commit()
        print(f"{email} is now an ADMIN!")
    else:
        print(f"ERROR: No account found with email {email}")
from flask_sqlalchemy import SQLAlchemy
import bcrypt

from Entity.db_init import db


class UserCredentials(db.Model):
    __tablename__ = 'user_credentials'

    username = db.Column(db.String(50), primary_key=True)
    emp_id = db.Column(db.String(20), db.ForeignKey('users.emp_id'), unique=True)
    ##password_hash = db.Column(db.String(60), nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    def set_password(self, password):
        self.password_hash = password

    def verify_password(self, password):
        return password == self.password_hash
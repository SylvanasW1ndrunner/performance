from flask_sqlalchemy import SQLAlchemy

from Entity.db_init import db


class Department(db.Model):
    __tablename__ = 'department'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    avgattendance = db.Column(db.Float, nullable=False)
    @classmethod
    def all_department(cls):
        return cls.query.all()


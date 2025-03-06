from flask_sqlalchemy import SQLAlchemy

from Entity.db_init import db


class User(db.Model):
    __tablename__ = 'users'

    emp_id = db.Column(db.String(20), primary_key=True)
    emp_name = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    isSA = db.Column(db.Boolean, nullable=False)
    isRJ = db.Column(db.Boolean, nullable=False)
    isPJ = db.Column(db.Boolean, nullable=False)
    immediate_leader = db.Column(db.String(20), db.ForeignKey('users.emp_id'))
    directJudgeid = db.Column(db.String(50))
    top_leader = db.Column(db.String(20), db.ForeignKey('users.emp_id'))
    ProductGroup = db.Column(db.String(100))
    ismanage = db.Column(db.Boolean, nullable=True)
    departmentid = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    productid = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    def to_dict(self):
        return {
            "emp_id": self.emp_id,
            "emp_name": self.emp_name,
            "position": self.position,
            "department": self.department,
            "isSA": self.isSA,
            "isRJ": self.isRJ,
            "isPJ": self.isPJ,
            "directJudgeid": self.directJudgeid,
            "ProductGroup": self.ProductGroup,
            "immediate_leader": self.immediate_leader,
            "top_leader": self.top_leader,
            "ismanage": self.ismanage,
            "productid": self.productid,
            "departmentid": self.departmentid
        }
    @classmethod
    def find_by_judge_id(cls, identify):
        return User.query.filter(
            (User.directJudgeid == identify) | (User.immediate_leader == identify)
        ).all()

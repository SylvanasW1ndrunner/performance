from flask_sqlalchemy import SQLAlchemy
from Entity.db_init import db

class AssessmentItems(db.Model):
    __tablename__ = 'assessmentitems'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.JSON, nullable=False)
    score_rule = db.Column(db.JSON, nullable=False)
    version = db.Column(db.String(50), nullable=False)
    ddl = db.Column(db.DateTime, nullable=False)
    forcedistrubution = db.Column(db.Integer, nullable=False)
    punishment = db.Column(db.JSON, nullable=False)
    department = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    @classmethod
    def create(cls, description, score_rule, version,ddl,forcedistrubution,punishment,departmentid):
        new_item = cls(
            description=description,
            score_rule=score_rule,
            version=version,
            ddl=ddl,
            forcedistrubution=forcedistrubution,
            punishment=punishment,
            department=departmentid
        )
        db.session.add(new_item)  # 添加到会话
        db.session.commit()  # 提交事务
        return new_item
    @classmethod
    def search_by_version( cls, version):
        return cls.query.filter_by(version=version).all()
    @classmethod
    def delete(cls,version,departmentid):
        try:
            AssessmentItems.query.filter_by(version=version,department=departmentid).delete()
            db.session.commit()
            return "Success"
        except Exception as e:
            print("error:", e)
            return "Error"


    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'score_rule': self.score_rule,
            'version': self.version,
            'ddl': self.ddl,
            'forcedistrubution': self.forcedistrubution,
            'punishment': self.punishment,
            'department': self.department,
        }
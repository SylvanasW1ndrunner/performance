from flask_sqlalchemy import SQLAlchemy
from Entity.db_init import db

class Assessments(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(20), db.ForeignKey('users.emp_id'), nullable=False)
    assessmentid = db.Column(db.Integer, db.ForeignKey('assessmentitems.id'), nullable=False)
    totalrank = db.Column(db.String(2), nullable=False)
    totalscore = db.Column(db.Integer, nullable=False)
    checktime = db.Column(db.DateTime, nullable=False)
    ProfessionDes = db.Column(db.JSON, nullable=False)
    gendes = db.Column(db.JSON, nullable=False)
    extrabonus = db.Column(db.JSON, nullable=False)
    abiscore = db.Column(db.Integer, nullable=False)
    productscore = db.Column(db.Integer, nullable=False)
    def update(self, emp_id, assessmentid, totalrank, totalscore, checktime, ProfessionDes, gendes, extrabonus, abiscore, productscore):
        """更新评估记录的各个字段"""
        self.emp_id = emp_id
        self.assessmentid = assessmentid
        self.totalrank = totalrank
        self.totalscore = totalscore
        self.checktime = checktime
        self.ProfessionDes = ProfessionDes
        self.gendes = gendes
        self.extrabonus = extrabonus
        self.abiscore = abiscore
        self.productscore = productscore
        db.session.commit()
        return self
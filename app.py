from os import access

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager

import config
from Entity.User import User
from Entity.auth import UserCredentials
from Entity.db_init import db

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
app.config.from_object(config.Config)

db.init_app(app)
jwt = JWTManager(app)


##username:string
##password:string
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "无效的请求"}), 400
    user = UserCredentials.query.filter_by(username=data['username']).first()
    if not user or not user.verify_password(data['password']):
        return jsonify({"error": "用户名或密码错误"}), 401
    user_info = User.query.get(user.emp_id)
    if not user_info:
        return jsonify({"error": "用户不存在"}), 404
    access_token = create_access_token(identity={
        "emp_id": user_info.emp_id,
        "role": user_info.user_role
    })
    return jsonify({"access_token": access_token, "user_info": user_info.to_dict()}), 200


@app.route('/api/change_password', methods=['POST'])
def change_password():
    data = request.get_json()
    if not data or 'username' not in data or 'old_password' not in data or 'new_password' not in data:
        return jsonify({"error": "无效的请求"}), 400

    username = data['username']
    old_password = data['old_password']
    new_password = data['new_password']

    # 查询用户凭证
    user = UserCredentials.query.filter_by(username=username).first()
    if not user or not user.verify_password(old_password):
        return jsonify({"error": "用户名或旧密码错误"}), 401

    # 更新密码
    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "密码修改成功"}), 200


@app.route('/change_password')
def change_password_page():
    return render_template("change_password.html")

@app.route('/Gentable')
def Gentable():
    return render_template('Gentable.html')  # 考核表发布页面

@app.route('/score-evaluation')
def score_evaluation():
    return render_template('score_evaluation.html')  # 绩效评分页面

@app.route('/member-management')
def member_management():
    return render_template('member_management.html')

@app.route('/data-import')
def data_import():
    return render_template('data_import.html')

@app.route('/permission-settings')
def permission_settings():
    return render_template('permission_settings.html')

@app.route('/performance-query')
def performance_query():
    return render_template('performance_query.html')


@app.route('/api/change_password', methods=['POST'])
def handle_change_password():
    data = request.get_json()
    if not data or 'username' not in data or 'old_password' not in data or 'new_password' not in data:
        return jsonify({"error": "无效的请求"}), 400

    username = data['username']
    old_password = data['old_password']
    new_password = data['new_password']

    # 查询用户凭证
    user = UserCredentials.query.filter_by(username=username).first()
    if not user or not user.verify_password(old_password):
        return jsonify({"error": "用户名或旧密码错误"}), 401

    # 更新密码
    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "密码修改成功"}), 200


@app.route('/')
def origin():  # put application's code here
    return render_template("login.html")


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)

import json
import traceback
from datetime import timedelta, datetime

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity, jwt_required, decode_token
from sqlalchemy import desc

import config
from Entity.User import User
from Entity.auth import UserCredentials
from Entity.assessmentitems import AssessmentItems
from Entity.db_init import db
from Entity.product import Product
from Entity.department import Department
from Entity.assessments import Assessments
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app,supports_credentials=True)
app.config.from_object(config.Config)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']  # 同时支持从 headers 和 cookies 中获取令牌
db.init_app(app)
jwt = JWTManager(app)


@app.route('/api/performance_detail', methods=['GET'])
@jwt_required()
def get_performance_detail():
    try:
        # 获取用户ID和绩效表ID
        user_id = request.args.get('userId', '')
        table_id = request.args.get('tableId', '')

        if not user_id or not table_id:
            return jsonify({"error": "缺少必要参数"}), 400

        # 查询绩效评估记录
        assessment = Assessments.query.filter_by(
            emp_id=user_id,
            assessmentid=table_id
        ).first()

        if not assessment:
            return jsonify({"error": "未找到绩效记录"}), 404

        # 计算职能评分和产品评分的权重
        # 假设职能评分权重为60%，产品评分权重为40%
        functional_weight = 0.6
        product_weight = 0.4

        # 构建响应数据
        response_data = {
            "functionalScore": float(assessment.abiscore),
            "functionalWeight": functional_weight,
            "productScore": float(assessment.productscore),
            "productWeight": product_weight,
            "totalScore": float(assessment.totalscore),
            "grade": assessment.totalrank,
            "comment": ""  # 默认为空，因为您提到评语不显示
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": "获取绩效详情失败"}), 500
@app.route('/api/user_performance_tables', methods=['GET'])
@jwt_required()
def get_user_performance_tables():
    try:
        # 获取用户ID
        user_id = request.args.get('userId', '')
        if not user_id:
            return jsonify({"error": "缺少用户ID参数"}), 400

        # 查询该用户的所有绩效评估记录
        assessments = Assessments.query.filter_by(emp_id=user_id).all()

        if not assessments:
            return jsonify([]), 200

        # 构建绩效表列表
        tables_data = []
        assessment_item_ids = set()  # 用于去重

        for assessment in assessments:
            # 避免重复的绩效表
            if assessment.assessmentid in assessment_item_ids:
                continue

            assessment_item_ids.add(assessment.assessmentid)

            # 查询绩效表详情
            assessment_item = AssessmentItems.query.filter_by(id=assessment.assessmentid).first()

            if assessment_item:
                tables_data.append({
                    "id": str(assessment.assessmentid),
                    "name": assessment_item.version,
                    "period": assessment_item.ddl.strftime("%Y-%m-%d") if assessment_item.ddl else "未指定",
                    "status": "已完成"
                })

        return jsonify(tables_data)

    except Exception as e:
        return jsonify({"error": "获取用户绩效表列表失败"}), 500
@app.route('/api/check_performance_permission', methods=['GET'])
@jwt_required()
def check_performance_permission():
    try:
        # 获取要查看绩效的用户ID
        user_id = request.args.get('userId', '')
        if not user_id:
            return jsonify({"error": "缺少用户ID参数"}), 400

        # 获取当前登录用户ID
        current_user_id = json.loads(get_jwt_identity())["userinfo"]["emp_id"]

        # 查询当前用户信息
        current_user = User.query.filter_by(emp_id=current_user_id).first()
        if not current_user:
            return jsonify({"error": "当前用户不存在"}), 404

        # 查询目标用户信息
        target_user = User.query.filter_by(emp_id=user_id).first()
        if not target_user:
            return jsonify({"error": "目标用户不存在"}), 404

        # 检查权限
        permission_level = 0
        has_permission = False
        message = "您没有权限查看该用户的绩效信息"

        # 1. 超级管理员可以查看所有人的绩效
        if current_user.isSA:
            permission_level = 1
            has_permission = True
            message = "您有权限查看该用户的绩效信息（超级管理员权限）"

        # 2. 直接领导可以查看下属的绩效
        elif current_user_id == target_user.immediate_leader:
            permission_level = 2
            has_permission = True
            message = "您有权限查看该用户的绩效信息（直接领导权限）"

        # 3. 产品线打分人可以查看其负责的用户的产品评分
        elif current_user_id == target_user.directJudgeid:
            permission_level = 3
            has_permission = True
            message = "您有权限查看该用户的产品线评分（产品线打分人权限）"

        return jsonify({
            "hasPermission": has_permission,
            "permissionLevel": permission_level,
            "message": message
        })

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "检查绩效查看权限失败"}), 500
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        # 获取分页和筛选参数
        page = request.args.get('page', 1, type=int)
        team_id = request.args.get('team', '')
        product_line_id = request.args.get('productLine', '')
        direct_leader_id = request.args.get('directLeader', '')
        name = request.args.get('name', '')
        employee_id = request.args.get('employeeId', '')

        # 每页显示的记录数
        per_page = 10

        # 构建查询
        query = User.query

        # 应用筛选条件
        if team_id:
            query = query.filter_by(departmentid=team_id)
        if product_line_id:
            query = query.filter_by(productid=product_line_id)
        if direct_leader_id:
            query = query.filter_by(immediate_leader=direct_leader_id)
        if name:
            query = query.filter(User.emp_name.like(f'%{name}%'))
        if employee_id:
            query = query.filter_by(emp_id=employee_id)

        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        total_pages = pagination.pages

        # 构建响应数据
        users_data = []
        for user in users:
            # 获取直接领导姓名
            direct_leader_name = None
            if user.immediate_leader:
                direct_leader = User.query.filter_by(emp_id=user.immediate_leader).first()
                if direct_leader:
                    direct_leader_name = direct_leader.emp_name

            # 获取产品线名称
            product_line_name = None
            if user.productid:
                product = Product.query.filter_by(id=user.productid).first()
                if product:
                    product_line_name = product.name

            # 获取团队名称
            team_name = None
            if user.departmentid:
                department = Department.query.filter_by(id=user.departmentid).first()
                if department:
                    team_name = department.name

            users_data.append({
                "id": user.emp_id,
                "name": user.emp_name,
                "employeeId": user.emp_id,
                "team": team_name or user.department,
                "productLine": product_line_name or user.ProductGroup,
                "position": user.position,
                "directLeader": direct_leader_name or "未指定"
            })

        return jsonify({
            "users": users_data,
            "totalPages": total_pages,
            "currentPage": page
        })

    except Exception as e:
        app.logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({"error": "获取用户列表失败"}), 500
@app.route('/api/leaders', methods=['GET'])
@jwt_required()
def get_leaders():
    try:
        # 查询所有isRJ为True的用户（即领导）
        leaders = User.query.filter_by(isRJ=True).all()

        # 如果没有找到领导
        if not leaders:
            return jsonify([]), 200

        # 构建响应数据
        leaders_data = []
        for leader in leaders:
            leaders_data.append({
                "id": leader.emp_id,
                "name": leader.emp_name
            })

        return jsonify(leaders_data)

    except Exception as e:
        return jsonify({"error": "获取领导列表失败"}), 500
@app.route('/api/product_lines', methods=['GET'])
@jwt_required()
def get_product_lines():
    try:
        # 查询所有产品线
        products = Product.query.all()
        print(products)
        # 如果没有找到产品线
        if not products:
            return jsonify([]), 200

        # 构建响应数据
        product_lines_data = []
        for product in products:
            product_lines_data.append({
                "id": str(product.id),  # 转换为字符串以符合API规范
                "name": product.name
            })

        return jsonify(product_lines_data)

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "获取产品线列表失败"}), 500
@app.route('/api/teams', methods=['GET'])
@jwt_required()
def get_teams():
    try:
        # 查询所有部门
        departments = Department.query.all()

        # 如果没有找到部门
        if not departments:
            return jsonify([]), 200

        # 构建响应数据
        teams_data = []
        for department in departments:
            teams_data.append({
                "id": str(department.id),  # 转换为字符串以符合API规范
                "name": department.name
            })

        return jsonify(teams_data)

    except Exception as e:
        return jsonify({"error": "获取团队列表失败"}), 500

@app.route('/api/current_user_info', methods=['GET'])
@jwt_required()
def get_current_user_info():
    try:
        # 从JWT令牌中获取当前用户ID
        current_user_id = json.loads(get_jwt_identity())["userinfo"]["emp_id"]


        # 查询用户信息
        user = User.query.filter_by(emp_id=current_user_id).first()

        if not user:
            return jsonify({"error": "用户不存在"}), 404

        # 查询用户的直接领导信息
        direct_leader_name = None
        if user.immediate_leader:
            direct_leader = User.query.filter_by(emp_id=user.immediate_leader).first()
            if direct_leader:
                direct_leader_name = direct_leader.emp_name

        # 查询用户最近的绩效评价
        recent_assessment = Assessments.query.filter_by(emp_id=current_user_id) \
            .order_by(desc(Assessments.checktime)) \
            .first()

        recent_performance = None
        if recent_assessment:
            recent_performance = recent_assessment.totalrank

        # 获取用户所在的部门和产品线信息
        department = user.department
        sub_team = ""  # 子团队信息，如果有的话

        # 如果department字段包含子团队信息，可以进行拆分
        if " - " in department:
            parts = department.split(" - ", 1)
            department = parts[0]
            sub_team = parts[1]

        # 构建响应数据
        response_data = {
            "name": user.emp_name,
            "employeeId": user.emp_id,
            "team": department,
            "subTeam": sub_team,
            "position": user.position,
            "directLeader": direct_leader_name or "未指定",
            "productLine": user.ProductGroup or "未指定",
            "recentPerformance": recent_performance
        }

        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({"error": "获取用户信息失败"}), 500


@app.route('/submit_score', methods=['POST'])
@jwt_required()
def submit_score():
    try:
        # 获取当前用户信息
        current_user_info = json.loads(get_jwt_identity())
        current_user = current_user_info["userinfo"]
        print("1")
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "未提供数据"}), 400

        emp_id = data.get('emp_id')
        assessmentid = data.get('table_id')

        if not emp_id or not assessmentid:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400

        # 获取被评估员工信息
        employee = User.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({"success": False, "message": "被评估员工不存在"}), 404

        # 权限验证
        is_sa = current_user.get('isSA', False)
        is_rj = current_user.get('isRJ', False)
        is_pj = current_user.get('isPJ', False)

        # 检查是否有权限提交评分
        has_professional_general_permission = is_sa or (is_rj and employee.immediate_leader == current_user.get('emp_id'))
        has_product_permission = is_sa or (is_pj and employee.directJudgeid == current_user.get('emp_id'))

        # 获取提交的评分数据
        professional_data = data.get('professional')
        general_data = data.get('general')
        product_score = data.get('product')
        details = data.get('details', {})
        extra_bonus = data.get('extraBonus', {"score": 0, "reason": ""})

        # 验证权限与提交数据的匹配
        if professional_data is not None and not has_professional_general_permission:
            return jsonify({"success": False, "message": "无权提交专业职能评分"}), 403

        if general_data is not None and not has_professional_general_permission:
            return jsonify({"success": False, "message": "无权提交通用职能评分"}), 403

        if product_score is not None and not has_product_permission:
            return jsonify({"success": False, "message": "无权提交产品表现评分"}), 403

        if extra_bonus.get('score') is not None and not is_sa:
            return jsonify({"success": False, "message": "无权提交额外加减分"}), 403

        # 计算能力分数 (专业职能 + 通用职能)
        abi_score = 0

        # 处理专业职能分数
        if professional_data and professional_data.get('items'):
            for item in professional_data['items']:
                abi_score += item.get('score', 0)

        # 处理通用职能分数
        if general_data:
            for item in general_data:
                abi_score += item.get('score', 0)

        # 处理产品表现分数
        product_score_value = product_score if product_score is not None else 0

        # 处理额外加减分
        extra_bonus_value = extra_bonus.get('score', 0) if extra_bonus else 0

        # 计算总分
        total_score = abi_score + product_score_value + (extra_bonus_value or 0)

        # 根据总分确定等级
        total_rank = "C"  # 默认等级
        if total_score >= 90:
            total_rank = "A"
        elif total_score >= 80:
            total_rank = "B+"
        elif total_score >= 70:
            total_rank = "B"

        # 检查是否已存在评估记录
        existing_assessment = Assessments.query.filter_by(
            emp_id=emp_id,
            assessmentid=assessmentid
        ).first()

        checktime = datetime.now()

        if existing_assessment:
            # 更新现有记录，只更新提交的部分
            if professional_data is not None and has_professional_general_permission:
                existing_assessment.ProfessionDes = details.get('professional', existing_assessment.ProfessionDes)

            if general_data is not None and has_professional_general_permission:
                existing_assessment.gendes = details.get('general', existing_assessment.gendes)

            if product_score is not None and has_product_permission:
                existing_assessment.productscore = product_score_value

            if is_sa and extra_bonus.get('score') is not None:
                existing_assessment.extrabonus = extra_bonus

            # 重新计算总分和等级
            current_abi_score = existing_assessment.abiscore
            current_product_score = existing_assessment.productscore
            current_extra_bonus = existing_assessment.extrabonus.get('score', 0) if existing_assessment.extrabonus else 0

            # 如果提交了新的专业职能或通用职能评分，更新能力分数
            if (professional_data is not None or general_data is not None) and has_professional_general_permission:
                existing_assessment.abiscore = abi_score
                current_abi_score = abi_score

            # 重新计算总分
            new_total_score = current_abi_score + current_product_score + current_extra_bonus
            existing_assessment.totalscore = new_total_score

            # 更新等级
            if new_total_score >= 90:
                existing_assessment.totalrank = "A"
            elif new_total_score >= 80:
                existing_assessment.totalrank = "B+"
            elif new_total_score >= 70:
                existing_assessment.totalrank = "B"
            else:
                existing_assessment.totalrank = "C"

            existing_assessment.checktime = checktime
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "评分更新成功",
                "assessment_id": existing_assessment.id
            }), 200
        else:
            # 创建新记录
            # 确保所有必要的数据都已提供
            if not has_professional_general_permission and not has_product_permission:
                return jsonify({"success": False, "message": "无权提交任何评分"}), 403

            # 创建新的评估记录
            new_assessment = Assessments(
                emp_id=emp_id,
                assessmentid=assessmentid,
                totalrank=total_rank,
                totalscore=total_score,
                checktime=checktime,
                ProfessionDes=details.get('professional', {}),
                gendes=details.get('general', {}),
                extrabonus=extra_bonus,
                abiscore=abi_score,
                productscore=product_score_value
            )

            db.session.add(new_assessment)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "评分提交成功",
                "assessment_id": new_assessment.id
            }), 201

    except Exception as e:
        db.session.rollback()
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

##username:string
##password:string
@app.route('/get_employee_info', methods=['GET'])
def get_employee_info():
    emp_id = request.args.get('emp_id')
    user = User.query.filter_by(emp_id=emp_id).first()
    return jsonify(user.to_dict())
@app.route('/get_evaluation_table', methods=['GET'])
def get_evaluation_table():
    tableid = request.args.get('table_id')
    table = AssessmentItems.query.filter_by(id=tableid).first()
    return jsonify(table.to_dict())
@app.route('/showalldepartment', methods=['GET'])
def showalldepartment():
    departmentlist = []
    tmp = Department.query.all()
    for item in tmp:
        departmentlist.append({
            "name": item.name,
            "id" : item.id
        })
    return jsonify(departmentlist)
@app.route('/showtabledetail', methods=['POST'])
def showtabledetail():
    data = request.get_json()
    version = data['version']
    assessmentitem = AssessmentItems.query.filter_by(version=version).first()
    data = {
        "name": assessmentitem.version,
        "description": assessmentitem.description,
        "score_rule": assessmentitem.score_rule,
        "ddl": assessmentitem.ddl.strftime("%Y-%m-%d"),
        "forcedistrubution": assessmentitem.forcedistrubution,
    }
    return jsonify(data)
@app.route('/showtablelist', methods=['GET'])
def showtablelist():
    assessmentlist = []
    tmp = AssessmentItems.query.all()
    for item in tmp:
        if item.ddl > datetime.now():
            assessmentlist.append({
                "name": item.version,
                "id" : item.id
            })
    return jsonify(assessmentlist)
@app.route('/staffChecked', methods=['POST'])
def staffChecked():
    data = request.get_json()
    id = data['userinfo']['emp_id']
    immediate_leader = data['userinfo']['immediate_leader']


    # 获取用户对象列表
    staff_list = User.find_by_judge_id(id)

    # 转换为 JSON 可序列化的格式
    staff_dict_list = [staff.to_dict() for staff in staff_list]

    return jsonify(staff_dict_list)


@app.route("/gettable", methods=["GET"])
def gettable():
    assessmentddl = AssessmentItems.query.all()
    data = [{
        "name": item.version,
        "departmentid": item.department,
        "departmentname": Department.query.filter_by(id=item.department).first().name,
        "deadline": item.ddl.strftime("%Y-%m-%d")  # 格式化日期
    } for item in assessmentddl]
    return jsonify(data)

@app.route("/viewtable", methods=["POST"])
def viewtable():
    version = request.json['version']
    assessmentitem = AssessmentItems.query.filter_by(version=version).first()
    data = {
        "name": assessmentitem.version,
        "description": assessmentitem.description,
        "score_rule": assessmentitem.score_rule,
        "ddl": assessmentitem.ddl.strftime("%Y-%m-%d"),
        "forcedistrubution": assessmentitem.forcedistrubution,
        "punishment": assessmentitem.punishment
    }
    return jsonify(data)

@app.route("/deletetable", methods=["POST"])
def deletetable():
    version = request.json['version']
    print(request.json)
    departmentid = request.json['departmentid']
    ret = AssessmentItems.delete(version, departmentid)
    if ret == "Success":
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False}), 400

@app.route('/api/submit_evaluation', methods=['POST'])
def submit_evaluation():
    formData = request.get_json()
    print(formData)
    Description = formData['description']
    Description = json.dumps(Description)
    score_rule = formData['grades']
    score_rule = json.dumps(score_rule)
    version = formData['title']
    department = formData['departmentId']
    ddl = formData['evaluationPeriod']
    punishment = formData['attendanceRules']
    punishment = json.dumps(punishment)
    forcedis = formData['forcedDistributionPercentage']
    if AssessmentItems.search_by_version(version):
        return jsonify({"error": "绩效评估表已存在"}), 400
    try:
        AssessmentItems.create(Description, score_rule, version, ddl, forcedis, punishment, department)

    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "绩效评估表创建成功"}), 200





@app.route('/api/login', methods=['POST'])
def login():
    """ 处理登录请求 """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "无效的请求"}), 400

    user = UserCredentials.query.filter_by(username=data['username']).first()
    if not user or not user.verify_password(data['password']):
        return jsonify({"error": "用户名或密码错误"}), 401

    user_info = User.query.get(user.emp_id)
    if not user_info:
        return jsonify({"error": "用户不存在"}), 404

    access_token = create_access_token(identity=json.dumps({
        "userinfo": user_info.to_dict(),
    }))


    response = jsonify({"message": "登录成功", "access_token": access_token})
    response.set_cookie("access_token", access_token, httponly=True, samesite="Lax")  # 令牌存入 Cookie
    return response, 200

@app.route('/api/me', methods=['GET'])
@jwt_required()  # 需要携带 access_token
def get_user_info():
    """ 从 access_token 解析 userinfo """

    identity = json.loads(get_jwt_identity())  # 解析 JWT
    return jsonify({"userinfo": identity["userinfo"]}), 200

@app.before_request
def check_auth():
    """ 在访问受保护页面时，检查 JWT 令牌是否有效 """
    protected_routes = ["/Gentable", "/score_evaluation", "/member-management",
                        "/data-import", "/permission-settings", "/performance_query","/score"]

    if request.path in protected_routes:
        token = request.cookies.get("access_token")  # 从 Cookie 获取 Token
        print(token)
        if not token:
            print("未登录")
            return redirect(url_for("origin"))  # 未登录则重定向到登录页
        try:
            decoded_token = decode_token(token)  # 解析 JWT 令牌
            user_identity = decoded_token["sub"]  # 获取用户身份信息
        except Exception as e:
            print(e)
            print("令牌无效")
            return redirect(url_for("origin"))  # 令牌无效，则重定向到登录页



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


@app.route('/api/logout', methods=['GET'])
def logout():
    """登出，删除 Cookie"""
    response = redirect(url_for("origin"))
    response.delete_cookie("access_token")
    return response


@app.route('/Gentable')
@jwt_required()
def Gentable():
    return render_template('Gentable.html')

@app.route('/table_index')
@jwt_required()
def table_index():
    return render_template('table_index.html')

@app.route('/change_password')
def change_password_html():
    return render_template('change_password.html')

@app.route('/score_evaluation')
@jwt_required()
def score_evaluation():
    return render_template('score_evaluation.html')


@app.route('/member-management')
@jwt_required()
def member_management():
    return render_template('member_management.html')


@app.route('/data-import')
@jwt_required()
def data_import():
    return render_template('data_import.html')


@app.route('/permission-settings')
@jwt_required()
def permission_settings():
    return render_template('permission_settings.html')


@app.route('/performance_query')
@jwt_required()
def performance_query():

    current_user = get_jwt_identity()
    return render_template('performance_query.html', current_user=current_user)


@app.route('/')
def origin():
    return render_template("login.html")

@app.route('/score')
@jwt_required()
def score():
    return render_template("score.html")


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)

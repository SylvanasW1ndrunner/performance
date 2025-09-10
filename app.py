import json
import logging
import math
import traceback
from datetime import timedelta, datetime

import pandas as pd
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
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
from Entity.working_rate import Working_rate
from Entity.import_history import ImportHistory
#from performance.test import get_password, to_pinyin
from test import get_password, to_pinyin#（本地测试路径）

from openpyxl import Workbook
from io import BytesIO
from flask import send_file

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True)
app.config.from_object(config.Config)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']  # 同时支持从 headers 和 cookies 中获取令牌
db.init_app(app)
jwt = JWTManager(app)

@app.route('/edittable', methods=['POST'])
@jwt_required()
def edittable():
    token = get_jwt_identity()
    decoded_token = json.loads(token)
    userinfo = decoded_token["userinfo"]
    isSA = userinfo["isSA"]
    isRJ = userinfo["isRJ"]
    if not isSA:
        return jsonify({"error": "权限不足"}), 403
    formData = request.get_json()
    print(formData)
    oriDescription = formData['description']
    Description = json.dumps(oriDescription)

    des = oriDescription



    origin_score_rule = formData['grades']
    score_rule = json.dumps(origin_score_rule)


    try:
        ProGrade = des["专业职能"]["分数"]
        ProGradeList = des["专业职能"]["评分项"]
        GradeMethod = des["专业职能"]["评分方式"]
        if GradeMethod == "评级":
            Agrade = origin_score_rule[0]["value"]
            cnt = len(ProGradeList)
            totalscore = int(Agrade) * cnt
            print("totalscore:",totalscore)
            print("ProGrade:",ProGrade)
            if totalscore != ProGrade:
                return jsonify({"error": "专业职能分数不匹配"}), 400
        else:
            totalscore = 0
            for item in ProGradeList:
                key = list(item.keys())[0]
                totalscore += item[key]["分数"]
            if totalscore != ProGrade:
                return jsonify({"error": "专业职能打分不匹配"}), 400
        GenGrade = des["通用职能"]["分数"]
        GenGradeList = des["通用职能"]["评分项"]
        GenCnt = len(GenGradeList)
        genScore = GenCnt * int(origin_score_rule[0]["value"])
        if genScore != GenGrade:
            return jsonify({"error": "通用职能打分不匹配"}) ,400
        finalScore = ProGrade + GenGrade + 10 + 5 + 10
        if (ProGrade + GenGrade + 10 + 5 )- 115 == 0:
            return jsonify({"error": f"总分不正确,应为115，实际为{finalScore}，请重新设置分数"}), 400


    except Exception as e:
        print("error:",e.with_traceback())
        return jsonify({"error":"分数验证失败"}),400

    version = formData['title']
    version = str(version)
    oldversion = formData['oldversion']
    # 修复 strip() 和 replace() 方法
    version = version.strip()  # 注意赋值回去
    version = version.replace("年 ", "")  # 删除 "年" 字符

     # 如果最后一个字符是 "-"，则删除后三个字符
    if version.endswith("-"):
        version = version[:-3]

    print(version)

    department = formData['departmentId']
    forcedis = formData['forcedDistributionPercentage']
    try:
        oldTable = AssessmentItems.query.filter_by(version=oldversion,department=department).first()
        if oldTable:
            oldTable.forcedDistributionPercentage = forcedis
            oldTable.description = Description
            oldTable.grades = score_rule
            oldTable.version = version
            db.session.commit()
            return jsonify({"message": "绩效评估表更新成功"}), 200
    except Exception as e:
        db.session.rollback()
        print("error:",e.with_traceback())
        return jsonify({"error": "绩效评估表更新失败"}), 400


@app.route('/getusername', methods=['POST'])
@jwt_required()
def getusername():
    data = request.get_json()
    emp_id = data.get('emp_id')
    print("emp_id:", emp_id)
    identity = get_jwt_identity()
    user = User.query.filter_by(emp_id=emp_id).first()
    if not user:
        print("未找到用户")
        return jsonify({"error": "未找到用户"}), 404
    return jsonify({"username": user.emp_name}), 200

@app.route('/copytable', methods=['POST'])  # 复制绩效评估表
@jwt_required()
def copytable():
    data = request.get_json()
    version = data.get('version')
    year = data.get('year')
    print("year:", year)
    quarter = data.get('quarter')
    month = data.get('month')
    departmentid = data.get('departmentid')
    if not version or not year or not quarter or not month or not departmentid:
        return jsonify({"error": "缺少必要参数"}), 400
    print("version:", version)
    print("year:", year)
    print("quarter:", quarter)
    print("month:", month)
    print("departmentid:", departmentid)
    assessmentitem = AssessmentItems.query.filter_by(version=version).first()
    department = Department.query.filter_by(id=departmentid).first()
    departmentname = department.name
    if not assessmentitem:
        return jsonify({"error": "未找到考核项"}), 404
    if month == "--":
        newversion = departmentname + year  + quarter
    else:
        newversion = departmentname + year  + quarter + '-' + month
    new_item = AssessmentItems.create(
        description=assessmentitem.description,
        score_rule=assessmentitem.score_rule,
        version=newversion,
        ddl=assessmentitem.ddl,
        forcedistrubution=assessmentitem.forcedistrubution,
        punishment=assessmentitem.punishment,
        departmentid=departmentid
    )
    try:
        db.session.commit()
        return jsonify({"version": newversion,"success":True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/department_leader', methods=['POST'])
@jwt_required()
def department_leader():
    data = request.get_json()
    departmentid = data.get('id')
    print("departmentid:", departmentid)
    department = Department.query.filter_by(id=departmentid).first()

    leader_id = department.leader_id
    if leader_id:
        user = User.query.filter_by(emp_id=leader_id).first()
        return jsonify({"leader_id": leader_id, "leader_name": user.emp_name}), 200
    else:
        return jsonify({"leader_id": None, "leader_name": None}), 200


@app.route('/api/update_performance_score', methods=['POST'])
@jwt_required()
def update_performance_score():
    try:
        token =json.loads(get_jwt_identity())
        user = token["userinfo"]
        if user["isSA"] is False:
            return jsonify({"error": "权限不足"}), 403

        data = request.get_json()
        userid = data.get('userId')
        tableid = data.get('tableId')
        newScore = data.get('totalScore')
        print("userid:", userid)
        print("tableid:", tableid)
        assessment = Assessments.query.filter_by(emp_id=userid, assessmentid=tableid).first()

        if not assessment:
            return jsonify({"error": "未找到评估记录"}), 404

        assessment.totalscore = newScore
        total_rank = "C"  # 默认等级
        if newScore >= 90:
            total_rank = "A"
        elif newScore >= 80:
            total_rank = "B+"
        elif newScore >= 70:
            total_rank = "B"
        else:
            total_rank = "C"
        assessment.totalrank = total_rank

        db.session.commit()

        return jsonify({"message": "评分更新成功"}), 200

    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/department_members/<departmentId>', methods=['GET'])
@jwt_required()
def get_department_members(departmentId):
    try:
        # 获取部门ID
        if not departmentId:
            return jsonify({"error": "缺少必要参数"}), 400

        # 查询部门成员
        members = User.query.filter_by(departmentid=departmentId).all()
        members = [member.to_dict() for member in members]
        print("members:", members)
        return jsonify(members), 200
    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/product_line_members/<productLineId>', methods=['GET'])
@jwt_required()
def get_product_line_members(productLineId):
    try:
        # 获取产品线ID
        if not productLineId:
            return jsonify({"error": "缺少必要参数"}), 400

        # 查询产品线成员
        members = User.query.filter_by(productid=productLineId).all()
        members = [member.to_dict() for member in members]
        print(members)
        return jsonify(members), 200
    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/performance_detail', methods=['GET', 'POST'])
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
        print("assessment!!:",assessment)
        if not assessment:
            return jsonify({"error": "未找到绩效记录"}), 404

        # 计算职能评分和产品评分的权重
        # 假设职能评分权重为60%，产品评分权重为40%
        functional_weight = 0.6
        product_weight = 0.4
        # 查询考勤评分
        working_rate = Working_rate.query.filter_by(emp_id=user_id).first()
        attendance_score = working_rate.rate if working_rate else 0.0
        # 构建响应数据
        response_data = {
            "functionalScore": float(assessment.abiscore),
            "functionalWeight": functional_weight,
            "productScore": float(assessment.productscore),
            "productWeight": product_weight,
            "totalScore": float(assessment.totalscore),
            "grade": assessment.totalrank,
            "comment": "",  # 默认为空，因为您提到评语不显示
            "ProfessDes": assessment.ProfessionDes,
            "GeneralDes": assessment.gendes,
            "ProductDes": assessment.productscore,
            "ExtraBonus":assessment.extrabonus,
            # 添加考勤评分 25年9月9日
            "attendanceScore":attendance_score
        }

        return jsonify(response_data)

    except Exception as e:
        print("error:", e)
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


# 获取当前用户的权限信息，并将权限等级分级传输
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
                "name": product.name,
                "number": product.number
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
                "name": department.name,
                "number": department.number
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

        # 构建响应数据
        response_data = {
            "name": user.emp_name,
            "employeeId": user.emp_id,
            "team": department,
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
        has_professional_general_permission = is_sa or (
                is_rj and employee.immediate_leader == current_user.get('emp_id'))
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
        # 获取考勤分数
        working_rate = Working_rate.query.filter_by(emp_id=emp_id).first()
        print(type(working_rate))
        depart_working_rate = 0
        if employee.departmentid==1 or employee.departmentid==2:
            department = Department.query.filter_by(id=employee.departmentid).first()
            avgattendance = department.avgattendance if department.avgattendance is not None else 0  # 处理当前部门 avgattendance 为空的情况

            # 将 None 值替换为 0 并排序
            allavgattendance = sorted([d.avgattendance if d.avgattendance is not None else 0 for d in Department.query.all()])

            # 确保 allavgattendance 不为空
            if allavgattendance:
                # 排序并去重，确保正确的排名次序（假设从高到低）
                sorted_attendance = sorted(allavgattendance, reverse=True)

                # 获取当前 avgattendance 的排名（从 1 开始）
                rank_index = sorted_attendance.index(avgattendance) + 1

                # 根据排名分配分数
                if rank_index == 1:
                    depart_working_rate = 10
                elif rank_index in [2, 3]:
                    depart_working_rate = 8
                elif 4 <= rank_index <= 7:
                    depart_working_rate = 6
                elif 8 <= rank_index <= 9:
                    depart_working_rate = 4
                else:
                    depart_working_rate = 2
            else:
                depart_working_rate = 0  # 如果没有有效数据，则设为 0
        working_rate_value = working_rate.rate
        tmp_value = working_rate_value + depart_working_rate
        total_score += tmp_value
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
            current_extra_bonus = existing_assessment.extrabonus.get('score',
                                                                     0) if existing_assessment.extrabonus else 0
            print("current_extra_bonus", current_extra_bonus)
            if current_extra_bonus is None:
                current_extra_bonus = 0
            # 如果提交了新的专业职能或通用职能评分，更新能力分数
            if (professional_data is not None or general_data is not None) and has_professional_general_permission:
                existing_assessment.abiscore = abi_score
                current_abi_score = abi_score

            # 重新计算总分
            new_total_score = current_abi_score + current_product_score + current_extra_bonus
            existing_assessment.totalscore = new_total_score + tmp_value

            # 更新等级 - 修改这里，使用包含考勤分数的总分
            final_score_with_attendance = new_total_score + tmp_value
            if final_score_with_attendance >= 90:
                existing_assessment.totalrank = "A"
            elif final_score_with_attendance >= 80:
                existing_assessment.totalrank = "B+"
            elif final_score_with_attendance >= 70:
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
    if not user.immediate_leader:
        leader_name = "暂无"
    else:
        leader = User.query.filter_by(emp_id=user.immediate_leader).first()
        leader_name = leader.emp_name
    user = user.to_dict()
    user['leader_name'] = leader_name
    print(user)
    return user


@app.route('/get_evaluation_table', methods=['GET'])
def get_evaluation_table():
    tableid = request.args.get('table_id')
    table = AssessmentItems.query.filter_by(id=tableid).first()
    return jsonify(table.to_dict())


@app.route('/showalldepartment', methods=['POST', 'GET'])
@jwt_required()
def showalldepartment():
    token = get_jwt_identity()
    token = json.loads(token)
    userid = token["userinfo"]["emp_id"]
    user = User.query.filter_by(emp_id=userid).first()
    departmentlist = []
    tmp = Department.query.all()
    for item in tmp:
        if item.name == "未分配":
            continue
        if user.isSA is False and item.leader_id != userid:
            continue
        departmentlist.append({
            "name": item.name,
            "id": item.id
        })
    print(departmentlist)
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


@app.route('/showtablelist', methods=['POST'])
def showtablelist():
    emp_id = request.json['empId']
    print(emp_id)
    user = User.query.filter_by(emp_id=emp_id).first()
    assessmentlist = []
    tmp = AssessmentItems.query.all()
    for item in tmp:
        if user.departmentid == item.department:
            assessmentlist.append({
                "name": item.version,
                "id": item.id
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
    current_time = datetime.now()  # 获取当前时间

    data = [{
        "name": item.version,
        "departmentid": item.department,
        "departmentname": Department.query.filter_by(id=item.department).first().name,
        "deadline": item.ddl.strftime("%Y-%m-%d")  # 格式化日期
    } for item in assessmentddl]  # 只返回 deadline 未过期的项

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


@app.route('/api/submit_evaluation', methods=['POST'])  # 提交绩效评估表
@jwt_required()
def submit_evaluation():
    token = get_jwt_identity()
    decoded_token = json.loads(token)
    userinfo = decoded_token["userinfo"]
    isSA = userinfo["isSA"]
    isRJ = userinfo["isRJ"]
    if not isSA:
        return jsonify({"error": "权限不足"}), 403
    formData = request.get_json()
    oriDescription = formData['description']
    Description = json.dumps(oriDescription)

    des = oriDescription



    origin_score_rule = formData['grades']
    score_rule = json.dumps(origin_score_rule)


    try:
        ProGrade = des["专业职能"]["分数"]
        ProGradeList = des["专业职能"]["评分项"]
        GradeMethod = des["专业职能"]["评分方式"]
        if GradeMethod == "评级":
            Agrade = origin_score_rule[0]["value"]
            cnt = len(ProGradeList)
            totalscore = int(Agrade) * cnt
            print("totalscore:",totalscore)
            print("ProGrade:",ProGrade)
            if totalscore != ProGrade:
                return jsonify({"error": "专业职能分数不匹配"}), 400
        else:
            totalscore = 0
            for item in ProGradeList:
                print(type(item))
                keys = list(item.keys())
                key = keys[0]
                totalscore += item[key]["分数"]
            if totalscore != ProGrade:
                return jsonify({"error": "专业职能打分不匹配"}), 400
        GenGrade = des["通用职能"]["分数"]
        GenGradeList = des["通用职能"]["评分项"]
        GenCnt = len(GenGradeList)
        genScore = GenCnt * int(origin_score_rule[0]["value"])
        if genScore != GenGrade:
            return jsonify({"error": "通用职能打分不匹配"}) ,400
        finalScore = ProGrade + GenGrade + 10 + 5 + 10
        if (ProGrade + GenGrade + 10 + 5 )- 115 == 0:
            return jsonify({"error": f"总分不正确,应为115，实际为{finalScore}，请重新设置分数"}), 400


    except Exception as e:
        print("error:",e.with_traceback())
        return jsonify({"error":"分数验证失败"}),400

    version = formData['title']
    version = str(version)

    # 修复 strip() 和 replace() 方法
    version = version.strip()  # 注意赋值回去
    version = version.replace("年 ", "")  # 删除 "年" 字符

    # 如果最后一个字符是 "-"，则删除后三个字符
    if version.endswith("-"):
        version = version[:-3]

    print(version)

    department = formData['departmentId']
    ddl = formData['evaluationPeriod']
    punishment = formData['attendanceRules']
    punishment = json.dumps(punishment)
    forcedis = formData['forcedDistributionPercentage']
    if AssessmentItems.search_by_version(version):
        return jsonify({"error": "绩效评估表已存在"}), 400
    if department is None:
        return jsonify({"error": "部门不能为空"}), 400
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
                        "/data-import", "/permission-settings", "/performance_query", "/score","/table_index","/data-export","/edittable","/score_evaluation"]

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


@app.route('/api/add_depart', methods=['POST'])
@jwt_required()
def add_depart():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    if "name" not in request.get_json():
        return jsonify({"error": "缺少必要参数"}), 400
    depart = request.get_json()["name"]
    leader_id = request.get_json()["leader_id"]
    try:
        user = User.query.filter_by(emp_id=leader_id).first()
        user.change_info(isRJ=True)
        Department.add_department(depart, leader_id)
        departid = Department.query.filter_by(name=depart).first().id
    except Exception as e:
        print("error:", e)
        return jsonify({"error": "用户不存在"}), 500
    return jsonify({"message": "部门添加成功"}), 200


@app.route('/api/delete_depart', methods=['POST'])
@jwt_required()
def delete_depart():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    if "id" not in request.get_json():
        return jsonify({"error": "缺少必要参数"}), 400
    depart = request.get_json()["id"]
    if depart == '0':
        print("无法删除默认部门")
        return jsonify({"error": "无法删除默认部门"}), 400
    depart_leader_id = Department.query.filter_by(id=depart).first().leader_id
    try:
        Department.delete_department(depart)
        if depart_leader_id:
            user = User.query.filter_by(emp_id=depart_leader_id).first()
            user.change_info(isRJ=False)
        originusers = User.query.filter_by(departmentid=depart).all()
        for user in originusers:
            user.change_info(departmentid=0, department="未分配")
        return jsonify({"message": "部门删除成功"}), 200
    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/add_product', methods=['POST'])
@jwt_required()
def add_product():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    if "name" not in request.get_json():
        return jsonify({"error": "缺少必要参数"}), 400

    product = request.get_json()["name"]
    leader_ids = request.get_json()["leader_ids"]
    print(leader_ids)
    try:
        userids = User.query.all()
        userids = [user.emp_id for user in userids]
        for leader in leader_ids:
            if leader not in userids:
                return jsonify({"error": "用户不存在"}), 500
        Product.add_product(product, leader_ids)
        productid = Product.query.filter_by(name=product).first().id
        return jsonify({"message": "产品线添加成功"}), 200
    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete_product', methods=['POST'])
@jwt_required()
def delete_product():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    if "id" not in request.get_json():
        return jsonify({"error": "缺少必要参数"}), 400
    product = request.get_json()["id"]
    print(product)
    if product == '0':
        return jsonify({"error": "无法删除默认产品线"}), 400
    product_leader_ids = Product.query.filter_by(id=product).first().leader_id
    try:
        if product_leader_ids:
            for product_leader_id in product_leader_ids:
                user = User.query.filter_by(emp_id=product_leader_id).first()
                user.change_info(isPJ=False)
        originusers = User.query.filter_by(productid=product).all()
        for user in originusers:
            user.change_info(productid=0, ProductGroup="未分配")
        Product.delete_product(product)
        return jsonify({"message": "产品线删除成功"}), 200
    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/adduser', methods=['POST'])
@jwt_required()
def adduser():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    if "name" not in request.get_json() or "empno" not in request.get_json():
        return jsonify({"error": "缺少必要参数"}), 400
    emp_name = request.get_json()["name"]
    emp_id = request.get_json()["empno"]
    position = request.get_json()["position"] or None
    department_id = request.get_json()["department_id"] or 0
    isSA = False
    isRJ = request.get_json()["is_manager"] or False
    isPJ = request.get_json()["is_product_manager"] or False
    directJudgeid = request.get_json()["product_line_rater"] or None
    productid = request.get_json()["product_line_id"] or None
    immediate_leader = Department.query.filter_by(id=department_id).first().leader_id if department_id else None
    ProductGroup = Product.query.filter_by(id=productid).first().name if productid else 0
    department = Department.query.filter_by(id=department_id).first().name if department_id else None

    try:
        User.add_user(emp_name=emp_name, emp_id=emp_id, position=position, departmentid=department_id,
                      productid=productid, isSA=isSA, isRJ=isRJ, isPJ=isPJ, directJudgeid=directJudgeid,
                      ProductGroup=ProductGroup, immediate_leader=immediate_leader, department=department)
        if isRJ:
            manageDepart = request.get_json()["manageDepartment"]
            department = Department.query.filter_by(id=manageDepart).first()
            originleader_id = department.leader_id
            origin_leader = User.query.filter_by(emp_id=originleader_id).first()
            origin_leader.isRJ = False
            department.leader_id = emp_id
            users = User.query.filter_by(departmentid=manageDepart).all()
            for user in users:
                user.immediate_leader = emp_id
        if isPJ:
            manageProduct = request.get_json()["manageProduct"]
            product = Product.query.filter_by(id=manageProduct).first()
            leader_ids = product.leader_id
            leader_ids.append(emp_id)
            product.leader_id = leader_ids
        UserCredentials.add_credentials(to_pinyin(emp_name), emp_id, get_password(emp_id))
        db.session.commit()
        return jsonify({"message": "用户添加成功"}), 200
    except Exception as e:
        db.session.rollback()
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/edituser', methods=['POST'])
@jwt_required()
def edituser():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    if "empno" not in request.get_json():
        return jsonify({"error": "缺少必要参数"}), 400
    emp_name = request.get_json()["name"] or None
    emp_id = request.get_json()["empno"]
    position = request.get_json()["position"] or None
    department_id = request.get_json()["department_id"] or 0
    product_id = request.get_json()["product_line_id"] or 0
    isSA = None
    isRJ = request.get_json()["is_manager"] or None
    isPJ = request.get_json()["is_product_manager"] or None
    directJudgeid = request.get_json()["product_line_rater"] or None
    user = User.query.filter_by(emp_id=emp_id).first()
    department = Department.query.filter_by(id=department_id).first()
    immediate_leader_id = None
    ProductGroup = None
    if department_id:
        immediate_leader_id = Department.query.filter_by(id=department_id).first().leader_id
        department = Department.query.filter_by(id=department_id).first()
    if product_id:
        ProductGroup = Product.query.filter_by(id=product_id).first().name
    try:

        user.change_info(emp_name=emp_name, emp_id=None, position=position, departmentid=department_id,
                         productid=product_id, isSA=isSA, isRJ=isRJ, isPJ=isPJ, directJudgeid=directJudgeid,
                         ProductGroup=ProductGroup, immediate_leader=immediate_leader_id, department=department.name)
        if isRJ:
            manageDepart = request.get_json()["manageDepartment"]
            department = Department.query.filter_by(id=manageDepart).first()
            originleader_id = department.leader_id
            origin_leader = User.query.filter_by(emp_id=originleader_id).first()
            origin_leader.isRJ = False
            department.leader_id = emp_id
            users = User.query.filter_by(departmentid = manageDepart).all()
            for user in users:
                user.immediate_leader = emp_id
        if isPJ:
            manageProduct = request.get_json()["manageProduct"]
            product = Product.query.filter_by(id=manageProduct).first()
            leader_ids = product.leader_id
            leader_ids.append(emp_id)
            product.leader_id = leader_ids


        db.session.commit()

        return jsonify({"message": "用户修改成功"}), 200
    except Exception as e:
        db.session.rollback()
        print("error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/deleteuser', methods=['POST'])
@jwt_required()
def deleteuser():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    if "empno" not in request.get_json():
        return jsonify({"error": "缺少必要参数"}), 400
    emp_id = request.get_json()["empno"]
    print(emp_id)
    try:
        User.delete_user(emp_id)
        return jsonify({"message": "用户删除成功"}), 200
    except Exception as e:
        print("error:", e)
        return jsonify({"error": str(e)}), 500


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



def calculate_rate(total_hours_dict):
    # 将工时按降序排序
    sorted_hours = sorted(total_hours_dict.items(), key=lambda x: x[1], reverse=True)
    total_people = len(sorted_hours)

    # 计算每个分数段的人数（向上取整）
    segment_size = math.ceil(total_people * 0.1)

    rates = {}
    current_index = 0

    # 遍历排序后的工时列表，分配分数
    for i, (name, hours) in enumerate(sorted_hours):
        # 如果当前工时与前一个相同，给相同的分数
        if i > 0 and hours == sorted_hours[i - 1][1]:
            rates[name] = rates[sorted_hours[i - 1][0]]
        else:
            # 根据当前位置计算分数
            if current_index < segment_size:  # 前10%
                rates[name] = 10
            elif current_index < segment_size * 3:  # 11%-30%
                rates[name] = 8
            elif current_index < segment_size * 5:  # 31%-50%
                rates[name] = 6
            elif current_index < segment_size * 7:  # 51%-70%
                rates[name] = 5
            elif current_index < segment_size * 9:  # 71%-90%
                rates[name] = 4
            else:  # 91%-100%
                rates[name] = 3
        current_index += 1

    return rates


@app.route('/api/import_history', methods=['GET'])
@jwt_required()
def get_import_history():
    try:
        # 添加调试日志
        print("开始获取导入历史")

        # 获取所有记录
        history = ImportHistory.query.all()
        print(f"查询到的记录数: {len(history)}")

        # 检查每条记录
        for h in history:
            print(f"记录ID: {h.id}, 文件名: {h.filename}")

        # 转换为JSON格式
        history_data = [{
            'filename': h.filename
        } for h in history]
        print(f"转换后的数据: {history_data}")

        return jsonify({
            'success': True,
            'history': history_data
        })
    except Exception as e:
        print(f"获取导入历史错误: {str(e)}")
        return jsonify({'success': False, 'message': '获取导入历史失败'})

@app.route('/upload_performance', methods=['POST'])
@jwt_required()
def upload_performance():
    # 验证用户权限
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isSA = decoded_token["isSA"]

    if not isSA:
        return jsonify({'success': False, 'message': '权限不足，仅系统管理员可以上传文件'}), 403

    if 'file1' not in request.files or 'file2' not in request.files or 'file3' not in request.files:
        return jsonify({'success': False, 'message': '请上传所有三个文件'})

    files = {
        'file1': request.files['file1'],
        'file2': request.files['file2'],
        'file3': request.files['file3']
    }

    # 检查文件名
    for file_key, file in files.items():
        if file.filename == '':
            return jsonify({'success': False, 'message': f'{file_key}未选择文件'})
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': f'{file_key}文件格式不正确'})

    try:
        # 清空历史记录表
        ImportHistory.query.delete()
        db.session.commit()
        i = 0
        # 逐个添加文件记录
        for file_key, file in files.items():
            if file and file.filename:  # 确保文件对象和文件名存在
                i = i + 1
                new_history = ImportHistory(id=i, filename=file.filename)
                db.session.add(new_history)
                print(f"添加导入历史记录: {file.filename}")
        # 提交新记录
        db.session.commit()
        wronglist = []
        # 用于存储所有人员的总工时
        all_hours = {}

        # 处理每个文件
        for file in files.values():
            # 读取Excel文件
            df = pd.read_excel(file, header=None)

            # 确保文件至少有5行数据
            if len(df) < 5:
                return jsonify({'success': False, 'message': '文件格式错误：数据行数不足'})

            # 处理列名
            headers = []
            for col in range(len(df.columns)):
                row3_val = str(df.iloc[2, col])
                row4_val = str(df.iloc[3, col])

                if row3_val != 'nan':
                    header = row3_val.strip()
                else:
                    header = row4_val.strip()

                if not header or header == 'nan':
                    header = f'Column_{col}'
                headers.append(header)

            # 设置列名并删除前4行
            df.columns = headers
            df = df.iloc[4:].reset_index(drop=True)

            # 处理数据
            for index, row in df.iterrows():
                try:
                    name = str(row['姓名']).strip()
                    if name and name != 'nan':
                        # 计算当前表格的工时
                        work_hours = float(row.get('工作时长', 0)) if pd.notna(row.get('工作时长')) else 0.0
                        business_hours = float(row.get('出差时长', 0)) if pd.notna(
                            row.get('出差时长')) else 0.0
                        nursing_hours = float(row.get('哺乳假(小时)', 0)) if pd.notna(
                            row.get('哺乳假(小时)')) else 0.0

                        maternity_days = float(row.get('产假(天)', 0)) if pd.notna(
                            row.get('产假(天)')) else 0.0
                        paternity_days = float(row.get('陪产假(天)', 0)) if pd.notna(
                            row.get('陪产假(天)')) else 0.0
                        marriage_days = float(row.get('婚假(天)', 0)) if pd.notna(
                            row.get('婚假(天)')) else 0.0
                        funeral_days = float(row.get('丧假(天)', 0)) if pd.notna(
                            row.get('丧假(天)')) else 0.0
                        parental_days = float(row.get('育儿假(天)', 0)) if pd.notna(
                            row.get('育儿假(天)')) else 0.0

                        leave_hours = 7.5 * (maternity_days + paternity_days + marriage_days +
                                             funeral_days + parental_days)
                        total_hours = work_hours + business_hours + nursing_hours + leave_hours

                        # 累加到总工时字典
                        if name in all_hours:
                            all_hours[name] += total_hours
                        else:
                            all_hours[name] = total_hours

                except Exception as e:
                    print(f"处理行 {index} 时出错: {str(e)}")
                    continue

        # 计算评分
        rates = calculate_rate(all_hours)

        # 更新数据库
        processed_data = []
        for name, total_hours in all_hours.items():
            user = User.query.filter_by(emp_name = name).first()
            if user is None:
                wronglist.append(name)
                continue
            try:
                # 查找或创建记录
                existing_record = Working_rate.query.filter_by(emp_name=name).first()
                if existing_record:
                    existing_record.work_hours = total_hours
                    existing_record.rate = rates[name]
                    print(f"更新记录: {name}, 总工时: {total_hours}, 评分: {rates[name]}")
                    db.session.commit()
                else:
                    new_record = Working_rate(
                        emp_name=name,
                        work_hours=total_hours,
                        rate=rates[name]
                    )
                    db.session.add(new_record)
                    db.session.commit()
                    print(f"创建新记录: {name}, 总工时: {total_hours}, 评分: {rates[name]}")

                processed_data.append({
                    'name': name,
                    'total_hours': total_hours,
                    'rate': rates[name]
                })
            except Exception as e:
                wronglist.append(name)
                print(f"数据库操作错误: {str(e)}")
                continue
        #print(f"部门工时统计操作成功 ")
        if not update_department_avg_hours():
            return jsonify({'success': False, 'message': '更新部门平均工时失败'})
        if wronglist is not None:
            return jsonify({'success': False,
    'message': f'更新成功，但以下人员更新失败：{", ".join(map(str, wronglist))}',  # 将列表内容转换为字符串
    'wronglist': wronglist}) , 400
        # 更新部门平均工时
        #if not update_department_avg_hours():
            #return jsonify({'success': False, 'message': '更新部门平均工时失败'})


        # 提交所有更改

        return jsonify({
            'success': True,
            'data': processed_data
        })


    except Exception as e:
        print(f"处理错误: {str(e)}")
        return jsonify({'success': False, 'message': '文件处理出错，请确保文件格式正确'})



def update_department_avg_hours():
    """更新部门平均工时"""
    print(f"部门工时统计操作成功 ")
    try:
        # 获取所有工时记录
        all_working_hours = Working_rate.query.all()

        # 初始化部门工时统计
        department_stats = {}  # 格式: {dept_id: {'total_hours': 0, 'count': 0}}

        # 遍历工时记录，按部门统计
        for record in all_working_hours:
            # 通过姓名查找用户及其部门
            user = User.query.filter_by(emp_name=record.emp_name).first()
            if user and user.departmentid:
                dept_id = user.departmentid

                # 初始化部门统计数据
                if dept_id not in department_stats:
                    department_stats[dept_id] = {
                        'total_hours': 0,
                        'count': 0
                    }

                # 累加部门工时和人数
                department_stats[dept_id]['total_hours'] += record.work_hours
                department_stats[dept_id]['count'] += 1

        # 更新每个部门的平均工时
        for dept_id, stats in department_stats.items():
            try:
                department = Department.query.get(dept_id)
                if department and stats['count'] > 0:
                    # 计算平均工时并保留两位小数
                    avg_hours = round(stats['total_hours'] / stats['count'], 2)
                    # 更新部门表
                    department.avgattendance = avg_hours
                    print(f"更新部门 {department.name} 平均工时: {avg_hours:.2f}")
            except Exception as e:
                print(f"更新部门 {dept_id} 平均工时时出错: {str(e)}")
                continue

        # 提交更改
        try:
            db.session.commit()
            print("所有部门平均工时更新完成")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"提交更改时出错: {str(e)}")
            return False

    except Exception as e:
        print(f"计算部门平均工时时出错: {str(e)}")
        return False


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/export_working_rate', methods=['GET'])
@jwt_required()
def export_working_rate():
    # 验证用户权限
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isSA = decoded_token["isSA"]

    if not isSA:
        return jsonify({'success': False, 'message': '权限不足，仅系统管理员可以导出工时文件'}), 406

    try:
        # 获取数据并按工时降序排序
        working_rates = Working_rate.query.order_by(Working_rate.work_hours.desc()).all()

        # 创建工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "工时统计"

        # 添加表头
        headers = ['员工ID', '员工姓名', '总工时', '评分']
        ws.append(headers)

        # 添加数据
        for rate in working_rates:
            ws.append([
                rate.emp_id,
                rate.emp_name,
                rate.work_hours,
                rate.rate
            ])

        # 调整列宽
        for column in ws.columns:
            max_length = 0
            column = list(column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column[0].column_letter].width = adjusted_width

        # 保存到内存
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='工时统计详情.xlsx'
        )

    except Exception as e:
        print(f"导出工时统计错误: {str(e)}")
        return jsonify({'success': False, 'message': '导出失败'}), 500



# 获取部门列表
@app.route('/api/departments', methods=['GET'])
def get_departments():
    try:
        # 从数据库获取部门信息
        departments = db.session.query(Department).all()

        return jsonify({
            'success': True,
            'departments': [{'id': dept.id, 'name': dept.name} for dept in departments]
        })
    except Exception as e:
        print(f"获取部门列表错误: {str(e)}")
        return jsonify({'success': False, 'message': '获取部门列表失败'})


# 根据部门获取版本列表
@app.route('/api/versions', methods=['GET'])
def get_versions():
    department_id = request.args.get('department')

    if not department_id:
        return jsonify({'success': False, 'message': '缺少部门参数'})

    try:
        if department_id == 'all':
            # 如果选择"所有部门"，获取所有版本
            versions = db.session.query(AssessmentItems.version).distinct().all()
        else:
            # 尝试将department_id转换为整数
            try:
                dept_id = int(department_id)
                # 查询指定部门的所有版本
                versions = db.session.query(AssessmentItems.version) \
                    .filter(AssessmentItems.department == dept_id) \
                    .distinct().all()
            except ValueError:
                return jsonify({'success': False, 'message': '无效的部门ID'})

        return jsonify({
            'success': True,
            'versions': [v[0] for v in versions]
        })
    except Exception as e:
        print(f"获取版本列表错误: {str(e)}")
        return jsonify({'success': False, 'message': '获取版本列表失败'})


@app.route('/api/assessments', methods=['GET'])
@jwt_required()
def get_assessments():
    try:
        # 获取用户身份信息
        token = get_jwt_identity()
        userinfo = json.loads(token)["userinfo"]
        isSA = userinfo.get("isSA", False)
        emp_id = userinfo.get("emp_id")

        department_id = request.args.get('department')
        version = request.args.get('version')

        # 验证权限
        if not isSA:
            # 检查是否为部门管理员
            dept = Department.query.filter_by(leader_id=emp_id).first()
            if not dept:
                return jsonify({'success': False, 'message': '无权限查看绩效信息'}), 403

            # 部门管理员只能查看自己部门的数据
            if str(dept.id) != str(department_id):
                return jsonify({'success': False, 'message': '无权限查看其他部门的绩效信息'}), 403

        # 处理超级管理员查看所有部门的情况
        if department_id == 'all':
            # 获取所有部门
            departments = Department.query.all()
            all_assessments = []

            for dept in departments:
                # 获取该部门最新的绩效表（id最大的）
                latest_item = db.session.query(AssessmentItems) \
                    .filter(AssessmentItems.department == dept.id) \
                    .order_by(AssessmentItems.id.desc()) \
                    .first()

                if latest_item:
                    # 获取该部门最新版本的评估数据
                    dept_data = get_department_assessments(dept.id, latest_item.version)
                    all_assessments.append({
                        'department_name': dept.name,
                        'assessments': dept_data or []
                    })
                else:
                    # 部门没有任何评估记录
                    all_assessments.append({
                        'department_name': dept.name,
                        'assessments': []
                    })

            return jsonify({
                'success': True,
                'assessments': all_assessments
            })

        # 处理单个部门查询
        else:
            results = get_department_assessments(department_id, version)
            if not results:
                return jsonify({
                    'success': True,
                    'assessments': [{
                        'department_name': Department.query.get(department_id).name,
                        'assessments': []
                    }]
                })

            return jsonify({
                'success': True,
                'assessments': [{
                    'department_name': Department.query.get(department_id).name,
                    'assessments': results
                }]
            })

    except Exception as e:
        print(f"查询绩效数据错误: {str(e)}")
        return jsonify({'success': False, 'message': '查询失败'})


def get_department_assessments(department_id, version):
    try:
        # 查询符合条件的考核项
        assessment_items = db.session.query(AssessmentItems) \
            .filter(AssessmentItems.department == department_id,
                    AssessmentItems.version == version).all()

        if not assessment_items:
            return []

        # 检查评分方式
        for item in assessment_items:
            # try:
            description = json.loads(item.description)
                # 检查专业职能中的评分方式
            prof_scoring = description.get("专业职能", {}).get("评分方式")

                # 统计A和B+的数量
            total_grades = 0
            total_employees = 0
            total_scores = 0
            scores_list = []

            # 获取所有评估记录
            assessment_ids = [item.id for item in assessment_items]
            assessments = db.session.query(Assessments) \
                .filter(Assessments.assessmentid.in_(assessment_ids)) \
                .all()

            print("开始统计评级...")  # 调试信息

            # 统计每个员工的A和B+数量
            for assessment in assessments:
                try:
                    total_employees += 1
                    print(f"处理员工ID: {assessment.emp_id}")

                    # 记录总分用于计算平均分和方差
                    if assessment.totalscore is not None:
                        score = float(assessment.totalscore)
                        total_scores += score
                        scores_list.append(score)

                    if prof_scoring == "评级":
                        # 评级模式：直接统计专业职能和通用职能的A、B+
                        if assessment.ProfessionDes:
                            prof_data = json.loads(assessment.ProfessionDes) if isinstance(assessment.ProfessionDes,
                                                                                           str) else assessment.ProfessionDes
                            if isinstance(prof_data, list):
                                for item in prof_data:
                                    grade = item.get('grade', '').strip().upper()
                                    if isinstance(item, dict) and (grade in ["A", "B+"]):
                                        total_grades += 1
                    else:
                        # 打分模式：专业职能按分数换算B+个数
                        if assessment.ProfessionDes:
                            prof_data = json.loads(assessment.ProfessionDes) if isinstance(assessment.ProfessionDes,
                                                                                           str) else assessment.ProfessionDes
                            if isinstance(prof_data, list):
                                prof_score = sum(item.get('score', 0) for item in prof_data)
                                # 按规则换算B+个数
                                if prof_score >= 27:
                                    total_grades += 3
                                elif prof_score >= 20:
                                    total_grades += 2
                                else:
                                    total_grades += 1

                    # 统计通用职能的A、B+（两种模式都需要）
                    if assessment.gendes:
                        gen_data = json.loads(assessment.gendes) if isinstance(assessment.gendes,
                                                                               str) else assessment.gendes
                        if isinstance(gen_data, list):
                            for item in gen_data:
                                grade = item.get('grade', '').strip().upper()
                                if isinstance(item, dict) and (grade in ["A", "B+"]):
                                    total_grades += 1

                except Exception as e:
                    print(f"处理评分数据错误: {str(e)}")
                    continue

            print(f"统计结果 - 总评级数: {total_grades}, 总员工数: {total_employees}")  # 调试信息

            # 计算统计数据
            if total_employees > 0 and scores_list:
                avg_score = round(total_scores / total_employees, 2)

                # 计算方差：Σ(x - μ)²/n
                squared_diff_sum = sum((score - avg_score) ** 2 for score in scores_list)
                variance = round(squared_diff_sum / total_employees, 2)
            else:
                avg_score = variance = 0

            # 计算平均值
            avg_grades = round(total_grades / total_employees, 2) if total_employees > 0 else 0
            print(f"平均评级数: {avg_grades}")  # 调试信息

            # 获取常规评估数据
            results = get_normal_assessments(assessment_items)

            # 添加统计信息
            return {
                'assessments': results,
                'stats': {
                    'avg_grades': avg_grades,
                    'total_employees': total_employees,
                    'avg_score': avg_score,
                    'score_variance': variance
                }
            }

    except Exception as e:
        print(f"获取部门绩效数据错误: {str(e)}")
        return []

def get_normal_assessments(assessment_items):
    """获取常规评估数据"""
    try:
        assessment_ids = [item.id for item in assessment_items]
        dept_users = User.query.filter_by(departmentid=assessment_items[0].department).all()
        dept_user_ids = {user.emp_id: user.emp_name for user in dept_users}

        assessments = db.session.query(Assessments) \
            .filter(Assessments.assessmentid.in_(assessment_ids)) \
            .all()

        results = []
        assessed_emp_ids = set()

        for assessment in assessments:
            if assessment.emp_id in dept_user_ids:
                results.append({
                    'emp_id': assessment.emp_id,
                    'emp_name': dept_user_ids[assessment.emp_id],
                    'totalrank': assessment.totalrank,
                    'totalscore': assessment.totalscore,
                    'checktime': assessment.checktime.strftime('%Y-%m-%d %H:%M:%S'),
                    'abiscore': assessment.abiscore,
                    'productscore': assessment.productscore
                })
                assessed_emp_ids.add(assessment.emp_id)

        for emp_id, emp_name in dept_user_ids.items():
            if emp_id not in assessed_emp_ids:
                results.append({
                    'emp_id': emp_id,
                    'emp_name': emp_name,
                    'totalrank': '未评分',
                    'totalscore': '未评分',
                    'checktime': '未评分',
                    'abiscore': '未评分',
                    'productscore': '未评分'
                })

        return results

    except Exception as e:
        print(f"获取常规评估数据错误: {str(e)}")
        return []


@app.route('/api/logout', methods=['GET'])
def logout():
    """登出，删除 Cookie"""
    response = redirect(url_for("origin"))
    response.delete_cookie("access_token")
    return response


@app.route('/getProductManager', methods=['GET'])
@jwt_required()
def getProductManager():
    decoded_token = json.loads(get_jwt_identity())["userinfo"]
    isadmin = decoded_token["isSA"]
    if not isadmin:
        return jsonify({"error": "权限不足"}), 403  # 获取用户身份信息
    productid = request.args.get('product_line_id')
    leader_id = Product.query.filter_by(id=productid).first().leader_id
    if leader_id is None:
        return jsonify([]), 200
    leaders = User.query.filter(User.emp_id.in_(leader_id)).all()
    result = [{"emp_id": leader.emp_id, "name": leader.emp_name} for leader in leaders]
    return jsonify(result), 200


@app.route('/Gentable')
@jwt_required()
def Gentable():
    token = get_jwt_identity()
    userinfo = json.loads(token)["userinfo"]
    if userinfo["isSA"] is False:
        return render_template('no_access.html')
    return render_template('Gentable.html')


@app.route('/table_index')
@jwt_required()
def table_index():
    token = get_jwt_identity()
    userinfo = json.loads(token)["userinfo"]
    if userinfo["isSA"] is False:
        return render_template('no_access.html')
    return render_template('table_index.html')


@app.route('/change_password')
def change_password_html():
    return render_template('change_password.html')


@app.route('/score_evaluation')
@jwt_required()
def score_evaluation():
    token = get_jwt_identity()
    userinfo = json.loads(token)["userinfo"]
    if userinfo["isSA"] is False and userinfo["isRJ"] is False and userinfo["isPJ"] is False:
        return render_template('no_access.html')
    return render_template('score_evaluation.html')


@app.route('/member-management')
@jwt_required()
def member_management():
    token = get_jwt_identity()
    userinfo = json.loads(token)["userinfo"]
    if userinfo["isSA"] is False:
        return render_template('no_access.html')
    return render_template('member_management.html')


@app.route('/data-import')
@jwt_required()
def data_import():
    token = get_jwt_identity()
    userinfo = json.loads(token)["userinfo"]
    if userinfo["isSA"] is False:
        return render_template('no_access.html')

    return render_template('data_import.html')


@app.route('/data-export')
@jwt_required()
def data_export():
    token = get_jwt_identity()
    userinfo = json.loads(token)["userinfo"]
    if userinfo["isSA"] is False and userinfo["isRJ"] is False:
        return render_template('no_access.html')

    return render_template('data_export.html')


# @app.route('/permission-settings')
# @jwt_required()
# def permission_settings():
#     return render_template('permission_settings.html')


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

@app.route('/edittable')
@jwt_required()
def edit_table():
    token = get_jwt_identity()
    userinfo = json.loads(token)["userinfo"]
    if userinfo["isSA"] is False:
        return render_template('no_access.html')

    # 从URL获取版本参数
    version = request.args.get('version')

    return render_template("edittable.html", version=version)


if __name__ == '__main__':
    #app.run('192.168.0.122', port=5000, debug=True)
    app.run('172.22.0.30', port=5000, debug=True)
    #app.run('192.168.0.209', port=5000, debug=True)
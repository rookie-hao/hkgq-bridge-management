# -*- coding: utf-8 -*-
"""港澳台侨管理库系统 - Flask 后端主程序"""

from flask import Flask, jsonify, request
import jwt
import pymysql
import logging
from datetime import datetime, timedelta
from functools import wraps
from config import Config
from models import init_db, User, Personnel, Policy, Activity

app = Flask(__name__)
app.config.from_object(Config)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库
init_db()


# ============ 全局错误处理 ============

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f'服务器错误: {str(error)}')
    return jsonify({'code': 50000, 'message': '服务器内部错误'}), 500


# ============ JWT 工具函数 ============

def generate_token(user_id, role):
    """生成 JWT Token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')


def decode_token(token):
    """解析 JWT Token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============ 鉴权装饰器 ============

def token_required(f):
    """Token 鉴权装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Token')
        if not token:
            return jsonify({'code': 40001, 'message': 'Token 缺失'}), 401
        payload = decode_token(token)
        if not payload:
            return jsonify({'code': 40002, 'message': 'Token 无效或已过期'}), 401
        return f(payload, *args, **kwargs)
    return decorated


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated(payload, *args, **kwargs):
        if not payload or payload.get('role') != 'admin':
            return jsonify({'code': 40003, 'message': '权限不足，仅管理员可操作'}), 403
        return f(payload, *args, **kwargs)
    return decorated


def _get_current_user_info(payload):
    """从 token payload 获取当前用户信息"""
    if not payload or not payload.get('user_id'):
        return None
    return User.find_by_id(payload['user_id'])


# ============ 认证 API（保留原有） ============

@app.route('/vue-admin-template/user/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 50000, 'message': '请求数据不能为空'})

        username = data.get('username', '').strip() if data.get('username') else ''
        password = data.get('password', '').strip() if data.get('password') else ''

        if not username or not password:
            return jsonify({'code': 50000, 'message': '用户名和密码不能为空'})

        user = User.find_by_username(username)
        if user and user['password'] == password:
            token = generate_token(user['id'], user['role'])
            logger.info(f'✅ 用户 {username} 登录成功')
            return jsonify({'code': 20000, 'data': {'token': token}})
        else:
            return jsonify({'code': 50000, 'message': '用户名或密码错误'}), 401
    except Exception as e:
        logger.error(f'❌ 登录异常: {str(e)}')
        return jsonify({'code': 50000, 'message': f'登录失败: {str(e)}'}), 500


@app.route('/vue-admin-template/user/info', methods=['GET'])
@token_required
def get_user_info(payload):
    """获取当前登录用户信息"""
    user = User.find_by_id(payload['user_id'])
    if user:
        return jsonify({
            'code': 20000,
            'data': {
                'roles': [user['role']],
                'name': user['name'],
                'avatar': user['avatar']
            }
        })
    return jsonify({'code': 50000, 'message': '用户不存在'})


@app.route('/vue-admin-template/user/logout', methods=['POST'])
def logout():
    """用户登出"""
    return jsonify({'code': 20000, 'data': 'success'})


@app.route('/vue-admin-template/user/register', methods=['POST'])
def register():
    """用户注册（公开接口）"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip() if data.get('username') else ''
        password = data.get('password', '').strip() if data.get('password') else ''

        if not username or not password:
            return jsonify({'code': 50000, 'message': '用户名和密码不能为空'})

        if len(username) < 2:
            return jsonify({'code': 50002, 'message': '用户名至少需要2个字符'})

        if len(password) < 6:
            return jsonify({'code': 50002, 'message': '密码不能少于6位'})

        if User.find_by_username(username):
            return jsonify({'code': 50001, 'message': '用户名已存在'})

        if User.find_by_name(username):
            return jsonify({'code': 50001, 'message': '该姓名已被其他用户使用'})

        user_id = User.create(username, password, 'user', username, '')
        logger.info(f'✅ 用户注册成功 - ID:{user_id}, 用户名:{username}')
        return jsonify({'code': 20000, 'data': {'id': user_id}})
    except Exception as e:
        logger.error(f'❌ 用户注册失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'注册失败: {str(e)}'}), 500


# ============ 用户管理 API（管理员） ============

@app.route('/vue-admin-template/user/list', methods=['GET'])
@token_required
@admin_required
def get_user_list(payload):
    """获取用户列表"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    username = request.args.get('username', '')
    role = request.args.get('role', '')
    result = User.get_all(page, limit, username, role)
    return jsonify({'code': 20000, 'data': result})


@app.route('/vue-admin-template/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_detail(payload, user_id):
    """获取用户详情"""
    user = User.find_by_id(user_id)
    if user:
        return jsonify({'code': 20000, 'data': user})
    return jsonify({'code': 50004, 'message': '用户不存在'})


@app.route('/vue-admin-template/user/create', methods=['POST'])
@token_required
@admin_required
def create_user(payload):
    """创建用户（管理员操作）"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip() if data.get('username') else ''
        password = data.get('password', '').strip() if data.get('password') else ''
        name = data.get('name', '').strip() if data.get('name') else ''
        role = data.get('role', 'user').strip()
        avatar = data.get('avatar', '').strip() if data.get('avatar') else ''

        if not username or not password:
            return jsonify({'code': 50002, 'message': '用户名和密码不能为空'})

        if len(username) < 2:
            return jsonify({'code': 50002, 'message': '用户名至少需要2个字符'})

        if User.find_by_username(username):
            return jsonify({'code': 50001, 'message': '用户名已存在'})

        if name and User.find_by_name(name):
            return jsonify({'code': 50001, 'message': '该姓名已被其他用户使用'})

        user_id = User.create(username, password, role, name, avatar)
        logger.info(f'✅ 新建用户成功 - ID:{user_id}, 用户名:{username}, 角色:{role}')
        return jsonify({'code': 20000, 'data': {'id': user_id}})
    except Exception as e:
        logger.error(f'❌ 新建用户失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'新建用户失败: {str(e)}'}), 500


@app.route('/vue-admin-template/user/update', methods=['POST'])
@token_required
@admin_required
def update_user(payload):
    """更新用户信息（管理员操作）"""
    try:
        data = request.get_json()
        user_id = data.get('id')
        if not user_id:
            return jsonify({'code': 50003, 'message': '用户ID不能为空'})

        target_user = User.find_by_id(user_id)
        if not target_user:
            return jsonify({'code': 50004, 'message': '用户不存在'})

        # 禁止修改 admin 管理员账号的用户名和角色
        if target_user['username'] == 'admin':
            if data.get('username') and data.get('username') != 'admin':
                return jsonify({'code': 50006, 'message': '无法修改 admin 管理员用户名'})
            if data.get('role') and data.get('role') != 'admin':
                return jsonify({'code': 50007, 'message': '无法修改 admin 管理员角色'})

        # 检查姓名是否被其他用户使用
        new_name = data.get('name')
        if new_name and new_name != target_user.get('name'):
            existing_user = User.find_by_name(new_name)
            if existing_user and existing_user['id'] != user_id:
                return jsonify({'code': 50001, 'message': '该姓名已被其他用户使用'})

        User.update(user_id, name=data.get('name'), password=data.get('password'),
                    role=data.get('role'), avatar=data.get('avatar'))
        logger.info(f'✅ 更新用户成功 - ID:{user_id}')
        return jsonify({'code': 20000, 'data': 'success'})
    except Exception as e:
        logger.error(f'❌ 更新用户失败: {str(e)}')
        return jsonify({'code': 50000, 'message': '更新用户失败'}), 500


@app.route('/vue-admin-template/user/delete', methods=['POST'])
@token_required
@admin_required
def delete_user(payload):
    """删除用户（管理员操作）"""
    try:
        data = request.get_json()
        user_id = data.get('id')
        if not user_id:
            return jsonify({'code': 50003, 'message': '用户ID不能为空'})

        # 禁止删除 admin 管理员账号
        conn = Config.get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT username FROM users WHERE id = %s', (user_id,))
        target_user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not target_user:
            return jsonify({'code': 50004, 'message': '用户不存在'})

        if target_user['username'] == 'admin':
            return jsonify({'code': 50005, 'message': '无法删除 admin 管理员账号'})

        if User.delete(user_id):
            logger.info(f'✅ 删除用户成功 - ID:{user_id}')
            return jsonify({'code': 20000, 'data': 'success'})
        return jsonify({'code': 50004, 'message': '用户不存在'})
    except Exception as e:
        logger.error(f'❌ 删除用户失败: {str(e)}')
        return jsonify({'code': 50000, 'message': '删除用户失败'}), 500


@app.route('/vue-admin-template/user/self-update', methods=['POST'])
@token_required
def update_self(payload):
    """用户更新个人信息"""
    try:
        data = request.get_json()
        user_id = payload.get('user_id')
        if not user_id:
            return jsonify({'code': 50003, 'message': '用户ID不能为空'})

        new_name = data.get('name')
        if new_name:
            current_user = User.find_by_id(user_id)
            if current_user and new_name != current_user.get('name'):
                existing_user = User.find_by_name(new_name)
                if existing_user and existing_user['id'] != user_id:
                    return jsonify({'code': 50001, 'message': '该姓名已被其他用户使用'})

        User.update(user_id, name=data.get('name'), password=data.get('password'),
                    avatar=data.get('avatar'))
        logger.info(f'✅ 用户更新个人信息成功 - ID:{user_id}')
        return jsonify({'code': 20000, 'data': 'success'})
    except Exception as e:
        logger.error(f'❌ 用户更新个人信息失败: {str(e)}')
        return jsonify({'code': 50000, 'message': '更新个人信息失败'}), 500


# ============ 人员信息管理 API ============

@app.route('/vue-admin-template/personnel/list', methods=['GET'])
@token_required
def get_personnel_list(payload):
    """获取人员列表（支持搜索、地区筛选、分页）"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        keyword = request.args.get('keyword', '')
        region = request.args.get('region', '')

        result = Personnel.get_all(page, limit, keyword, region)
        return jsonify({'code': 20000, 'data': result})
    except Exception as e:
        logger.error(f'❌ 获取人员列表失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取人员列表失败: {str(e)}'}), 500


@app.route('/vue-admin-template/personnel/detail', methods=['GET'])
@token_required
def get_personnel_detail(payload):
    """获取人员详情"""
    try:
        person_id = request.args.get('id')
        if not person_id:
            return jsonify({'code': 50003, 'message': '人员ID不能为空'})

        person = Personnel.get_by_id(int(person_id))
        if person:
            return jsonify({'code': 20000, 'data': person})
        return jsonify({'code': 50004, 'message': '人员不存在'})
    except Exception as e:
        logger.error(f'❌ 获取人员详情失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取人员详情失败: {str(e)}'}), 500


@app.route('/vue-admin-template/personnel/create', methods=['POST'])
@token_required
def create_personnel(payload):
    """新增人员信息"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip() if data.get('name') else ''
        if not name:
            return jsonify({'code': 50002, 'message': '姓名不能为空'})

        person_id = Personnel.create(
            name=name,
            gender=data.get('gender', ''),
            birth_date=data.get('birth_date'),
            id_number=data.get('id_number', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            region=data.get('region', ''),
            address=data.get('address', ''),
            occupation=data.get('occupation', ''),
            organization=data.get('organization', ''),
            remark=data.get('remark', '')
        )
        logger.info(f'✅ 新增人员成功 - ID:{person_id}, 姓名:{name}')
        return jsonify({'code': 20000, 'data': {'id': person_id}})
    except Exception as e:
        logger.error(f'❌ 新增人员失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'新增人员失败: {str(e)}'}), 500


@app.route('/vue-admin-template/personnel/update', methods=['POST'])
@token_required
def update_personnel(payload):
    """更新人员信息"""
    try:
        data = request.get_json()
        person_id = data.get('id')
        if not person_id:
            return jsonify({'code': 50003, 'message': '人员ID不能为空'})

        person = Personnel.get_by_id(int(person_id))
        if not person:
            return jsonify({'code': 50004, 'message': '人员不存在'})

        # 构建更新字段（仅传递前端传入的字段）
        update_fields = {}
        for field in ['name', 'gender', 'birth_date', 'id_number', 'phone', 'email',
                      'region', 'address', 'occupation', 'organization', 'remark']:
            if field in data:
                update_fields[field] = data[field]

        Personnel.update(int(person_id), **update_fields)
        logger.info(f'✅ 更新人员成功 - ID:{person_id}')
        return jsonify({'code': 20000, 'data': 'success'})
    except Exception as e:
        logger.error(f'❌ 更新人员失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'更新人员失败: {str(e)}'}), 500


@app.route('/vue-admin-template/personnel/delete', methods=['POST'])
@token_required
def delete_personnel(payload):
    """删除人员信息"""
    try:
        data = request.get_json()
        person_id = data.get('id')
        if not person_id:
            return jsonify({'code': 50003, 'message': '人员ID不能为空'})

        person = Personnel.get_by_id(int(person_id))
        if not person:
            return jsonify({'code': 50004, 'message': '人员不存在'})

        if Personnel.delete(int(person_id)):
            logger.info(f'✅ 删除人员成功 - ID:{person_id}')
            return jsonify({'code': 20000, 'data': 'success'})
        return jsonify({'code': 50004, 'message': '删除失败'})
    except Exception as e:
        logger.error(f'❌ 删除人员失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'删除人员失败: {str(e)}'}), 500


# ============ 政策文件管理 API ============

@app.route('/vue-admin-template/policy/list', methods=['GET'])
@token_required
def get_policy_list(payload):
    """获取政策文件列表（支持搜索、分类筛选、状态筛选、分页）"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        status = request.args.get('status', '')

        result = Policy.get_all(page, limit, keyword, category, status)
        return jsonify({'code': 20000, 'data': result})
    except Exception as e:
        logger.error(f'❌ 获取政策列表失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取政策列表失败: {str(e)}'}), 500


@app.route('/vue-admin-template/policy/detail', methods=['GET'])
@token_required
def get_policy_detail(payload):
    """获取政策文件详情"""
    try:
        policy_id = request.args.get('id')
        if not policy_id:
            return jsonify({'code': 50003, 'message': '政策ID不能为空'})

        policy = Policy.get_by_id(int(policy_id))
        if policy:
            return jsonify({'code': 20000, 'data': policy})
        return jsonify({'code': 50004, 'message': '政策文件不存在'})
    except Exception as e:
        logger.error(f'❌ 获取政策详情失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取政策详情失败: {str(e)}'}), 500


@app.route('/vue-admin-template/policy/create', methods=['POST'])
@token_required
def create_policy(payload):
    """新增政策文件"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip() if data.get('title') else ''
        if not title:
            return jsonify({'code': 50002, 'message': '标题不能为空'})

        policy_id = Policy.create(
            title=title,
            issuer=data.get('issuer', ''),
            publish_date=data.get('publish_date'),
            doc_number=data.get('doc_number', ''),
            summary=data.get('summary', ''),
            attachment_path=data.get('attachment_path', ''),
            category=data.get('category', ''),
            status=data.get('status', '有效')
        )
        logger.info(f'✅ 新增政策文件成功 - ID:{policy_id}, 标题:{title}')
        return jsonify({'code': 20000, 'data': {'id': policy_id}})
    except Exception as e:
        logger.error(f'❌ 新增政策文件失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'新增政策文件失败: {str(e)}'}), 500


@app.route('/vue-admin-template/policy/update', methods=['POST'])
@token_required
def update_policy(payload):
    """更新政策文件"""
    try:
        data = request.get_json()
        policy_id = data.get('id')
        if not policy_id:
            return jsonify({'code': 50003, 'message': '政策ID不能为空'})

        policy = Policy.get_by_id(int(policy_id))
        if not policy:
            return jsonify({'code': 50004, 'message': '政策文件不存在'})

        update_fields = {}
        for field in ['title', 'issuer', 'publish_date', 'doc_number', 'summary',
                      'attachment_path', 'category', 'status']:
            if field in data:
                update_fields[field] = data[field]

        Policy.update(int(policy_id), **update_fields)
        logger.info(f'✅ 更新政策文件成功 - ID:{policy_id}')
        return jsonify({'code': 20000, 'data': 'success'})
    except Exception as e:
        logger.error(f'❌ 更新政策文件失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'更新政策文件失败: {str(e)}'}), 500


@app.route('/vue-admin-template/policy/delete', methods=['POST'])
@token_required
def delete_policy(payload):
    """删除政策文件"""
    try:
        data = request.get_json()
        policy_id = data.get('id')
        if not policy_id:
            return jsonify({'code': 50003, 'message': '政策ID不能为空'})

        policy = Policy.get_by_id(int(policy_id))
        if not policy:
            return jsonify({'code': 50004, 'message': '政策文件不存在'})

        if Policy.delete(int(policy_id)):
            logger.info(f'✅ 删除政策文件成功 - ID:{policy_id}')
            return jsonify({'code': 20000, 'data': 'success'})
        return jsonify({'code': 50004, 'message': '删除失败'})
    except Exception as e:
        logger.error(f'❌ 删除政策文件失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'删除政策文件失败: {str(e)}'}), 500


# ============ 活动管理 API ============

@app.route('/vue-admin-template/activity/list', methods=['GET'])
@token_required
def get_activity_list(payload):
    """获取活动列表（支持搜索、类型筛选、状态筛选、分页）"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        keyword = request.args.get('keyword', '')
        activity_type = request.args.get('activity_type', '')
        status = request.args.get('status', '')

        result = Activity.get_all(page, limit, keyword, activity_type, status)
        return jsonify({'code': 20000, 'data': result})
    except Exception as e:
        logger.error(f'❌ 获取活动列表失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取活动列表失败: {str(e)}'}), 500


@app.route('/vue-admin-template/activity/detail', methods=['GET'])
@token_required
def get_activity_detail(payload):
    """获取活动详情"""
    try:
        activity_id = request.args.get('id')
        if not activity_id:
            return jsonify({'code': 50003, 'message': '活动ID不能为空'})

        activity = Activity.get_by_id(int(activity_id))
        if activity:
            return jsonify({'code': 20000, 'data': activity})
        return jsonify({'code': 50004, 'message': '活动不存在'})
    except Exception as e:
        logger.error(f'❌ 获取活动详情失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取活动详情失败: {str(e)}'}), 500


@app.route('/vue-admin-template/activity/create', methods=['POST'])
@token_required
def create_activity(payload):
    """新增活动"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip() if data.get('name') else ''
        if not name:
            return jsonify({'code': 50002, 'message': '活动名称不能为空'})

        activity_id = Activity.create(
            name=name,
            activity_type=data.get('activity_type', ''),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            location=data.get('location', ''),
            organizer=data.get('organizer', ''),
            max_participants=data.get('max_participants', 0),
            status=data.get('status', '未开始'),
            description=data.get('description', '')
        )
        logger.info(f'✅ 新增活动成功 - ID:{activity_id}, 名称:{name}')
        return jsonify({'code': 20000, 'data': {'id': activity_id}})
    except Exception as e:
        logger.error(f'❌ 新增活动失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'新增活动失败: {str(e)}'}), 500


@app.route('/vue-admin-template/activity/update', methods=['POST'])
@token_required
def update_activity(payload):
    """更新活动"""
    try:
        data = request.get_json()
        activity_id = data.get('id')
        if not activity_id:
            return jsonify({'code': 50003, 'message': '活动ID不能为空'})

        activity = Activity.get_by_id(int(activity_id))
        if not activity:
            return jsonify({'code': 50004, 'message': '活动不存在'})

        update_fields = {}
        for field in ['name', 'activity_type', 'start_time', 'end_time', 'location',
                      'organizer', 'max_participants', 'status', 'description']:
            if field in data:
                update_fields[field] = data[field]

        Activity.update(int(activity_id), **update_fields)
        logger.info(f'✅ 更新活动成功 - ID:{activity_id}')
        return jsonify({'code': 20000, 'data': 'success'})
    except Exception as e:
        logger.error(f'❌ 更新活动失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'更新活动失败: {str(e)}'}), 500


@app.route('/vue-admin-template/activity/delete', methods=['POST'])
@token_required
def delete_activity(payload):
    """删除活动"""
    try:
        data = request.get_json()
        activity_id = data.get('id')
        if not activity_id:
            return jsonify({'code': 50003, 'message': '活动ID不能为空'})

        activity = Activity.get_by_id(int(activity_id))
        if not activity:
            return jsonify({'code': 50004, 'message': '活动不存在'})

        if Activity.delete(int(activity_id)):
            logger.info(f'✅ 删除活动成功 - ID:{activity_id}')
            return jsonify({'code': 20000, 'data': 'success'})
        return jsonify({'code': 50004, 'message': '删除失败'})
    except Exception as e:
        logger.error(f'❌ 删除活动失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'删除活动失败: {str(e)}'}), 500


# ============ 统计看板 API ============

@app.route('/vue-admin-template/dashboard/overview', methods=['GET'])
@token_required
def get_dashboard_overview(payload):
    """统计看板 - 综合概览数据"""
    try:
        conn = Config.get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 用户总数
        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = cursor.fetchone()['count']

        # 人员总数
        cursor.execute('SELECT COUNT(*) as count FROM personnel')
        personnel_count = cursor.fetchone()['count']

        # 政策文件总数
        cursor.execute('SELECT COUNT(*) as count FROM policy')
        policy_count = cursor.fetchone()['count']

        # 活动总数
        cursor.execute('SELECT COUNT(*) as count FROM activity')
        activity_count = cursor.fetchone()['count']

        # 各地区人员数量统计
        cursor.execute('''
            SELECT region, COUNT(*) as count FROM personnel
            WHERE region != '' GROUP BY region ORDER BY count DESC
        ''')
        region_stats = cursor.fetchall()

        # 各分类政策文件数量
        cursor.execute('''
            SELECT category, COUNT(*) as count FROM policy
            WHERE category != '' GROUP BY category ORDER BY count DESC
        ''')
        policy_category_stats = cursor.fetchall()

        # 各状态政策文件数量
        cursor.execute('''
            SELECT status, COUNT(*) as count FROM policy
            WHERE status != '' GROUP BY status ORDER BY count DESC
        ''')
        policy_status_stats = cursor.fetchall()

        # 活动按类型统计
        cursor.execute('''
            SELECT activity_type, COUNT(*) as count FROM activity
            WHERE activity_type != '' GROUP BY activity_type ORDER BY count DESC
        ''')
        activity_type_stats = cursor.fetchall()

        # 活动按状态统计
        cursor.execute('''
            SELECT status, COUNT(*) as count FROM activity
            WHERE status != '' GROUP BY status ORDER BY count DESC
        ''')
        activity_status_stats = cursor.fetchall()

        # 最近活动列表（最新5条）
        cursor.execute('''
            SELECT id, name, activity_type, start_time, end_time, location, organizer, status
            FROM activity ORDER BY start_time DESC LIMIT 5
        ''')
        recent_activities = cursor.fetchall()

        # 有效政策数量
        cursor.execute("SELECT COUNT(*) as count FROM policy WHERE status = '有效'")
        active_policy_count = cursor.fetchone()['count']

        # 进行中活动数量
        cursor.execute("SELECT COUNT(*) as count FROM activity WHERE status = '进行中'")
        ongoing_activity_count = cursor.fetchone()['count']

        conn.close()

        logger.info('✅ 获取统计看板数据成功')
        return jsonify({
            'code': 20000,
            'data': {
                'users_count': users_count,
                'personnel_count': personnel_count,
                'policy_count': policy_count,
                'active_policy_count': active_policy_count,
                'activity_count': activity_count,
                'ongoing_activity_count': ongoing_activity_count,
                'region_stats': region_stats,
                'policy_category_stats': policy_category_stats,
                'policy_status_stats': policy_status_stats,
                'activity_type_stats': activity_type_stats,
                'activity_status_stats': activity_status_stats,
                'recent_activities': recent_activities
            }
        })
    except Exception as e:
        logger.error(f'❌ 获取统计看板数据失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取统计看板数据失败: {str(e)}'}), 500


@app.route('/vue-admin-template/dashboard/region-stats', methods=['GET'])
@token_required
def get_region_stats(payload):
    """统计看板 - 各地区人员数量统计"""
    try:
        conn = Config.get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute('''
            SELECT region, COUNT(*) as count FROM personnel
            WHERE region != '' GROUP BY region ORDER BY count DESC
        ''')
        stats = cursor.fetchall()

        conn.close()
        return jsonify({'code': 20000, 'data': stats})
    except Exception as e:
        logger.error(f'❌ 获取地区统计失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取地区统计失败: {str(e)}'}), 500


@app.route('/vue-admin-template/dashboard/policy-stats', methods=['GET'])
@token_required
def get_policy_stats(payload):
    """统计看板 - 政策文件分类与状态统计"""
    try:
        conn = Config.get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 按分类统计
        cursor.execute('''
            SELECT category, COUNT(*) as count FROM policy
            WHERE category != '' GROUP BY category ORDER BY count DESC
        ''')
        category_stats = cursor.fetchall()

        # 按状态统计
        cursor.execute('''
            SELECT status, COUNT(*) as count FROM policy
            GROUP BY status ORDER BY count DESC
        ''')
        status_stats = cursor.fetchall()

        conn.close()
        return jsonify({'code': 20000, 'data': {
            'category_stats': category_stats,
            'status_stats': status_stats
        }})
    except Exception as e:
        logger.error(f'❌ 获取政策统计失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取政策统计失败: {str(e)}'}), 500


@app.route('/vue-admin-template/dashboard/activity-stats', methods=['GET'])
@token_required
def get_activity_stats(payload):
    """统计看板 - 活动统计（按类型、按状态）"""
    try:
        conn = Config.get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 按类型统计
        cursor.execute('''
            SELECT activity_type, COUNT(*) as count FROM activity
            WHERE activity_type != '' GROUP BY activity_type ORDER BY count DESC
        ''')
        type_stats = cursor.fetchall()

        # 按状态统计
        cursor.execute('''
            SELECT status, COUNT(*) as count FROM activity
            GROUP BY status ORDER BY count DESC
        ''')
        status_stats = cursor.fetchall()

        # 最近活动列表
        cursor.execute('''
            SELECT id, name, activity_type, start_time, end_time, location, status
            FROM activity ORDER BY created_at DESC LIMIT 10
        ''')
        recent = cursor.fetchall()

        conn.close()
        return jsonify({'code': 20000, 'data': {
            'type_stats': type_stats,
            'status_stats': status_stats,
            'recent_activities': recent
        }})
    except Exception as e:
        logger.error(f'❌ 获取活动统计失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取活动统计失败: {str(e)}'}), 500


# ============ 数据库信息 API ============

@app.route('/vue-admin-template/db/stats', methods=['GET'])
@token_required
def get_db_stats(payload):
    """获取数据库统计信息"""
    conn = Config.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM personnel')
        personnel_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM policy')
        policy_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM activity')
        activity_count = cursor.fetchone()['count']

        stats = {
            'users': users_count,
            'personnel': personnel_count,
            'policy': policy_count,
            'activity': activity_count
        }

        logger.info(f'📊 实时统计 - 用户:{users_count}, 人员:{personnel_count}, 政策:{policy_count}, 活动:{activity_count}')
        return jsonify({'code': 20000, 'data': stats})
    except Exception as e:
        logger.error(f'❌ 获取数据库统计失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取统计失败: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/vue-admin-template/db/tables', methods=['GET'])
@token_required
def get_db_tables(payload):
    """查看数据库表数据"""
    table_name = request.args.get('table')
    if not table_name:
        return jsonify({'code': 50003, 'message': '请指定表名 (table=users/personnel/policy/activity)'})

    valid_tables = ['users', 'personnel', 'policy', 'activity']
    if table_name not in valid_tables:
        return jsonify({'code': 50003, 'message': f'无效的表名，可选: {valid_tables}'})

    conn = Config.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT * FROM {table_name} ORDER BY id DESC LIMIT 20')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = []
        for row in rows:
            item = {}
            for i, col in enumerate(columns):
                value = row[i]
                item[col] = str(value) if value else ''
            data.append(item)

        logger.info(f'📋 查看表 {table_name}: 返回 {len(data)} 条记录')
        return jsonify({
            'code': 20000,
            'data': {
                'table': table_name,
                'columns': columns,
                'records': data,
                'total_count': len(data)
            }
        })
    except Exception as e:
        logger.error(f'❌ 查看表数据错误: {str(e)}')
        return jsonify({'code': 50000, 'message': f'查询{table_name}表失败'}), 500
    finally:
        conn.close()


# ============ 启动入口 ============

if __name__ == '__main__':
    logger.info('🚀 港澳台侨管理库系统后端启动')
    logger.info(f'📦 数据库配置: mysql://{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}')
    app.run(host='0.0.0.0', port=5000, debug=True)

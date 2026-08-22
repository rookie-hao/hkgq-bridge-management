# -*- coding: utf-8 -*-
"""港澳台侨管理库系统 - Flask 后端主程序"""

from flask import Flask, jsonify, request
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from config import Config
from models import init_db, User, Personnel, Policy, Activity, Diary

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
    """Token 鉴权装饰器 - 支持 Authorization: Bearer、X-Token header 和 query param"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # 1. 优先检查 Authorization: Bearer <token>
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        # 2. 其次检查 X-Token header
        if not token:
            token = request.headers.get('X-Token')
        # 3. 最后检查 query parameter
        if not token:
            token = request.args.get('token')
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


# ============ 认证 API ============

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
    limit = int(request.args.get('page_size', request.args.get('limit', 10)))
    keyword = request.args.get('keyword', request.args.get('username', ''))
    role = request.args.get('role', '')
    result = User.get_all(page, limit, keyword, role)
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

        if target_user['username'] == 'admin':
            if data.get('username') and data.get('username') != 'admin':
                return jsonify({'code': 50006, 'message': '无法修改 admin 管理员用户名'})
            if data.get('role') and data.get('role') != 'admin':
                return jsonify({'code': 50007, 'message': '无法修改 admin 管理员角色'})

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

        conn = Config.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        target_user = cursor.fetchone()
        if target_user:
            target_user = dict(target_user)
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
        limit = int(request.args.get('page_size', request.args.get('limit', 10)))
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        region = request.args.get('region', '')

        result = Personnel.get_all(page, limit, keyword, region, category)
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
            remark=data.get('remark', ''),
            category=data.get('category', '')
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

        update_fields = {}
        for field in ['name', 'gender', 'birth_date', 'id_number', 'phone', 'email',
                      'region', 'address', 'occupation', 'organization', 'remark', 'category']:
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
        limit = int(request.args.get('page_size', request.args.get('limit', 10)))
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
        limit = int(request.args.get('page_size', request.args.get('limit', 10)))
        keyword = request.args.get('keyword', '')
        activity_type = request.args.get('category', request.args.get('activity_type', ''))
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


# ============ 工作日记管理 API ============

@app.route('/vue-admin-template/diary/list', methods=['GET'])
@token_required
def get_diary_list(payload):
    """获取工作日记列表（支持搜索、类型筛选、日期范围筛选、分页）"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', request.args.get('limit', 10)))
        keyword = request.args.get('keyword', '')
        work_type = request.args.get('work_type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        result = Diary.find_all(
            page=page,
            page_size=page_size,
            keyword=keyword,
            work_type=work_type,
            start_date=start_date,
            end_date=end_date
        )
        return jsonify({'code': 20000, 'data': result})
    except Exception as e:
        logger.error(f'❌ 获取日记列表失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取日记列表失败: {str(e)}'}), 500


@app.route('/vue-admin-template/diary/detail', methods=['GET'])
@token_required
def get_diary_detail(payload):
    """获取工作日记详情"""
    try:
        diary_id = request.args.get('id')
        if not diary_id:
            return jsonify({'code': 50003, 'message': '日记ID不能为空'})

        diary = Diary.find_by_id(int(diary_id))
        if diary:
            return jsonify({'code': 20000, 'data': diary})
        return jsonify({'code': 50004, 'message': '日记不存在'})
    except Exception as e:
        logger.error(f'❌ 获取日记详情失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取日记详情失败: {str(e)}'}), 500


@app.route('/vue-admin-template/diary/create', methods=['POST'])
@token_required
def create_diary(payload):
    """创建工作日记（需登录）"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip() if data.get('title') else ''
        if not title:
            return jsonify({'code': 50002, 'message': '标题不能为空'})

        data['user_id'] = payload['user_id']
        diary_id = Diary.create(data)
        logger.info(f'✅ 新增工作日记成功 - ID:{diary_id}, 标题:{title}')
        return jsonify({'code': 20000, 'data': {'id': diary_id}})
    except Exception as e:
        logger.error(f'❌ 新增工作日记失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'新增工作日记失败: {str(e)}'}), 500


@app.route('/vue-admin-template/diary/update', methods=['POST'])
@token_required
def update_diary(payload):
    """更新工作日记"""
    try:
        data = request.get_json()
        diary_id = data.get('id')
        if not diary_id:
            return jsonify({'code': 50003, 'message': '日记ID不能为空'})

        diary = Diary.find_by_id(int(diary_id))
        if not diary:
            return jsonify({'code': 50004, 'message': '日记不存在'})

        update_data = {}
        for field in ['title', 'content', 'work_type', 'work_date',
                      'location', 'participants', 'status', 'attachments']:
            if field in data:
                update_data[field] = data[field]

        Diary.update(int(diary_id), update_data)
        logger.info(f'✅ 更新工作日记成功 - ID:{diary_id}')
        return jsonify({'code': 20000, 'data': 'success'})
    except Exception as e:
        logger.error(f'❌ 更新工作日记失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'更新工作日记失败: {str(e)}'}), 500


@app.route('/vue-admin-template/diary/delete', methods=['POST'])
@token_required
def delete_diary(payload):
    """删除工作日记"""
    try:
        data = request.get_json()
        diary_id = data.get('id')
        if not diary_id:
            return jsonify({'code': 50003, 'message': '日记ID不能为空'})

        diary = Diary.find_by_id(int(diary_id))
        if not diary:
            return jsonify({'code': 50004, 'message': '日记不存在'})

        if Diary.delete(int(diary_id)):
            logger.info(f'✅ 删除工作日记成功 - ID:{diary_id}')
            return jsonify({'code': 20000, 'data': 'success'})
        return jsonify({'code': 50004, 'message': '删除失败'})
    except Exception as e:
        logger.error(f'❌ 删除工作日记失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'删除工作日记失败: {str(e)}'}), 500


@app.route('/vue-admin-template/diary/my', methods=['GET'])
@token_required
def get_my_diaries(payload):
    """获取当前用户的日记列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', request.args.get('limit', 10)))
        keyword = request.args.get('keyword', '')
        work_type = request.args.get('work_type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        result = Diary.find_all(
            page=page,
            page_size=page_size,
            keyword=keyword,
            work_type=work_type,
            user_id=payload['user_id'],
            start_date=start_date,
            end_date=end_date
        )
        return jsonify({'code': 20000, 'data': result})
    except Exception as e:
        logger.error(f'❌ 获取我的日记失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取我的日记失败: {str(e)}'}), 500


# ============ 统计看板 API ============

@app.route('/vue-admin-template/dashboard/overview', methods=['GET'])
@token_required
def get_dashboard_overview(payload):
    """统计看板 - 综合概览数据"""
    try:
        conn = Config.get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM personnel')
        personnel_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM policy')
        policy_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM activity')
        activity_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM diaries')
        diary_count = dict(cursor.fetchone())['count']

        cursor.execute('''
            SELECT region, COUNT(*) as count FROM personnel
            WHERE region != '' GROUP BY region ORDER BY count DESC
        ''')
        region_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT category, COUNT(*) as count FROM policy
            WHERE category != '' GROUP BY category ORDER BY count DESC
        ''')
        policy_category_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT status, COUNT(*) as count FROM policy
            WHERE status != '' GROUP BY status ORDER BY count DESC
        ''')
        policy_status_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT activity_type, COUNT(*) as count FROM activity
            WHERE activity_type != '' GROUP BY activity_type ORDER BY count DESC
        ''')
        activity_type_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT status, COUNT(*) as count FROM activity
            WHERE status != '' GROUP BY status ORDER BY count DESC
        ''')
        activity_status_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT id, name, activity_type, start_time, end_time, location, organizer, status
            FROM activity ORDER BY start_time DESC LIMIT 5
        ''')
        recent_activities = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) as count FROM policy WHERE status = '有效'")
        active_policy_count = dict(cursor.fetchone())['count']

        cursor.execute("SELECT COUNT(*) as count FROM activity WHERE status = '进行中'")
        ongoing_activity_count = dict(cursor.fetchone())['count']

        # 日记统计
        cursor.execute('''
            SELECT work_type, COUNT(*) as count FROM diaries
            WHERE work_type != '' GROUP BY work_type ORDER BY count DESC
        ''')
        diary_type_stats = [dict(r) for r in cursor.fetchall()]

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
                'diary_count': diary_count,
                'region_stats': region_stats,
                'policy_category_stats': policy_category_stats,
                'policy_status_stats': policy_status_stats,
                'activity_type_stats': activity_type_stats,
                'activity_status_stats': activity_status_stats,
                'recent_activities': recent_activities,
                'diary_type_stats': diary_type_stats
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
        cursor = conn.cursor()

        cursor.execute('''
            SELECT region, COUNT(*) as count FROM personnel
            WHERE region != '' GROUP BY region ORDER BY count DESC
        ''')
        stats = [{'name': dict(r)['region'], 'value': dict(r)['count']} for r in cursor.fetchall()]

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
        cursor = conn.cursor()

        cursor.execute('''
            SELECT category, COUNT(*) as count FROM policy
            WHERE category != '' GROUP BY category ORDER BY count DESC
        ''')
        category_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT status, COUNT(*) as count FROM policy
            GROUP BY status ORDER BY count DESC
        ''')
        status_stats = [dict(r) for r in cursor.fetchall()]

        CATEGORY_LABELS = {
            'visa': '签证政策', 'residence': '居留政策', 'employment': '就业政策',
            'education': '教育政策', 'investment': '投资政策', 'social': '社会保障'
        }
        chart_data = []
        for item in category_stats:
            cat = item.get('category', '')
            label = CATEGORY_LABELS.get(cat, cat)
            chart_data.append({'name': label, 'value': item['count']})

        conn.close()
        return jsonify({'code': 20000, 'data': chart_data})
    except Exception as e:
        logger.error(f'❌ 获取政策统计失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取政策统计失败: {str(e)}'}), 500


@app.route('/vue-admin-template/dashboard/activity-stats', methods=['GET'])
@token_required
def get_activity_stats(payload):
    """统计看板 - 活动统计（按类型、按状态）"""
    try:
        conn = Config.get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT activity_type, COUNT(*) as count FROM activity
            WHERE activity_type != '' GROUP BY activity_type ORDER BY count DESC
        ''')
        type_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT status, COUNT(*) as count FROM activity
            GROUP BY status ORDER BY count DESC
        ''')
        status_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT id, name, activity_type, start_time, end_time, location, status
            FROM activity ORDER BY created_at DESC LIMIT 10
        ''')
        recent = [dict(r) for r in cursor.fetchall()]

        TYPE_LABELS = {
            'summit': '峰会论坛', 'exchange': '交流活动', 'internship': '实习计划',
            'cultural': '文化交流', 'symposium': '学术研讨', 'social': '社交联谊'
        }
        chart_data = []
        for item in type_stats:
            t = item.get('activity_type', '')
            label = TYPE_LABELS.get(t, t)
            chart_data.append({'name': label, 'value': item['count']})

        conn.close()
        return jsonify({'code': 20000, 'data': chart_data})
    except Exception as e:
        logger.error(f'❌ 获取活动统计失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取活动统计失败: {str(e)}'}), 500


@app.route('/vue-admin-template/dashboard/diary-stats', methods=['GET'])
@token_required
def get_diary_stats(payload):
    """统计看板 - 工作日记统计"""
    try:
        conn = Config.get_db_connection()
        cursor = conn.cursor()

        # 按类型统计
        cursor.execute('''
            SELECT work_type, COUNT(*) as count FROM diaries
            WHERE work_type != '' GROUP BY work_type ORDER BY count DESC
        ''')
        type_stats = [dict(r) for r in cursor.fetchall()]

        # 按状态统计
        cursor.execute('''
            SELECT status, COUNT(*) as count FROM diaries
            GROUP BY status ORDER BY count DESC
        ''')
        status_stats = [dict(r) for r in cursor.fetchall()]

        # 最近10条日记
        cursor.execute('''
            SELECT d.id, d.title, d.work_type, d.work_date, d.location, d.status,
                   u.name as author_name
            FROM diaries d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.created_at DESC LIMIT 10
        ''')
        recent = [dict(r) for r in cursor.fetchall()]

        # 本月日记数量
        cursor.execute('''
            SELECT COUNT(*) as count FROM diaries
            WHERE work_date >= date('now', 'start of month')
        ''')
        monthly_count = dict(cursor.fetchone())['count']

        # 总数量
        cursor.execute('SELECT COUNT(*) as count FROM diaries')
        total_count = dict(cursor.fetchone())['count']

        conn.close()
        
        # 转换为前端饼图需要的格式 [{name, value}]
        WORK_TYPE_LABELS = {
            'daily': '日常工作', 'meeting': '会议记录', 'research': '调研报告',
            'visit': '外出走访', 'training': '学习培训', 'other': '其他'
        }
        chart_data = []
        for item in type_stats:
            wt = item.get('work_type', '')
            label = WORK_TYPE_LABELS.get(wt, wt)
            chart_data.append({'name': label, 'value': item['count']})
        
        return jsonify({'code': 20000, 'data': {
            'type_stats': type_stats,
            'status_stats': status_stats,
            'recent_diaries': recent,
            'recent': recent,
            'monthly_count': monthly_count,
            'total_count': total_count,
            'chart_data': chart_data
        }})
    except Exception as e:
        logger.error(f'❌ 获取日记统计失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'获取日记统计失败: {str(e)}'}), 500


# ============ 数据库信息 API ============

@app.route('/vue-admin-template/db/stats', methods=['GET'])
@token_required
def get_db_stats(payload):
    """获取数据库统计信息"""
    conn = Config.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM personnel')
        personnel_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM policy')
        policy_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM activity')
        activity_count = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM diaries')
        diary_count = dict(cursor.fetchone())['count']

        stats = {
            'users': users_count,
            'personnel': personnel_count,
            'policy': policy_count,
            'activity': activity_count,
            'diaries': diary_count
        }

        logger.info(f'📊 实时统计 - 用户:{users_count}, 人员:{personnel_count}, 政策:{policy_count}, 活动:{activity_count}, 日记:{diary_count}')
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
        return jsonify({'code': 50003, 'message': '请指定表名 (table=users/personnel/policy/activity/diaries)'})

    valid_tables = ['users', 'personnel', 'policy', 'activity', 'diaries']
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
            item = dict(row)
            for key in item:
                if item[key] is not None:
                    item[key] = str(item[key])
                else:
                    item[key] = ''
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


# ============ AI Chat 模块 ============

import os
import requests as http_requests
import json as json_lib

DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'
DEEPSEEK_MODELS = {
    'deepseek-chat': 'DeepSeek-V3（通用对话）',
    'deepseek-reasoner': 'DeepSeek-R1（深度推理）'
}

# 存储对话历史（内存中，简化方案）
chat_conversations = {}

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/vue-admin-template/chat/models', methods=['GET'])
@token_required
def get_chat_models(payload):
    """获取可用的 AI 模型列表"""
    models = [{'id': k, 'name': v} for k, v in DEEPSEEK_MODELS.items()]
    return jsonify({'code': 20000, 'data': models})


@app.route('/vue-admin-template/chat/upload', methods=['POST'])
@token_required
def chat_upload(payload):
    """上传文件用于 AI 分析"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': 50000, 'message': '未选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 50000, 'message': '文件名为空'})
        
        # 保存文件
        filename = f"{payload['user_id']}_{int(datetime.now().timestamp())}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 读取文件内容（支持 txt、csv、json）
        content = ''
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        
        if ext in ['txt', 'csv', 'md', 'log']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()[:10000]  # 最多读取前10000字符
        elif ext == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json_lib.load(f)
                content = json_lib.dumps(data, ensure_ascii=False, indent=2)[:10000]
        elif ext in ['xlsx', 'xls']:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(filepath, read_only=True)
                ws = wb.active
                rows = []
                for i, row in enumerate(ws.iter_rows(values_only=True)):
                    if i > 100:
                        break
                    rows.append([str(cell) if cell is not None else '' for cell in row])
                content = '\n'.join(['\t'.join(row) for row in rows])
            except Exception:
                content = f'[文件 {file.filename} 已上传，但不支持自动解析]'
        elif ext == 'pdf':
            content = f'[PDF文件 {file.filename} 已上传，共 {os.path.getsize(filepath)} 字节]'
        else:
            content = f'[文件 {file.filename} 已上传]'
        
        return jsonify({
            'code': 20000,
            'data': {
                'filename': file.filename,
                'filepath': filepath,
                'content': content,
                'size': os.path.getsize(filepath)
            }
        })
    except Exception as e:
        logger.error(f'文件上传失败: {str(e)}')
        return jsonify({'code': 50000, 'message': f'上传失败: {str(e)}'})


def _parse_mentions(message):
    """解析消息中的 @ 提及，返回匹配的数据模块列表"""
    mention_map = {
        '@人员管理': 'personnel',
        '@人员': 'personnel',
        '@政策法规': 'policy',
        '@政策': 'policy',
        '@交流活动': 'activity',
        '@活动': 'activity',
        '@工作日记': 'diary',
        '@日记': 'diary',
    }
    matched = set()
    for keyword, module in mention_map.items():
        if keyword in message:
            matched.add(module)
    return list(matched)


def _get_module_context(modules):
    """根据引用的模块，查询数据库并生成上下文文本"""
    contexts = []
    conn = Config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        if 'personnel' in modules:
            cursor.execute('SELECT name, gender, region, category, occupation, organization, phone FROM personnel LIMIT 100')
            rows = [dict(r) for r in cursor.fetchall()]
            if rows:
                import csv, io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
                contexts.append(f'【人员管理数据】共{len(rows)}条记录：\n{output.getvalue()[:8000]}')
        
        if 'policy' in modules:
            cursor.execute('SELECT title, issuer, publish_date, category, status FROM policy LIMIT 100')
            rows = [dict(r) for r in cursor.fetchall()]
            if rows:
                import csv, io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
                contexts.append(f'【政策法规数据】共{len(rows)}条记录：\n{output.getvalue()[:8000]}')
        
        if 'activity' in modules:
            cursor.execute('SELECT name, activity_type, start_time, end_time, location, status FROM activity LIMIT 100')
            rows = [dict(r) for r in cursor.fetchall()]
            if rows:
                import csv, io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
                contexts.append(f'【交流活动数据】共{len(rows)}条记录：\n{output.getvalue()[:8000]}')
        
        if 'diary' in modules:
            cursor.execute('SELECT title, work_type, work_date, location, status FROM diaries LIMIT 100')
            rows = [dict(r) for r in cursor.fetchall()]
            if rows:
                import csv, io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
                contexts.append(f'【工作日记数据】共{len(rows)}条记录：\n{output.getvalue()[:8000]}')
    finally:
        conn.close()
    
    return contexts


@app.route('/vue-admin-template/chat/send', methods=['POST'])
@token_required
def chat_send(payload):
    """发送消息给 AI"""
    try:
        api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        if not api_key:
            return jsonify({'code': 50000, 'message': 'AI 服务未配置，请联系管理员设置 DEEPSEEK_API_KEY'})
        
        data = request.get_json()
        model = data.get('model', 'deepseek-chat')
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', 'default')
        files = data.get('files', [])  # [{filename, content}]
        
        if not message:
            return jsonify({'code': 50000, 'message': '消息不能为空'})
        
        # 构建系统提示
        system_prompt = '你是港澳台侨管库系统的 AI 助手，专门负责港澳台侨事务管理工作。你可以回答政策问题、分析数据、撰写报告、提供建议。请用中文回答，语气专业但友好。'
        
        # 如果是对话模式，获取历史消息
        if conversation_id not in chat_conversations:
            chat_conversations[conversation_id] = []
        
        messages = [{'role': 'system', 'content': system_prompt}]
        
        # 解析 @ 提及并注入数据上下文
        mentions = _parse_mentions(message)
        if mentions:
            contexts = _get_module_context(mentions)
            for ctx in contexts:
                messages.append({'role': 'system', 'content': ctx})
        
        # 添加文件内容
        for f in files:
            if f.get('content'):
                messages.append({
                    'role': 'system',
                    'content': f'用户上传了文件 [{f["filename"]}]，内容如下：\n\n{f["content"][:5000]}'
                })
        
        # 添加历史消息（最近20条）
        history = chat_conversations[conversation_id][-20:]
        messages.extend(history)
        
        # 添加当前用户消息
        messages.append({'role': 'user', 'content': message})
        
        # 调用 DeepSeek API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        api_payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 4096,
            'stream': False
        }
        
        response = http_requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=api_payload,
            timeout=120
        )
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', f'API 错误 {response.status_code}')
            return jsonify({'code': 50000, 'message': f'AI 服务异常: {error_msg}'})
        
        result = response.json()
        ai_message = result['choices'][0]['message']['content']
        
        # 保存对话历史
        chat_conversations[conversation_id].append({'role': 'user', 'content': message})
        chat_conversations[conversation_id].append({'role': 'assistant', 'content': ai_message})
        
        # 限制历史长度
        if len(chat_conversations[conversation_id]) > 40:
            chat_conversations[conversation_id] = chat_conversations[conversation_id][-40:]
        
        return jsonify({
            'code': 20000,
            'data': {
                'reply': ai_message,
                'model': model,
                'conversation_id': conversation_id
            }
        })
    except http_requests.exceptions.Timeout:
        return jsonify({'code': 50000, 'message': 'AI 响应超时，请稍后重试'})
    except Exception as e:
        logger.error(f'AI 对话异常: {str(e)}')
        return jsonify({'code': 50000, 'message': f'对话失败: {str(e)}'})


@app.route('/vue-admin-template/chat/clear', methods=['POST'])
@token_required
def chat_clear(payload):
    """清空对话历史"""
    data = request.get_json() or {}
    conversation_id = data.get('conversation_id', 'default')
    if conversation_id in chat_conversations:
        del chat_conversations[conversation_id]
    return jsonify({'code': 20000, 'data': 'success'})


# ============ 生产模式：托管前端静态文件 ============
import os
from flask import send_from_directory

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')

@app.route('/')
def serve_index():
    index_path = os.path.join(STATIC_DIR, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(STATIC_DIR, 'index.html')
    return jsonify({'code': 20000, 'message': '港澳台侨管库系统 API 运行中', 'data': {'status': 'ok'}})

@app.route('/vue-admin-template/uploads/<path:filename>')
def serve_uploads(filename):
    """提供上传文件（头像等）的静态访问"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/<path:path>')
def serve_static(path):
    # 跳过 API 路由（已有专门的处理函数）
    file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(STATIC_DIR, path)
    # 非 API、非静态文件的路径，返回 index.html（SPA hash 路由）
    index_path = os.path.join(STATIC_DIR, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(STATIC_DIR, 'index.html')
    return jsonify({'code': 404, 'message': 'Not Found'}), 404


# ============ 启动入口 ============

if __name__ == '__main__':
    logger.info('🚀 港澳台侨管理库系统后端启动')
    if Config.is_turso_enabled():
        logger.info('📦 数据库配置: Turso 云数据库')
    else:
        logger.info(f'📦 数据库配置: SQLite - {Config.SQLITE_DB_PATH}')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


@app.route('/vue-admin-template/user/upload-avatar', methods=['POST'])
@token_required
def upload_avatar(payload):
    """上传用户头像"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': 50000, 'message': '未选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 50000, 'message': '文件名为空'})
        
        # 只允许图片格式
        allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed:
            return jsonify({'code': 50000, 'message': '只支持图片格式 (png/jpg/jpeg/gif/webp/svg)'})
        
        # 保存头像
        filename = f"avatar_{payload['user_id']}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 更新用户头像字段
        avatar_url = f"/vue-admin-template/uploads/{filename}"
        User.update(payload['user_id'], avatar=avatar_url)
        
        logger.info(f'✅ 用户 {payload["user_id"]} 上传头像成功')
        return jsonify({'code': 20000, 'data': {'avatar_url': avatar_url}})
    except Exception as e:
        logger.error(f'❌ 上传头像失败: {str(e)}')
        return jsonify({'code': 50000, 'message': '上传失败'}), 500

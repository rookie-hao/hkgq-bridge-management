# -*- coding: utf-8 -*-
"""港澳台侨管理库系统 - 数据模型"""

import sqlite3
import logging
import re
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)


# ============ 工具函数 ============

def _to_datetime(value):
    """
    统一转换各种时间格式为 DATETIME 格式字符串 'YYYY-MM-DD HH:MM:SS'。
    返回 None 表示使用当前时间。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        # 尝试解析 ISO 8601 格式
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            pass
        # 尝试解析常见日期格式
        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})',
            r'(\d{4})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2}):(\d{2})',
            r'(\d{4})-(\d{2})-(\d{2})',
        ]
        for pattern in patterns:
            match = re.match(pattern, v)
            if match:
                groups = match.groups()
                if len(groups) == 6:
                    return f'{groups[0]}-{groups[1]}-{groups[2]} {groups[3]}:{groups[4]}:{groups[5]}'
                elif len(groups) == 3:
                    return f'{groups[0]}-{groups[1]}-{groups[2]} 00:00:00'
        if 'T' in v:
            v = v.replace('T', ' ')
        return v
    return value


def _row_to_dict(row):
    """将 sqlite3.Row 转换为 dict"""
    if row is None:
        return None
    return dict(row)


def _rows_to_list(rows):
    """将 sqlite3.Row 列表转换为 dict 列表"""
    return [dict(r) for r in rows]


def get_db_connection():
    """获取数据库连接（模块级函数，方便各模型调用）"""
    try:
        connection = sqlite3.connect(Config.SQLITE_DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        logger.error(f'数据库连接错误: {str(e)}')
        raise


# ============ 数据库初始化 ============

def init_db():
    """初始化数据库表结构并插入默认数据"""
    try:
        connection = get_db_connection()
        with connection:
            cursor = connection.cursor()

            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    name VARCHAR(50),
                    avatar VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 人员信息表：侨胞/港澳台人员
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personnel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    gender VARCHAR(10) DEFAULT '',
                    birth_date DATE DEFAULT NULL,
                    id_number VARCHAR(50) DEFAULT '',
                    phone VARCHAR(30) DEFAULT '',
                    email VARCHAR(100) DEFAULT '',
                    region VARCHAR(30) DEFAULT '',
                    address VARCHAR(255) DEFAULT '',
                    occupation VARCHAR(100) DEFAULT '',
                    organization VARCHAR(200) DEFAULT '',
                    remark TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 政策文件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS policy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(255) NOT NULL,
                    issuer VARCHAR(200) DEFAULT '',
                    publish_date DATE DEFAULT NULL,
                    doc_number VARCHAR(100) DEFAULT '',
                    summary TEXT,
                    attachment_path VARCHAR(500) DEFAULT '',
                    category VARCHAR(30) DEFAULT '',
                    status VARCHAR(20) DEFAULT '有效',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 活动管理表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    activity_type VARCHAR(30) DEFAULT '',
                    start_time DATETIME DEFAULT NULL,
                    end_time DATETIME DEFAULT NULL,
                    location VARCHAR(255) DEFAULT '',
                    organizer VARCHAR(100) DEFAULT '',
                    max_participants INT DEFAULT 0,
                    status VARCHAR(20) DEFAULT '未开始',
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 插入默认管理员账号
            cursor.execute('SELECT COUNT(*) as count FROM users')
            result = cursor.fetchone()
            if result['count'] == 0:
                cursor.executemany('''
                    INSERT INTO users (username, password, role, name, avatar, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', [
                    ('admin', '111111', 'admin', '管理员', '', '2026-06-22 14:58:00'),
                    ('test', '111111', 'user', '测试用户', '', '2026-06-22 14:58:30'),
                ])

            # 插入示例人员数据
            cursor.execute('SELECT COUNT(*) as count FROM personnel')
            result = cursor.fetchone()
            if result['count'] == 0:
                personnel_data = [
                    ('陈志明', '男', '1975-03-15', 'H12345678', '+852-9876-5432', 'chen@example.com',
                     '香港', '香港特别行政区九龙城区', '商人', '香港潮州商会', '热心侨务工作'),
                    ('林美玲', '女', '1988-07-22', 'M55667788', '+853-6655-4433', 'lin@example.com',
                     '澳门', '澳门特别行政区新桥区', '律师', '澳门妇女联合总会', ''),
                    ('王建宏', '男', '1965-11-08', '台湾居民来往大陆通行证T1234567', '+886-2-2345-6789', 'wang@example.com',
                     '台湾', '台湾台北市大安区', '教授', '台湾同乡会', '致力于两岸文化交流'),
                    ('李秀英', '女', '1990-01-30', '美国护照US9876543', '+1-212-555-0123', 'li@example.com',
                     '海外侨胞', '美国纽约法拉盛', '工程师', '纽约华人华侨联合会', '华人社区活跃成员'),
                    ('张伟强', '男', '1982-09-12', '香港身份证A123456(7)', '+852-6123-4567', 'zhang@example.com',
                     '香港', '香港特别行政区湾仔区', '医生', '香港医学会', ''),
                ]
                cursor.executemany('''
                    INSERT INTO personnel (name, gender, birth_date, id_number, phone, email, region, address, occupation, organization, remark)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', personnel_data)

            # 插入示例政策文件数据
            cursor.execute('SELECT COUNT(*) as count FROM policy')
            result = cursor.fetchone()
            if result['count'] == 0:
                policy_data = [
                    ('关于进一步加强为侨服务工作的意见', '国务院侨务办公室', '2023-06-15', '国侨发〔2023〕12号',
                     '为进一步做好为侨服务工作，保障海外侨胞和归侨侨眷合法权益，提出以下意见...', '', '惠侨政策', '有效'),
                    ('港澳居民在内地求学就业若干政策措施', '国务院港澳事务办公室', '2023-09-01', '港澳办发〔2023〕8号',
                     '为便利港澳居民在内地学习、就业、创业，现将有关政策措施通知如下...', '', '涉港政策', '有效'),
                    ('台湾同胞投资保护法实施细则（修订）', '国务院台湾事务办公室', '2022-12-01', '国台发〔2022〕15号',
                     '根据《中华人民共和国台湾同胞投资保护法》，制定本实施细则...', '', '涉台政策', '有效'),
                    ('澳门特别行政区参与"一带一路"建设指导意见', '国务院港澳事务办公室', '2024-01-20', '港澳办发〔2024〕2号',
                     '支持澳门发挥独特优势，积极参与"一带一路"建设...', '', '涉澳政策', '有效'),
                    ('海外侨胞参与国内创新创业支持办法', '国务院侨务办公室', '2023-03-10', '国侨发〔2023〕5号',
                     '鼓励和支持海外侨胞回国创新创业，提供政策扶持和资金引导...', '', '惠侨政策', '待生效'),
                ]
                cursor.executemany('''
                    INSERT INTO policy (title, issuer, publish_date, doc_number, summary, attachment_path, category, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', policy_data)

            # 插入示例活动数据
            cursor.execute('SELECT COUNT(*) as count FROM activity')
            result = cursor.fetchone()
            if result['count'] == 0:
                activity_data = [
                    ('2024年海外侨胞新春联谊会', '交流会', '2024-02-10 14:00:00', '2024-02-10 17:00:00',
                     '北京人民大会堂', '李明', 200, '已结束', '邀请海外侨胞代表共庆新春，共话发展。'),
                    ('港澳台青年创新创业座谈会', '座谈会', '2024-05-15 09:00:00', '2024-05-15 17:00:00',
                     '深圳前海深港青年梦工场', '王芳', 80, '已结束', '围绕港澳台青年在内地创业发展进行交流。'),
                    ('粤港澳大湾区文化交流节', '文化节', '2024-08-01 10:00:00', '2024-08-03 18:00:00',
                     '广州天河体育中心', '张伟', 500, '未开始', '展示粤港澳三地文化特色，促进文化交流与融合。'),
                    ('侨胞专场人才招聘会', '招聘会', '2024-06-20 09:00:00', '2024-06-20 16:00:00',
                     '上海国际会议中心', '刘静', 300, '进行中', '为归国侨胞提供高质量就业机会。'),
                    ('两岸青年夏令营', '其他', '2024-07-10 08:00:00', '2024-07-15 18:00:00',
                     '厦门大学', '陈华', 150, '未开始', '组织两岸青年开展文化参访与交流活动。'),
                ]
                cursor.executemany('''
                    INSERT INTO activity (name, activity_type, start_time, end_time, location, organizer, max_participants, status, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', activity_data)

        logger.info('✅ 数据库初始化完成 - 港澳台侨管理库系统')
    except Exception as e:
        logger.error(f'❌ 数据库初始化错误: {str(e)}')
        raise
    finally:
        if 'connection' in locals():
            connection.close()


# ============ User 模型 ============

class User:
    """用户模型"""

    @staticmethod
    def find_by_username(username):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def find_by_id(user_id):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id, username, role, name, avatar FROM users WHERE id = ?', (user_id,))
                return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def find_by_name(name):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
                return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(username, password, role='user', name=None, avatar=None):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO users (username, password, role, name, avatar)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password, role, name or username, avatar or ''))
                connection.commit()
                return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def get_all(page=1, limit=10, username='', role=''):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                query = 'SELECT id, username, role, name, avatar, created_at FROM users WHERE 1=1'
                params = []
                if username:
                    query += ' AND username LIKE ?'
                    params.append(f'%{username}%')
                if role:
                    query += ' AND role = ?'
                    params.append(role)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                all_users = _rows_to_list(cursor.fetchall())
                total = len(all_users)
                start = (page - 1) * limit
                users_page = all_users[start:start + limit]
                return {'total': total, 'items': users_page}
        finally:
            connection.close()

    @staticmethod
    def update(user_id, name=None, password=None, role=None, avatar=None):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                user = User.find_by_id(user_id)
                if not user:
                    return None
                updates = []
                params = []
                if name is not None:
                    updates.append('name=?')
                    params.append(name)
                if password is not None:
                    updates.append('password=?')
                    params.append(password)
                if role is not None:
                    updates.append('role=?')
                    params.append(role)
                if avatar is not None:
                    updates.append('avatar=?')
                    params.append(avatar)
                if updates:
                    params.append(user_id)
                    cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id=?', params)
                    connection.commit()
                return user_id
        finally:
            connection.close()

    @staticmethod
    def delete(user_id):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                connection.commit()
                return cursor.rowcount > 0
        finally:
            connection.close()


# ============ Personnel 模型：港澳台侨人员信息 ============

class Personnel:
    """港澳台侨人员信息模型"""

    @staticmethod
    def get_all(page=1, limit=10, keyword='', region=''):
        """获取人员列表，支持关键词搜索和地区筛选，分页"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where = 'WHERE 1=1'
                params = []
                if keyword:
                    where += ' AND (name LIKE ? OR phone LIKE ? OR organization LIKE ? OR address LIKE ?)'
                    like_kw = f'%{keyword}%'
                    params.extend([like_kw, like_kw, like_kw, like_kw])
                if region:
                    where += ' AND region = ?'
                    params.append(region)

                cursor.execute(f'SELECT COUNT(*) as total FROM personnel {where}', params)
                total = cursor.fetchone()['total']

                offset = (page - 1) * limit
                cursor.execute(f'''
                    SELECT * FROM personnel {where}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', params + [limit, offset])
                items = _rows_to_list(cursor.fetchall())

                return {'total': total, 'items': items}
        finally:
            connection.close()

    @staticmethod
    def get_by_id(person_id):
        """根据ID获取人员详情"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM personnel WHERE id = ?', (person_id,))
                return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(name, gender='', birth_date=None, id_number='', phone='', email='',
               region='', address='', occupation='', organization='', remark=''):
        """创建人员记录"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO personnel (name, gender, birth_date, id_number, phone, email,
                                           region, address, occupation, organization, remark)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, gender, birth_date, id_number, phone, email,
                      region, address, occupation, organization, remark))
                connection.commit()
                return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(person_id, **kwargs):
        """更新人员信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                person = Personnel.get_by_id(person_id)
                if not person:
                    return None

                updatable = ['name', 'gender', 'birth_date', 'id_number', 'phone', 'email',
                             'region', 'address', 'occupation', 'organization', 'remark']
                updates = []
                params = []
                for field in updatable:
                    if field in kwargs and kwargs[field] is not None:
                        updates.append(f'{field}=?')
                        params.append(kwargs[field])

                if updates:
                    params.append(person_id)
                    cursor.execute(f'UPDATE personnel SET {", ".join(updates)} WHERE id=?', params)
                    connection.commit()
                return person_id
        finally:
            connection.close()

    @staticmethod
    def delete(person_id):
        """删除人员记录"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM personnel WHERE id = ?', (person_id,))
                connection.commit()
                return cursor.rowcount > 0
        finally:
            connection.close()


# ============ Policy 模型：政策文件 ============

class Policy:
    """港澳台侨政策文件模型"""

    @staticmethod
    def get_all(page=1, limit=10, keyword='', category='', status=''):
        """获取政策列表，支持关键词搜索、分类筛选、状态筛选，分页"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where = 'WHERE 1=1'
                params = []
                if keyword:
                    where += ' AND (title LIKE ? OR issuer LIKE ? OR doc_number LIKE ?)'
                    like_kw = f'%{keyword}%'
                    params.extend([like_kw, like_kw, like_kw])
                if category:
                    where += ' AND category = ?'
                    params.append(category)
                if status:
                    where += ' AND status = ?'
                    params.append(status)

                cursor.execute(f'SELECT COUNT(*) as total FROM policy {where}', params)
                total = cursor.fetchone()['total']

                offset = (page - 1) * limit
                cursor.execute(f'''
                    SELECT * FROM policy {where}
                    ORDER BY publish_date DESC, created_at DESC
                    LIMIT ? OFFSET ?
                ''', params + [limit, offset])
                items = _rows_to_list(cursor.fetchall())

                return {'total': total, 'items': items}
        finally:
            connection.close()

    @staticmethod
    def get_by_id(policy_id):
        """根据ID获取政策详情"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM policy WHERE id = ?', (policy_id,))
                return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(title, issuer='', publish_date=None, doc_number='', summary='',
               attachment_path='', category='', status='有效'):
        """创建政策文件记录"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO policy (title, issuer, publish_date, doc_number, summary,
                                        attachment_path, category, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, issuer, publish_date, doc_number, summary,
                      attachment_path, category, status))
                connection.commit()
                return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(policy_id, **kwargs):
        """更新政策文件信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                policy = Policy.get_by_id(policy_id)
                if not policy:
                    return None

                updatable = ['title', 'issuer', 'publish_date', 'doc_number', 'summary',
                             'attachment_path', 'category', 'status']
                updates = []
                params = []
                for field in updatable:
                    if field in kwargs and kwargs[field] is not None:
                        updates.append(f'{field}=?')
                        params.append(kwargs[field])

                if updates:
                    params.append(policy_id)
                    cursor.execute(f'UPDATE policy SET {", ".join(updates)} WHERE id=?', params)
                    connection.commit()
                return policy_id
        finally:
            connection.close()

    @staticmethod
    def delete(policy_id):
        """删除政策文件记录"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM policy WHERE id = ?', (policy_id,))
                connection.commit()
                return cursor.rowcount > 0
        finally:
            connection.close()


# ============ Activity 模型：活动管理 ============

class Activity:
    """港澳台侨活动管理模型"""

    @staticmethod
    def get_all(page=1, limit=10, keyword='', activity_type='', status=''):
        """获取活动列表，支持关键词搜索、类型筛选、状态筛选，分页"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                where = 'WHERE 1=1'
                params = []
                if keyword:
                    where += ' AND (name LIKE ? OR location LIKE ? OR organizer LIKE ?)'
                    like_kw = f'%{keyword}%'
                    params.extend([like_kw, like_kw, like_kw])
                if activity_type:
                    where += ' AND activity_type = ?'
                    params.append(activity_type)
                if status:
                    where += ' AND status = ?'
                    params.append(status)

                cursor.execute(f'SELECT COUNT(*) as total FROM activity {where}', params)
                total = cursor.fetchone()['total']

                offset = (page - 1) * limit
                cursor.execute(f'''
                    SELECT * FROM activity {where}
                    ORDER BY start_time DESC, created_at DESC
                    LIMIT ? OFFSET ?
                ''', params + [limit, offset])
                items = _rows_to_list(cursor.fetchall())

                return {'total': total, 'items': items}
        finally:
            connection.close()

    @staticmethod
    def get_by_id(activity_id):
        """根据ID获取活动详情"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM activity WHERE id = ?', (activity_id,))
                return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(name, activity_type='', start_time=None, end_time=None, location='',
               organizer='', max_participants=0, status='未开始', description=''):
        """创建活动记录"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                parsed_start = _to_datetime(start_time)
                parsed_end = _to_datetime(end_time)
                cursor.execute('''
                    INSERT INTO activity (name, activity_type, start_time, end_time, location,
                                          organizer, max_participants, status, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, activity_type, parsed_start, parsed_end, location,
                      organizer, max_participants, status, description))
                connection.commit()
                return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(activity_id, **kwargs):
        """更新活动信息"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                activity = Activity.get_by_id(activity_id)
                if not activity:
                    return None

                updatable = ['name', 'activity_type', 'start_time', 'end_time', 'location',
                             'organizer', 'max_participants', 'status', 'description']
                updates = []
                params = []
                for field in updatable:
                    if field in kwargs and kwargs[field] is not None:
                        if field in ('start_time', 'end_time'):
                            val = _to_datetime(kwargs[field])
                        else:
                            val = kwargs[field]
                        updates.append(f'{field}=?')
                        params.append(val)

                if updates:
                    params.append(activity_id)
                    cursor.execute(f'UPDATE activity SET {", ".join(updates)} WHERE id=?', params)
                    connection.commit()
                return activity_id
        finally:
            connection.close()

    @staticmethod
    def delete(activity_id):
        """删除活动记录"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM activity WHERE id = ?', (activity_id,))
                connection.commit()
                return cursor.rowcount > 0
        finally:
            connection.close()

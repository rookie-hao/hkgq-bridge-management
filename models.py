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
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            pass
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
    if row is None:
        return None
    return dict(row)


def _rows_to_list(rows):
    return [dict(r) for r in rows]


def get_db_connection():
    """获取数据库连接 - 委托给 Config 统一处理"""
    return Config.get_db_connection()


def _safe_sync(connection):
    """写入操作后，安全地将更改推送到 Turso 云数据库"""
    if Config.is_turso_enabled():
        try:
            connection.sync()
        except Exception:
            pass


# ============ 数据库初始化 ============

def init_db():
    """初始化数据库表结构并插入默认数据"""
    connection = None
    try:
        connection = get_db_connection()
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

        # 人员信息表
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

        # 为 personnel 表添加 category 字段（如果不存在）
        cursor.execute("PRAGMA table_info(personnel)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'category' not in columns:
            cursor.execute("ALTER TABLE personnel ADD COLUMN category VARCHAR(30) DEFAULT ''")

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

        # 工作日记表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                work_type VARCHAR(30) DEFAULT '日常工作',
                work_date DATE DEFAULT NULL,
                location VARCHAR(255) DEFAULT '',
                participants VARCHAR(500) DEFAULT '',
                status VARCHAR(20) DEFAULT 'published',
                attachments TEXT DEFAULT '',
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

        connection.commit()
        # 系统配置表
        SystemConfig.init_table()
        logger.info('✅ 数据库表结构初始化完成')

        # 如果是 Turso，推送本地更改到云端
        if Config.is_turso_enabled():
            try:
                connection.sync()
                logger.info('✅ 数据已同步到 Turso 云数据库')
            except Exception as sync_err:
                logger.warning(f'Turso sync 失败: {sync_err}')

        # 自动填充样例数据（当各表为空时）
        try:
            from seed_data import seed_all
            seed_all(connection)
            # Turso: 推送样例数据到云端
            if Config.is_turso_enabled():
                try:
                    connection.sync()
                except Exception:
                    pass
        except Exception as seed_err:
            logger.warning(f'样例数据填充跳过: {seed_err}')

        logger.info('✅ 数据库初始化完成 - 港澳台侨管理库系统')
    except Exception as e:
        logger.error(f'❌ 数据库初始化错误: {str(e)}')
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()


# ============ User 模型 ============

class User:
    """用户模型"""

    @staticmethod
    def find_by_username(username):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def find_by_id(user_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT id, username, role, name, avatar FROM users WHERE id = ?', (user_id,))
            return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def find_by_name(name):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
            return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(username, password, role='user', name=None, avatar=None):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, role, name, avatar)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, role, name or username, avatar or ''))
            connection.commit()
            _safe_sync(connection)
            return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def get_all(page=1, limit=10, username='', role=''):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            query = 'SELECT id, username, role, name, avatar, created_at FROM users WHERE 1=1'
            params = []
            if username:
                query += ' AND (username LIKE ? OR name LIKE ?)'
                params.extend([f'%{username}%', f'%{username}%'])
            if role:
                query += ' AND role = ?'
                params.append(role)
            query += ' ORDER BY created_at DESC'
            cursor.execute(query, params)
            all_users = _rows_to_list(cursor.fetchall())
            total = len(all_users)
            start = (page - 1) * limit
            users_page = all_users[start:start + limit]
            return {'total': total, 'list': users_page}
        finally:
            connection.close()

    @staticmethod
    def update(user_id, name=None, password=None, role=None, avatar=None):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
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
            _safe_sync(connection)
            return user_id
        finally:
            connection.close()

    @staticmethod
    def delete(user_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            connection.commit()
            _safe_sync(connection)
            return cursor.rowcount > 0
        finally:
            connection.close()


# ============ Personnel 模型 ============

class Personnel:
    """港澳台侨人员信息模型"""

    @staticmethod
    def get_all(page=1, limit=10, keyword='', region='', category=''):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            where = 'WHERE 1=1'
            params = []
            if keyword:
                where += ' AND (name LIKE ? OR phone LIKE ? OR organization LIKE ? OR address LIKE ? OR remark LIKE ?)'
                like_kw = f'%{keyword}%'
                params.extend([like_kw, like_kw, like_kw, like_kw, like_kw])
            if region:
                where += ' AND region = ?'
                params.append(region)
            if category:
                where += ' AND category = ?'
                params.append(category)
            cursor.execute(f'SELECT COUNT(*) as total FROM personnel {where}', params)
            total = cursor.fetchone()['total']
            offset = (page - 1) * limit
            cursor.execute(f'''
                SELECT * FROM personnel {where}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', params + [limit, offset])
            items = _rows_to_list(cursor.fetchall())
            return {'total': total, 'list': items}
        finally:
            connection.close()

    @staticmethod
    def get_by_id(person_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM personnel WHERE id = ?', (person_id,))
            return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(name, gender='', birth_date=None, id_number='', phone='', email='',
               region='', address='', occupation='', organization='', remark='', category=''):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO personnel (name, gender, birth_date, id_number, phone, email,
                                       region, address, occupation, organization, remark, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, gender, birth_date, id_number, phone, email,
                  region, address, occupation, organization, remark, category))
            connection.commit()
            _safe_sync(connection)
            return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(person_id, **kwargs):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            person = Personnel.get_by_id(person_id)
            if not person:
                return None
            updatable = ['name', 'gender', 'birth_date', 'id_number', 'phone', 'email',
                         'region', 'address', 'occupation', 'organization', 'remark', 'category']
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
            _safe_sync(connection)
            return person_id
        finally:
            connection.close()

    @staticmethod
    def delete(person_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM personnel WHERE id = ?', (person_id,))
            connection.commit()
            _safe_sync(connection)
            return cursor.rowcount > 0
        finally:
            connection.close()


# ============ Policy 模型 ============

class Policy:
    """港澳台侨政策文件模型"""

    @staticmethod
    def get_all(page=1, limit=10, keyword='', category='', status=''):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
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
            return {'total': total, 'list': items}
        finally:
            connection.close()

    @staticmethod
    def get_by_id(policy_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM policy WHERE id = ?', (policy_id,))
            return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(title, issuer='', publish_date=None, doc_number='', summary='',
               attachment_path='', category='', status='有效'):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO policy (title, issuer, publish_date, doc_number, summary,
                                    attachment_path, category, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, issuer, publish_date, doc_number, summary,
                  attachment_path, category, status))
            connection.commit()
            _safe_sync(connection)
            return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(policy_id, **kwargs):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
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
            _safe_sync(connection)
            return policy_id
        finally:
            connection.close()

    @staticmethod
    def delete(policy_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM policy WHERE id = ?', (policy_id,))
            connection.commit()
            _safe_sync(connection)
            return cursor.rowcount > 0
        finally:
            connection.close()


# ============ Activity 模型 ============

class Activity:
    """港澳台侨活动管理模型"""

    @staticmethod
    def get_all(page=1, limit=10, keyword='', activity_type='', status=''):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
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
            return {'total': total, 'list': items}
        finally:
            connection.close()

    @staticmethod
    def get_by_id(activity_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM activity WHERE id = ?', (activity_id,))
            return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(name, activity_type='', start_time=None, end_time=None, location='',
               organizer='', max_participants=0, status='未开始', description=''):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            parsed_start = _to_datetime(start_time)
            parsed_end = _to_datetime(end_time)
            cursor.execute('''
                INSERT INTO activity (name, activity_type, start_time, end_time, location,
                                      organizer, max_participants, status, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, activity_type, parsed_start, parsed_end, location,
                  organizer, max_participants, status, description))
            connection.commit()
            _safe_sync(connection)
            return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(activity_id, **kwargs):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
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
            _safe_sync(connection)
            return activity_id
        finally:
            connection.close()

    @staticmethod
    def delete(activity_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM activity WHERE id = ?', (activity_id,))
            connection.commit()
            _safe_sync(connection)
            return cursor.rowcount > 0
        finally:
            connection.close()


# ============ Diary 模型：工作日记 ============

class Diary:
    """工作日记模型"""
    TABLE = 'diaries'

    @staticmethod
    def init_table():
        """确保 diaries 表存在"""
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS diaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    work_type VARCHAR(30) DEFAULT '日常工作',
                    work_date DATE DEFAULT NULL,
                    location VARCHAR(255) DEFAULT '',
                    participants VARCHAR(500) DEFAULT '',
                    status VARCHAR(20) DEFAULT 'published',
                    attachments TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            connection.commit()
            _safe_sync(connection)
        finally:
            connection.close()

    @staticmethod
    def find_all(page=1, page_size=10, keyword='', work_type='', user_id=None, start_date='', end_date=''):
        """分页查询，支持关键词搜索、类型筛选、日期范围筛选"""
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            where = 'WHERE 1=1'
            params = []
            if keyword:
                where += ' AND (d.title LIKE ? OR d.content LIKE ? OR d.location LIKE ? OR d.participants LIKE ?)'
                like_kw = f'%{keyword}%'
                params.extend([like_kw, like_kw, like_kw, like_kw])
            if work_type:
                where += ' AND d.work_type = ?'
                params.append(work_type)
            if user_id is not None:
                where += ' AND d.user_id = ?'
                params.append(user_id)
            if start_date:
                where += ' AND d.work_date >= ?'
                params.append(start_date)
            if end_date:
                where += ' AND d.work_date <= ?'
                params.append(end_date)

            cursor.execute(f'SELECT COUNT(*) as total FROM diaries d {where}', params)
            total = cursor.fetchone()['total']

            offset = (page - 1) * page_size
            cursor.execute(f'''
                SELECT d.*, u.name as author_name
                FROM diaries d
                LEFT JOIN users u ON d.user_id = u.id
                {where}
                ORDER BY d.work_date DESC, d.created_at DESC
                LIMIT ? OFFSET ?
            ''', params + [page_size, offset])
            items = _rows_to_list(cursor.fetchall())
            return {'total': total, 'list': items}
        finally:
            connection.close()

    @staticmethod
    def find_by_id(diary_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT d.*, u.name as author_name
                FROM diaries d
                LEFT JOIN users u ON d.user_id = u.id
                WHERE d.id = ?
            ''', (diary_id,))
            return _row_to_dict(cursor.fetchone())
        finally:
            connection.close()

    @staticmethod
    def create(data):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO diaries (user_id, title, content, work_type, work_date,
                                     location, participants, status, attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('user_id'),
                data.get('title', ''),
                data.get('content', ''),
                data.get('work_type', '日常工作'),
                data.get('work_date'),
                data.get('location', ''),
                data.get('participants', ''),
                data.get('status', 'published'),
                data.get('attachments', '')
            ))
            connection.commit()
            _safe_sync(connection)
            return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(diary_id, data):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            diary = Diary.find_by_id(diary_id)
            if not diary:
                return None
            updatable = ['title', 'content', 'work_type', 'work_date',
                         'location', 'participants', 'status', 'attachments']
            updates = []
            params = []
            for field in updatable:
                if field in data and data[field] is not None:
                    updates.append(f'{field}=?')
                    params.append(data[field])
            if updates:
                updates.append('updated_at=?')
                params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                params.append(diary_id)
                cursor.execute(f'UPDATE diaries SET {", ".join(updates)} WHERE id=?', params)
                connection.commit()
            _safe_sync(connection)
            return diary_id
        finally:
            connection.close()

    @staticmethod
    def delete(diary_id):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM diaries WHERE id = ?', (diary_id,))
            connection.commit()
            _safe_sync(connection)
            return cursor.rowcount > 0
        finally:
            connection.close()

    @staticmethod
    def count(keyword='', work_type='', user_id=None):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            where = 'WHERE 1=1'
            params = []
            if keyword:
                where += ' AND (title LIKE ? OR content LIKE ?)'
                like_kw = f'%{keyword}%'
                params.extend([like_kw, like_kw])
            if work_type:
                where += ' AND work_type = ?'
                params.append(work_type)
            if user_id is not None:
                where += ' AND user_id = ?'
                params.append(user_id)
            cursor.execute(f'SELECT COUNT(*) as total FROM diaries {where}', params)
            return cursor.fetchone()['total']
        finally:
            connection.close()


# ============ SystemConfig 模型 ============

class SystemConfig:
    """系统配置模型 - 存储系统名称、Logo 等可配置项"""

    @staticmethod
    def init_table():
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT DEFAULT '',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 插入默认配置
            defaults = [
                ('system_name', '港澳台侨管库系统'),
                ('system_subtitle', 'Hong Kong, Macau, Taiwan & Overseas Chinese Management System'),
                ('sidebar_title', '港澳台侨管库'),
                ('logo_text', '侨'),
                ('logo_image', ''),
            ]
            for key, value in defaults:
                cursor.execute(
                    'INSERT INTO system_config (key, value) VALUES (?, ?) '
                    'ON CONFLICT(key) DO UPDATE SET value=excluded.value '
                    'WHERE system_config.value = \'\' OR system_config.value IS NULL',
                    (key, value)
                )
            connection.commit()
            _safe_sync(connection)
        finally:
            connection.close()

    @staticmethod
    def get_all():
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT key, value FROM system_config')
            rows = cursor.fetchall()
            return {row['key']: row['value'] for row in rows}
        finally:
            connection.close()

    @staticmethod
    def set_value(key, value):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO system_config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            ''', (key, value, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            connection.commit()
            _safe_sync(connection)
            return True
        finally:
            connection.close()

    @staticmethod
    def set_many(config_dict):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for key, value in config_dict.items():
                cursor.execute('''
                    INSERT INTO system_config (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                ''', (key, value, now))
            connection.commit()
            _safe_sync(connection)
            return True
        finally:
            connection.close()

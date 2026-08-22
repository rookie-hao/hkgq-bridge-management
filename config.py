# -*- coding: utf-8 -*-
"""港澳台侨管理库系统 - 配置文件"""

import os
import sqlite3
import logging

logger = logging.getLogger(__name__)


# ============ Turso/libsql 适配层 ============
# libsql_experimental 不支持 row_factory，需要用包装类让返回结果像 sqlite3.Row 一样
# 支持 dict(row)、row['key']、row[index] 等用法

class _DictRow:
    """模拟 sqlite3.Row，支持 dict() 转换和键/索引访问"""
    __slots__ = ('_data', '_keys')

    def __init__(self, keys, values):
        self._data = dict(zip(keys, values))
        self._keys = list(keys)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[self._keys[key]]
        return self._data[key]

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    def keys(self):
        return list(self._keys)

    def __repr__(self):
        return f'<DictRow {self._data}>'

    def __eq__(self, other):
        if isinstance(other, _DictRow):
            return self._data == other._data
        return False

    def __hash__(self):
        return hash(tuple(sorted(self._data.items())))


class _TursoCursor:
    """包装 libsql cursor，自动将 tuple 结果转为 _DictRow"""

    def __init__(self, raw_cursor):
        self._cursor = raw_cursor
        self.description = None
        self.rowcount = -1

    def execute(self, sql, params=None):
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        self.description = self._cursor.description
        try:
            self.rowcount = self._cursor.rowcount
        except Exception:
            pass
        return self

    def executemany(self, sql, params_list):
        self._cursor.executemany(sql, params_list)
        self.description = self._cursor.description
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self.description:
            keys = [d[0] for d in self.description]
            return _DictRow(keys, row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self.description:
            keys = [d[0] for d in self.description]
            return [_DictRow(keys, row) for row in rows]
        return rows

    def fetchmany(self, size=None):
        if size is not None:
            rows = self._cursor.fetchmany(size)
        else:
            rows = self._cursor.fetchmany()
        if self.description:
            keys = [d[0] for d in self.description]
            return [_DictRow(keys, row) for row in rows]
        return rows

    def close(self):
        self._cursor.close()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid


class _TursoConnection:
    """包装 libsql 连接，cursor 自动返回 _DictRow"""

    def __init__(self, raw_conn):
        self._raw = raw_conn

    def cursor(self):
        return _TursoCursor(self._raw.cursor())

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql, params_list):
        cur = self.cursor()
        cur.executemany(sql, params_list)
        return cur

    def commit(self):
        self._raw.commit()

    def rollback(self):
        try:
            self._raw.rollback()
        except Exception:
            pass

    def close(self):
        try:
            self._raw.close()
        except Exception:
            pass

    def sync(self):
        """推送/拉取 Turso 云端数据"""
        try:
            self._raw.sync()
        except Exception as e:
            logger.warning(f'Turso sync 异常: {e}')


class Config:
    """应用配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hkgq-secret-key-change-in-production'

    # 数据库配置
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hkgq.db')
    TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
    TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'hkgq-jwt-secret-key-change-in-production'
    JWT_EXPIRATION_HOURS = 24

    @staticmethod
    def is_turso_enabled():
        """是否启用 Turso 云数据库"""
        return bool(Config.TURSO_DATABASE_URL and Config.TURSO_AUTH_TOKEN)

    @staticmethod
    def get_db_connection():
        """获取数据库连接（优先 Turso，回退本地 SQLite）"""
        try:
            if Config.is_turso_enabled():
                try:
                    import libsql_experimental as libsql
                    # 使用临时本地副本 + 远程 Turso 同步
                    local_path = '/tmp/hkgq_replica.db'
                    raw_conn = libsql.connect(
                        local_path,
                        sync_url=Config.TURSO_DATABASE_URL,
                        auth_token=Config.TURSO_AUTH_TOKEN
                    )
                    raw_conn.sync()  # 拉取最新数据
                    return _TursoConnection(raw_conn)
                except ImportError:
                    logger.warning('libsql_experimental 未安装，回退本地 SQLite')
                except Exception as e:
                    logger.warning(f'Turso 连接失败: {e}，回退本地 SQLite')

            # 本地 SQLite 回退
            connection = sqlite3.connect(Config.SQLITE_DB_PATH)
            connection.row_factory = sqlite3.Row
            return connection
        except Exception as e:
            logger.error(f'❌ 数据库连接失败: {str(e)}')
            raise

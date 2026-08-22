# -*- coding: utf-8 -*-
"""港澳台侨管理库系统 - 配置文件"""

import os
import sqlite3
import logging

logger = logging.getLogger(__name__)


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
                    conn = libsql.connect(
                        local_path,
                        sync_url=Config.TURSO_DATABASE_URL,
                        auth_token=Config.TURSO_AUTH_TOKEN
                    )
                    conn.sync()  # 拉取最新数据
                    conn.row_factory = sqlite3.Row
                    return conn
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

# -*- coding: utf-8 -*-
"""港澳台侨管理库系统 - 配置文件"""

import os
import sqlite3


class Config:
    """应用配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hkgq-secret-key-change-in-production'

    # SQLite 数据库配置
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hkgq.db')

    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'hkgq-jwt-secret-key-change-in-production'
    JWT_EXPIRATION_HOURS = 24

    @staticmethod
    def get_db_connection():
        """获取数据库连接"""
        try:
            connection = sqlite3.connect(Config.SQLITE_DB_PATH)
            connection.row_factory = sqlite3.Row
            return connection
        except Exception as e:
            print(f'❌ 数据库连接失败: {str(e)}')
            raise

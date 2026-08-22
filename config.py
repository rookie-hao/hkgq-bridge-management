# -*- coding: utf-8 -*-
"""港澳台侨管理库系统 - 配置文件"""

import os
import pymysql


class Config:
    """应用配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hkgq-secret-key-change-in-production'

    # MySQL 数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '1234'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'hkgq_management'

    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'hkgq-jwt-secret-key-change-in-production'
    JWT_EXPIRATION_HOURS = 24

    @staticmethod
    def get_db_connection():
        """获取数据库连接"""
        try:
            connection = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            print(f'❌ 数据库连接失败: {str(e)}')
            raise

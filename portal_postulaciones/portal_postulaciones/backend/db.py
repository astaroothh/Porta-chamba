import pymysql
import pymysql.cursors
import config


def get_conn():
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

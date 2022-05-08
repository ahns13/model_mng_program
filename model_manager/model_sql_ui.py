import importlib
import sys

cx_Oracle = importlib.import_module("cx_Oracle")
username = "ADMIN"
password = "AhnCsh181223"
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")
cursor = conn.cursor()


def get_model_list(v_page_no, v_page_size,  v_input_name=""):
    sql = "SELECT A.NAME, A.BIRTH_DATE, A.TEL, A.INSTA_ID, A.DATA_DATE, B.FILE_NAME, B.DIR_ROUTE\n"
    sql += "     , COUNT(1) OVER () AS TOTAL_CNT\n"
    sql += "  FROM MODEL_PROFILE A\n"
    sql += "       LEFT OUTER JOIN MODEL_INFO B\n"
    sql += "         ON A.KEY = B.KEY\n"
    if v_input_name:
        sql += " WHERE A.NAME LIKE '%" + v_input_name + "%'\n"
    sql += " ORDER BY A.NAME\n"
    sql += "OFFSET " + str(v_page_size) + "*(" + str(v_page_no) + "-1) ROWS\n"
    sql += " FETCH NEXT " + str(v_page_size) + " ROWS ONLY"
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        return result
        cursor.close()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        cursor.close()
        conn.close()
        sys.exit()



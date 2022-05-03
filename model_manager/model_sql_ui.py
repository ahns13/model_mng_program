import importlib
import sys

cx_Oracle = importlib.import_module("cx_Oracle")
username = "ADMIN"
password = "AhnCsh181223"
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")
cursor = conn.cursor()


def get_model_list(v_page_no, v_input_name=""):
    sql = "SELECT A.NAME, A.BIRTH_DATE, A.HEIGHT, A.TEL, A.INSTA_ID, A.DATA_DATE\n"
    sql += "  FROM MODEL_PROFILE A\n"
    if v_input_name:
        sql += " WHERE A.NAME LIKE '%" + v_input_name + "%'\n"
    sql += " ORDER BY A.NAME\n"
    sql += "OFFSET 20*(1-" + str(v_page_no) + ") ROWS\n"
    sql += " FETCH NEXT 20 ROWS ONLY"
    print(sql)
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



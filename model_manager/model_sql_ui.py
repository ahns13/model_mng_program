import importlib

cx_Oracle = importlib.import_module("cx_Oracle")
username = "ADMIN"
password = "AhnCsh181223"
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")
cursor = conn.cursor()


def get_model_list(v_page_no, v_input_name=None):
    check_sql = ("SELECT A.NAME, A.BIRTH_DATE, A.HEIGHT, A.TEL, A.INSTA_ID, A.DATA_DATE"
                 "  FROM MODEL_PROFILE A"
                 " WHERE A.NAME " + "LIKE '%" + v_input_name + "%'" if v_input_name else "= '" + v_input_name + "'"
                 " ORDER BY A.NAME"
                 "OFFSET 20*(1-" + v_page_no + " ROWS)"
                 " FETCH NEXT 20 ROWS ONLY")
    cursor.execute(check_sql)
    result = cursor.fetchall()
    return result


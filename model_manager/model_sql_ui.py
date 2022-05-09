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
    sql += "       LEFT OUTER JOIN HOBBYNSPEC C\n"
    sql += "         ON A.KEY = C.KEY\n"
    sql += "       LEFT OUTER JOIN CAREER D\n"
    sql += "         ON A.KEY = D.KEY\n"
    sql += "       LEFT OUTER JOIN CONTACT E\n"
    sql += "         ON A.KEY = E.KEY\n"
    sql += "       LEFT OUTER JOIN CNTR_AMOUNT F\n"
    sql += "         ON A.KEY = F.KEY\n"
    sql += "       LEFT OUTER JOIN CNTR_OTHER G\n"
    sql += "         ON A.KEY = G.KEY\n"
    sql += " WHERE 1=1\n"
    if v_input_name:
        sql += "   AND A.NAME LIKE '%" + v_input_name + "%'\n"
    if v_hobbynspec:
        sql += "   AND C.HOBBYNSPEC LIKE '%" + v_hobbynspec + "%'\n"
    if v_careers:
        sql += "   AND D.CAREER_TYPE = '" + v_career_type + "'\n"
        sql += "   AND D.CAREERS LIKE '%" + v_careers + "%'\n"
    if v_contact:
        sql += "   AND E."+v_contact[0]+" LIKE '%" + v_contact[1] + "%'\n"
    if v_contract:
        sql += "   AND E."+v_contract[0]+" LIKE '%" + v_contract[1] + "%'\n"
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


def get_comboBox_list_a(v_combo_type)"
    sql = "SELECT TABLE_NAME, COMBO_DETAIL_TYPE, COL_NAME, COL_DISPLAY_NAME\n"
    sql += "  FROM COMBO_MAP_LIST\n"
    sql += " WHERE COMBO_TYPE = '" + v_combo_type + "'\n"
    sql += " ORDER BY SORT_ORDER"
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
        
def get_comboBox_list_career(v_no)"
    sql = "SELECT TABLE_NAME, 'CAREER_TYPE' AS LOOKUP_COL_NAME\n"
    sql += "     , 'CAREER_TYPE' AS SEARCH_COL_NAME, COL_DISPLAY_NAME\n"
    sql += "  FROM COMBO_MAP_LIST\n"
    sql += " WHERE COMBO_TYPE = 'CAREER'\n"
    sql += "   AND COMBO_DETAIL_TYPE IN ('DATA', 'DATA" + str(v_no) + "')\n"
    sql += " ORDER BY SORT_ORDER"
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

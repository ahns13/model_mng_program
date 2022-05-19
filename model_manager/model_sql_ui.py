import importlib
import sys

cx_Oracle = importlib.import_module("cx_Oracle")
# username = "ADMIN"
# password = "AhnCsh181223"
# conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")
conn = cx_Oracle.connect(user="AHN_TEST", password="AHN_TEST3818", dsn="cogdw_144")


def condition_add(v_tab_alias, v_srch_dir):
    v_sql = ""
    for key in v_srch_dir.keys():
        srch_items = v_srch_dir[key][2]
        insert_check = 0
        srch_sql, srch_sql2 = "", ""
        if srch_items["s"]:
            for idx, item in enumerate(srch_items["s"]):
                insert_check += 1
                srch_sql += (" OR UPPER(" if idx else "UPPER(") + v_tab_alias + "." + v_srch_dir[key][0] + ") " + \
                            v_srch_dir[key][1] + (" UPPER('%" + item + "%')" if v_srch_dir[key][1] == "LIKE" else " UPPER('" + item + "')")
        if srch_items["ge"]:
            insert_check += 1
            srch_sql2 += ("        OR (" if srch_sql else "        (") + v_tab_alias + "." + v_srch_dir[key][0] + " >= "+ srch_items["ge"]
        if srch_items["le"]:
            insert_check += 1
            if srch_sql:
                srch_sql2 += " AND " if srch_items["ge"] else "        OR ("
            else:
                srch_sql2 += " AND " if srch_items["ge"] else "        ("
            srch_sql2 += v_tab_alias + "." + v_srch_dir[key][0] + " <= "+ srch_items["le"] + ")"
        elif srch_items["ge"]:
            srch_sql2 += ")"
        if insert_check:
            v_sql += "   AND (" + srch_sql + ("\n" + srch_sql2 if srch_sql2 else "") + ")\n"
    return v_sql


def condition_career(v_tab_alias, v_srch_dir):
    v_sql = ""
    for key in v_srch_dir.keys():
        type_list = v_srch_dir[key]
        if type_list:
            for item in type_list:
                if key == "전체":
                    v_sql += (" OR " if v_sql else "") + "UPPER(CAREERS) LIKE '%" + item + "%'"
                else:
                    v_sql += (" OR " if v_sql else "") + v_tab_alias + ".CAREER_TYPE = '" + key + "' AND UPPER(CAREERS) LIKE '%" + item + "%'"
    if v_sql:
        return "   AND (" + v_sql + ")\n"
    else:
        return ""


def sql_execute(v_cur_cursor, v_sql, **kwargs):
    # ins_data = None, execute_only = False, key = None
    try:
        if "execute_many" in kwargs and kwargs["execute_maney"]:
            v_cur_cursor.executemany(v_sql, kwargs["ins_data"])
        elif "ins_data" in kwargs:
            v_cur_cursor.execute(v_sql, kwargs["ins_data"])
        else:
            v_cur_cursor.execute(v_sql)
        if not kwargs or ("execute_only" in kwargs and not kwargs["execute_only"]):
            return v_cur_cursor.fetchall()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(v_sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        if kwargs and "key" in kwargs:
            flagStatus(kwargs["key"], 0)  # 점유중인 데이터를 해제
        v_cur_cursor.close()
        conn.close()
        sys.exit()


def get_model_list(v_page_no, v_page_size,  v_search_dir={}):
    cursor = conn.cursor()
    sql = "SELECT A.NAME, A.BIRTH_DATE, A.TEL, A.INSTA_ID, A.DATA_DATE, A.FILE_NAME, A.DIR_ROUTE, A.FOLDER_PATH, COUNT(A.NAME) OVER () AS TOTAL_CNT, A.KEY\n"
    sql += "  FROM (\n"
    sql += "SELECT DISTINCT A.NAME, A.BIRTH_DATE, A.TEL, A.INSTA_ID, A.DATA_DATE, B.FILE_NAME, B.DIR_ROUTE, B.FOLDER_PATH, A.KEY\n"
    sql += "  FROM MODEL_PROFILE A\n"
    sql += "       LEFT OUTER JOIN MODEL_INFO B ON A.KEY = B.KEY\n"
    sql += "       LEFT OUTER JOIN HOBBYNSPEC C ON A.KEY = C.KEY\n"
    sql += "       LEFT OUTER JOIN CAREER D ON A.KEY = D.KEY\n"
    sql += "       LEFT OUTER JOIN CONTACT E ON A.KEY = E.KEY\n"
    sql += "       LEFT OUTER JOIN CNTR_AMOUNT F ON A.KEY = F.KEY\n"
    sql += "       LEFT OUTER JOIN CNTR_OTHER G ON A.KEY = G.KEY\n"
    sql += " WHERE 1=1\n"
    srch_profile = v_search_dir["PROFILE"]
    sql += condition_add("A", srch_profile)
    srch_hobbynspec = v_search_dir["HOBBYNSPEC"]
    sql += condition_add("C", srch_hobbynspec)
    srch_career = v_search_dir["CAREER"]
    sql += condition_career("D", srch_career)
    srch_contact = v_search_dir["CONTACT"]
    sql += condition_add("E", srch_contact)
    srch_amount= v_search_dir["CONTRACT"]
    sql += condition_add("F", srch_amount)
    srch_other = v_search_dir["OTHER"]
    sql += condition_add("G", srch_other)
    sql += "       ) A\n"
    sql += " ORDER BY A.NAME\n"
    sql += "OFFSET " + str(v_page_size) + "*(" + str(v_page_no) + "-1) ROWS\n"
    sql += " FETCH NEXT " + str(v_page_size) + " ROWS ONLY"
    result = sql_execute(cursor, sql)
    cursor.close()
    return result


def get_comboBox_list_a(v_combo_type):
    cursor = conn.cursor()
    sql = "SELECT TABLE_NAME, COMBO_DETAIL_TYPE, COL_NAME, COL_DISPLAY_NAME, COMPARE_OPERATOR, DATA_TYPE\n"
    sql += "  FROM COMBO_MAP_LIST\n"
    sql += " WHERE COMBO_TYPE = '" + v_combo_type + "'\n"
    sql += " ORDER BY SORT_ORDER"
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        item_list, item_table_map, comboBox_dir = [], {}, {}
        for row in result:
            item_list.append(row[3])
            comboBox_dir[row[3]] = [row[2], row[4], {"s": [], "ge": "", "le": ""}, row[5]]
            # 테이블명: { 항목명: [칼럼명, 연산자, {검색목록}, 데이터유형] }
        cursor.close()
        return [item_list, comboBox_dir]
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        cursor.close()
        conn.close()
        sys.exit()


def get_comboBox_list_career():
    # DATA_TYPE : only string
    cursor = conn.cursor()
    sql = "SELECT COL_DISPLAY_NAME\n"
    sql += "  FROM COMBO_MAP_LIST\n"
    sql += " WHERE COMBO_TYPE = 'CAREER'\n"
    sql += "   AND COMBO_DETAIL_TYPE = 'DATA'\n"
    sql += " ORDER BY SORT_ORDER"
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        item_list, comboBox_dir = [], {}
        for row in result:
            item_list.append(row[0])
            comboBox_dir[row[0]] = []
        cursor.close()
        return [item_list, comboBox_dir]
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        cursor.close()
        conn.close()
        sys.exit()


def flagStatus(v_key, v_status):
    cursor = conn.cursor()
    sql = "SELECT FLAG FROM MODEL_PROFILE WHERE KEY = " + str(v_key)
    result = sql_execute(cursor, sql)

    if result[0][0] == v_status:
        cursor.close()
        return 0
    else:
        sql = "BEGIN SP_FLAG_STATUS("+str(v_key)+", "+str(v_status)+"); END;"
        sql_execute(cursor, sql, execute_only=True)
        cursor.close()
        if result[0][0] == 0 and v_status == 1:
            return 1


# model 상세 정보
def info_profile(v_key):
    cursor = conn.cursor()
    sql = "SELECT name, real_name, birth_date, height, weight, size_top, size_pants, size_shoe, size_other\n"
    sql += "     , tel, email, insta_id, model_desc, data_date\n"
    sql += "  FROM MODEL_PROFILE\n"
    sql += " WHERE KEY = " + str(v_key)
    result = sql_execute(cursor, sql)
    columns = [d[0].lower() for d in cursor.description]  # 칼럼명은 대문자로 입력됨
    result_profile = {columns[idx]: (str(data) if data is not None or data == "None" else "") for idx, data in enumerate(result[0])}

    sql = "SELECT no, nvl(hobbynspec, '''') as hobbynspec\n"
    sql += "  FROM HOBBYNSPEC\n"
    sql += " WHERE KEY = " + str(v_key)
    sql += " ORDER BY no"
    result_hobbynspec = sql_execute(cursor, sql)
    cursor.close()
    return [result_profile, result_hobbynspec]


def updateProfile(v_update_tuple):
    """
    v_update_tuple[key, update_value]
    """
    cursor = conn.cursor()
    sql = "UPDATE MODEL_PROFILE\n"
    sql += "  SET "
    for idx, data in enumerate(v_update_tuple[1]):
        sql += ("     , " if idx else "") + data[0] + " = '" + str(data[1]) + "'\n"
    sql += " WHERE KEY = " + str(v_update_tuple[0]) + "\n"
    sql_execute(cursor, sql, execute_only=True, key=v_update_tuple[0])
    print(sql)
    cursor.close()
    conn.commit()
    return True


def updateHobbynspec(v_update_tuple):
    """
    v_update_tuple[key, mod_type, insert_value]
    mod_type: INSERT/DELETE
    """
    cursor = conn.cursor()
    returnVal = ""
    if v_update_tuple[1] == "INSERT":
        sql = "INSERT INTO HOBBYNSPEC VALUES\n"
        sql += "("+str(v_update_tuple[0])+",(SELECT NVL(MAX(NO),0)+1 FROM HOBBYNSPEC WHERE KEY = "+str(v_update_tuple[0])+"),'"+v_update_tuple[2]+"',SYSDATE,'admin',SYSDATE,'admin')"
        sql_execute(cursor, sql, execute_only=True, key=v_update_tuple[0])
        returnVal = "저장되었습니다."
    elif v_update_tuple[1] == "DELETE":
        sql = "DELETE HOBBYNSPEC WHERE KEY = " + str(v_update_tuple[0]) + " AND NO = " + str(v_update_tuple[2])
        sql_execute(cursor, sql, execute_only=True, key=v_update_tuple[0])
        returnVal = "삭제되었습니다."
    cursor.close()
    conn.commit()
    return returnVal


if __name__ == "__main__":
    pass

import importlib
import sys

cx_Oracle = importlib.import_module("cx_Oracle")
username = "ADMIN"
<<<<<<< HEAD
password = "AhnCsh181223"
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")# conn = cx_Oracle.connect(user="AHN_TEST", password="AHN_TEST3818", dsn="cogdw_144")
=======
password = ""
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")
>>>>>>> origin/master


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
            srch_sql2 += ("        OR (" if srch_sql else "(") + v_tab_alias + "." + v_srch_dir[key][0] + " >= " + srch_items["ge"]
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
            v_sql += "   AND (" + (srch_sql + "\n" if srch_sql else "") + srch_sql2 + ")\n"
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
    """
    execute_only : 필수
    key = None : 에러 발생 - 점유 해제 필요 시
    """
    try:
        if "execute_many" in kwargs and kwargs["execute_many"]:
            v_cur_cursor.executemany(v_sql, kwargs["ins_data"])
        elif "ins_data" in kwargs:
            v_cur_cursor.execute(v_sql, kwargs["ins_data"])
        else:
            v_cur_cursor.execute(v_sql)
        if "execute_only" in kwargs and not kwargs["execute_only"]:
            return v_cur_cursor.fetchall()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(v_sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        if kwargs and "key" in kwargs and kwargs["key"] is not None:
            flagStatus(kwargs["key"], 0)  # 점유중인 데이터를 해제
        v_cur_cursor.close()
        if kwargs and "er_rollback" in kwargs:
            conn.rollback()
        conn.close()
        sys.exit()


def get_model_list(v_page_no, v_page_size,  v_search_dir={}):
    cursor = conn.cursor()
    sql =  "SELECT A.NAME, A.BIRTH_DATE, A.TEL, A.INSTA_ID, A.DATA_DATE, A.FILE_NAME, A.DIR_ROUTE, A.IMAGE_PATH, COUNT(A.NAME) OVER () AS TOTAL_CNT, A.KEY, A.FOLDER_PATH\n"
    sql += "  FROM (\n"
    sql += "SELECT DISTINCT A.NAME, A.BIRTH_DATE, A.TEL, A.INSTA_ID, A.DATA_DATE, B.FILE_NAME, B.DIR_ROUTE, B.FOLDER_PATH, B.IMAGE_PATH, A.KEY\n"
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
    result = sql_execute(cursor, sql, execute_only=False)
    cursor.close()
    return list(map(list, result))


def get_comboBox_list_a(v_combo_type):
    cursor = conn.cursor()
    sql =  "SELECT TABLE_NAME, COMBO_DETAIL_TYPE, COL_NAME, COL_DISPLAY_NAME, COMPARE_OPERATOR, DATA_TYPE, RANGE_SEARCH\n"
    sql += "  FROM COMBO_MAP_LIST\n"
    sql += " WHERE COMBO_TYPE = '" + v_combo_type + "'\n"
    sql += " ORDER BY SORT_ORDER"
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        item_list, item_table_map, comboBox_dir = [], {}, {}
        for row in result:
            item_list.append(row[3])
            comboBox_dir[row[3]] = [row[2], row[4], {"s": [], "ge": "", "le": ""}, row[5], row[6]]
            # 테이블명: { 항목명: [칼럼명, 연산자, {검색목록}, 데이터유형, 범위 검색 여부] }
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
    sql =  "SELECT COL_DISPLAY_NAME\n"
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
    sql = "SELECT NVL(FLAG,0) FLAG FROM MODEL_PROFILE WHERE KEY = '" + str(v_key) + "'"
    result = sql_execute(cursor, sql, execute_only=False, key=v_key)

    if result[0][0] == v_status:
        cursor.close()
        return 0
    else:
        sql = "BEGIN SP_FLAG_STATUS('"+str(v_key)+"', "+str(v_status)+"); END;"
        sql_execute(cursor, sql, execute_only=True)
        cursor.close()
        if result[0][0] == 0 and v_status == 1:
            return 1


# model 상세 정보
def info_profile(v_key):
    cursor = conn.cursor()
    sql =  "SELECT name, real_name, birth_date, height, weight, size_top, size_pants, size_shoe, size_other\n"
    sql += "     , tel, email, insta_id, model_desc, data_date\n"
    sql += "  FROM MODEL_PROFILE\n"
    sql += " WHERE KEY = '" + str(v_key) + "'"
    result = sql_execute(cursor, sql, execute_only=False, key=v_key)
    columns = [d[0].lower() for d in cursor.description]  # 칼럼명은 대문자로 입력됨
    if len(result):
        result_profile = {col: (str(result[0][idx]) if result[0][idx] is not None and result[0][idx] != "None" else "") for idx, col in enumerate(columns)}
    else:
        result_profile = {col: "" for idx, col in enumerate(columns)}

    sql =  "SELECT no, nvl(hobbynspec, '') as hobbynspec\n"
    sql += "  FROM HOBBYNSPEC\n"
    sql += " WHERE KEY = '" + str(v_key) + "'"
    sql += " ORDER BY no"
    result_hobbynspec = sql_execute(cursor, sql, execute_only=False, key=v_key)
    cursor.close()
    return [result_profile, result_hobbynspec]


def updateProfile(v_update_tuple):
    """
    v_update_tuple[key, user_name, update_value]
    """
    cursor = conn.cursor()
    user_name = v_update_tuple[1]
    column_list = ""
    value_list = ""
    sql = "MERGE INTO MODEL_PROFILE\n" \
          "  USING DUAL\n" \
          "    ON (KEY = '" + str(v_update_tuple[0]) + "')\n" \
          " WHEN MATCHED THEN\n" \
          "   UPDATE SET UPDATE_DATE = SYSDATE, UPDATE_EMP = '" + user_name + "'"
    for idx, data in enumerate(v_update_tuple[2]):
        sql += ", " + data[0] + " = '" + str(data[1]) + "'"
        column_list += ", " + data[0]
        value_list += ", '" + str(data[1]) + "'"
    sql += "\nWHEN NOT MATCHED THEN\n" \
           "   INSERT (key, insert_date, insert_emp, update_date, update_emp" + column_list + ") " \
           "VALUES ((SELECT NVL(MAX(KEY),0)+1 FROM MODEL_PROFILE), sysdate, '"+user_name+"', sysdate, '"+user_name+"'"+value_list + ")"

    sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_update_tuple[0])
    cursor.close()
    return True


def updateHobbynspec(v_update_tuple):
    """
    v_update_tuple[mod_type, key, user_name, insert_value]
    mod_type: INSERT/DELETE
    """
    v_key = v_update_tuple[1]["key"]
    cursor = conn.cursor()
    if v_update_tuple[0] == "INSERT":
        sql = "INSERT INTO HOBBYNSPEC VALUES\n"
        sql += "(:key,(SELECT NVL(MAX(NO),0)+1 FROM HOBBYNSPEC WHERE KEY = :key),:data,SYSDATE,:user_name,SYSDATE,:user_name)"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_update_tuple[1])
    elif v_update_tuple[0] == "DELETE":
        sql = "DELETE HOBBYNSPEC WHERE KEY = :key AND NO = :no"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_update_tuple[1])

        sql = "UPDATE HOBBYNSPEC A\n" \
              "   SET NO = (SELECT R_NO\n" \
              "               FROM (SELECT KEY, NO, ROW_NUMBER() OVER (ORDER BY NO) AS R_NO\n" \
              "                       FROM HOBBYNSPEC\n" \
              "                      WHERE KEY = :key) B\n" \
              "              WHERE A.KEY = B.KEY AND A.NO = B.NO)\n" \
              " WHERE A.KEY = :key"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data={"key": v_key})
    cursor.close()
    return True


def info_career(v_key):
    cursor = conn.cursor()
    sql =  "SELECT a.career_type, a.detail_gubun, to_char(a.no) as no, a.careers\n"
    sql += "  FROM CAREER A, COMBO_MAP_LIST B\n"
    sql += " WHERE A.CAREER_TYPE = B.COL_NAME(+)\n"
    sql += "   AND A.KEY = '" + str(v_key) + "'\n"
    sql += "   AND 'CAREER' = B.COMBO_TYPE(+)\n"
    sql += " ORDER BY B.SORT_ORDER, A.CAREER_TYPE, A.DETAIL_GUBUN, A.NO"
    result = sql_execute(cursor, sql, execute_only=False, key=v_key)
    career_result = {}
    for row in result:
        if row[0] not in career_result:
            career_result[row[0]] = {}
        if row[1] not in career_result[row[0]]:
            career_result[row[0]][row[1]] = {}
        career_result[row[0]][row[1]][row[2]] = row[3]
    columns = [d[0].lower() for d in cursor.description]
    cursor.close()
    return [columns, career_result]


def updateCareer(v_update_tuple):
    """
    v_update_tuple
    INSERT : (mod_type, [{key, career_type, detail_gubun, insert_value}])
    UPDATE : (mod_type, [{key, career_type, detail_gubun, no, insert_value}])
    DELETE : (mod_type, [{key, career_type, detail_gubun, no}])
    mod_type: INSERT/UPDATE/DELETE
    """
    v_data_list = v_update_tuple[1]
    v_key = v_data_list[0]["key"]
    cursor = conn.cursor()
    if v_update_tuple[0] == "INSERT":
        sql = "INSERT INTO CAREER VALUES\n" + \
              "(:key, :career_type, :detail_gubun, " + \
              "(SELECT NVL(MAX(NO),0)+1 FROM CAREER" + \
              " WHERE KEY = :key AND CAREER_TYPE = :career_type AND DETAIL_GUBUN = :detail_gubun), :careers, SYSDATE,:user_name,SYSDATE,:user_name)"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[0])
    elif v_update_tuple[0] == "UPDATE":
        sql = "UPDATE CAREER SET CAREERS = :careers WHERE KEY = :key AND CAREER_TYPE = :career_type AND DETAIL_GUBUN = :detail_gubun AND NO = :no AND UPDATE_EMP = :user_name"
        sql_execute(cursor, sql, execute_many=True, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list)
    elif v_update_tuple[0] == "DELETE":
        sql = "DELETE CAREER WHERE KEY = :key AND CAREER_TYPE = :career_type AND DETAIL_GUBUN = :detail_gubun AND NO = :no"
        sql_execute(cursor, sql, execute_many=True, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list)

        v_no_update_list = []
        compare_val = ""
        for data in v_data_list:
            current_val = data["career_type"]+data["detail_gubun"]
            if compare_val != current_val:
                v_no_update_list.append({"key": v_key, "career_type": data["career_type"], "detail_gubun": data["detail_gubun"]})
                compare_val = current_val

        sql = "UPDATE CAREER A\n" \
              "   SET NO = (SELECT R_NO\n" \
              "               FROM (SELECT KEY, CAREER_TYPE, DETAIL_GUBUN, NO\n"\
              "                          , ROW_NUMBER() OVER (PARTITION BY KEY, CAREER_TYPE, DETAIL_GUBUN ORDER BY NO) AS R_NO\n" \
              "                       FROM CAREER\n" \
              "                      WHERE KEY = :key AND CAREER_TYPE = :career_type AND DETAIL_GUBUN = :detail_gubun) B\n" \
              "              WHERE A.KEY = B.KEY AND A.CAREER_TYPE = B.CAREER_TYPE\n" \
              "                AND A.DETAIL_GUBUN = B.DETAIL_GUBUN AND A.NO = B.NO)\n" \
              " WHERE A.KEY = :key AND CAREER_TYPE = :career_type AND DETAIL_GUBUN = :detail_gubun"
        sql_execute(cursor, sql, execute_many=True, execute_only=True, er_rollback=True, key=v_key, ins_data=v_no_update_list)
    elif v_update_tuple[0] == "ALL_DELETE":
        sql = "DELETE CAREER WHERE KEY = '" + v_key + "'"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key)
    cursor.close()
    return True


def getCMCodeList(v_g_code):
    cursor = conn.cursor()
    sql = "SELECT CODE, CODE_NM FROM CM_CODE WHERE G_CODE = '" + v_g_code + "' AND USE_YN = 'Y' ORDER BY SORT_ORDER"
    result = sql_execute(cursor, sql, execute_only=False)
    cursor.close()
    code_list = []
    code_map = {}
    for cd in result:
        code_list.append(cd[1])
        code_map[cd[1]] = cd[0]
    return [code_list, code_map]


def info_contact(v_key):
    cursor = conn.cursor()
    sql =  "SELECT to_char(no) no, name, sf_code_nm('CONTACT_GUBUN', gubun) as gubun, position, mng_gubun, tel, email, data_date\n"
    sql += "  FROM CONTACT\n"
    sql += " WHERE KEY = '" + str(v_key) + "'\n"
    sql += " ORDER BY NO"
    result = sql_execute(cursor, sql, execute_only=False, key=v_key)
    columns = [d[0].lower() for d in cursor.description]
    cursor.close()
    return [columns, result]


def updateContact(v_update_tuple):
    """
    v_update_tuple
    INSERT : (mod_type, [{key, name, gubun, position, mng_gubun, tel, email, data_date}])
    UPDATE : (mod_type, [{key, no, name, gubun, position, mng_gubun, tel, email, data_date}])
    DELETE : (mod_type, [{key, no}])
    mod_type: INSERT/UPDATE/DELETE
    """
    v_data_list = v_update_tuple[1]
    v_key = v_data_list[0]["key"]
    cursor = conn.cursor()
    if v_update_tuple[0] == "INSERT":
        sql = "INSERT INTO CONTACT VALUES\n" \
              "(:key, (SELECT NVL(MAX(NO),0)+1 FROM CONTACT WHERE KEY = :key), :name, :gubun, :position, " + \
              ":mng_gubun, :tel, :email, :data_date, SYSDATE,:user_name,SYSDATE,:user_name)"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[0])
    elif v_update_tuple[0] == "UPDATE":
        for r_idx, row in enumerate(v_data_list):
            sql = "UPDATE CONTACT SET UPDATE_DATE = SYSDATE, UPDATE_EMP = :user_name"
            for c_idx, col in enumerate(list(row.keys())[2:]):  # key, no 제외
                sql += ", " + col+" = :"+col
            sql += "\n"
            sql += " WHERE KEY = :key AND NO = :no"
            sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[r_idx])
    elif v_update_tuple[0] == "DELETE":
        sql = "DELETE CONTACT WHERE KEY = :key AND NO = :no"
        sql_execute(cursor, sql, execute_many=True, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list)

        sql = "UPDATE CONTACT A\n" \
              "   SET NO = (SELECT R_NO\n" \
              "               FROM (SELECT KEY, NO, ROW_NUMBER() OVER (ORDER BY NO) AS R_NO\n" \
              "                       FROM CONTACT\n" \
              "                      WHERE KEY = :key) B\n" \
              "              WHERE A.KEY = B.KEY AND A.NO = B.NO)\n" \
              " WHERE A.KEY = :key"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data={"key": v_key})
    elif v_update_tuple[0] == "ALL_DELETE":
        sql = "DELETE CONTACT WHERE KEY = '" + v_key + "'"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key)
    cursor.close()
    return True


def getColType():
    cursor = conn.cursor()
    sql = "SELECT LOWER(GUBUN) GUBUN, LOWER(COL_NAME) COL_NAME, DATA_TYPE, DATA_LEN, CHECK_STRING\n" \
          "  FROM COLUMN_VALUE_TYPE\n" \
          " ORDER BY COL_NAME"
    result = sql_execute(cursor, sql, execute_only=False)
    result_mod_data = {}
    for r in result:
        if r[0] not in result_mod_data:
            result_mod_data[r[0]] = []
        result_mod_data[r[0]].append(r[1:])
    return result_mod_data


def getMaxKeyOfProfile():
    cursor = conn.cursor()
    sql = "SELECT MAX(KEY)\n" \
          "  FROM MODEL_PROFILE"
    result = sql_execute(cursor, sql, execute_only=False)
    return result[0][0]


def info_contract(v_key):
    cursor = conn.cursor()
    sql =  "SELECT A.type, sf_code_nm('C_MONTH', A.c_month) as c_month, A.amount||NVL2(A.amount2,'~'||A.amount2,'') as amount" \
           ", B.ap, A.data_date, A.amount amount1, A.amount2\n" \
           "     , count(1) over (partition by A.type) as merge_col_cnt\n" \
           "     , row_number() over (partition by A.type order by to_number(A.c_month)) as r_no\n" \
           "  FROM CNTR_AMOUNT A, CNTR_AMOUNT_AP B\n" \
           " WHERE A.KEY = B.KEY(+) AND A.TYPE = B.TYPE(+)\n" \
           "   AND A.KEY = '" + str(v_key) + "'\n" \
           " ORDER BY A.TYPE, TO_NUMBER(A.C_MONTH)"
    result = sql_execute(cursor, sql, execute_only=False, key=v_key)
    columns = [d[0].lower() for d in cursor.description]
    cursor.close()
    return [columns, result]


def updateContract(v_update_tuple):
    """
    v_update_tuple
    INSERT : (mod_type, [{key, type, c_month, amount, amount2, ap, data_date}])
    UPDATE : (mod_type, [{key, type, c_month, amount, amount2, ap, data_date}])
    DELETE : (mod_type, [{key, type, c_month}])
    mod_type: INSERT/UPDATE/DELETE
    """
    v_data_list = v_update_tuple[1]
    v_key = v_data_list[0]["key"]
    cursor = conn.cursor()
    if v_update_tuple[0] == "INSERT":
        sql = "INSERT INTO CNTR_AMOUNT (KEY, TYPE, C_MONTH, AMOUNT, AMOUNT2, DATA_DATE, " \
              "INSERT_DATE, INSERT_EMP, UPDATE_DATE, UPDATE_EMP)\n VALUES" \
              "(:key, :type, sf_code_cd('C_MONTH', :c_month), :amount, :amount2, :data_date, SYSDATE,:user_name,SYSDATE,:user_name)"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[0])

        if v_data_list[1]["ap"]:
            sql = "MERGE INTO CNTR_AMOUNT_AP\n" \
                  "  USING DUAL\n" \
                  "     ON (KEY = :key AND TYPE = :type)\n" \
                  " WHEN MATCHED THEN\n" \
                  "   UPDATE SET AP = :ap, UPDATE_DATE = SYSDDATE, UPDATE_EMP = :user_name\n" \
                  " WHEN NOT MATCHED THEN\n" \
                  "   INSERT VALUES (:key, :type, :ap, SYSDATE,:user_name,SYSDATE,:user_name)\n"
            sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[1])
    elif v_update_tuple[0] == "UPDATE":
        update_data = v_data_list[0]
        first_check = 0
        update_list = list(update_data.keys())[3:]  # key, type, c_month 제외
        if update_list:
            sql = "UPDATE CNTR_AMOUNT SET UPDATE_DATE = SYSDATE, UPDATE_EMP = :user_name"
            for c_idx, col in enumerate(update_list):
                if update_data[col] is not None:
                    sql += ", " + col+" = :"+col
                    first_check += 1
            sql += "\n"
            sql += " WHERE KEY = :key AND TYPE = :type AND C_MONTH = sf_code_cd('C_MONTH', :c_month)"

            sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=update_data)

        if v_data_list[1]["ap"] is not None and v_data_list[1]["ap"] != "":
            sql = "MERGE INTO CNTR_AMOUNT_AP\n" \
                  "  USING DUAL\n" \
                  "     ON (KEY = :key AND TYPE = :type)\n" \
                  " WHEN MATCHED THEN\n" \
                  "   UPDATE SET AP = :ap, UPDATE_DATE = SYSDDATE, UPDATE_EMP = :user_name\n" \
                  " WHEN NOT MATCHED THEN\n" \
                  "   INSERT VALUES (:key, :type, :ap, SYSDATE,:user_name,SYSDATE,:user_name)\n"
            sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[1])
        elif v_data_list[1]["ap"] == "":
            sql = "DELETE CNTR_AMOUNT_AP WHERE KEY = :key AND TYPE = :type"
            v_delete_data = {"key": v_key, "type": update_data["type"]}
            sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_delete_data)
    elif v_update_tuple[0] == "DELETE":
        sql = "DELETE CNTR_AMOUNT WHERE KEY = :key AND TYPE = :type AND C_MONTH = sf_code_cd('C_MONTH', :c_month)"
        sql_execute(cursor, sql, execute_many=True, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list)

        sql = "DELETE CNTR_AMOUNT_AP A\n" \
              " WHERE (KEY, TYPE) IN (SELECT DISTINCT B.KEY, B.TYPE FROM CNTR_AMOUNT_AP B, CNTR_AMOUNT C\n" \
              "                        WHERE B.KEY = C.KEY(+) AND B.TYPE = C.TYPE(+)\n" \
              "                          AND B.KEY = :key AND C.KEY IS NULL)"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data={"key": v_key})
    elif v_update_tuple[0] == "ALL_DELETE":
        sql = "DELETE CNTR_AMOUNT WHERE KEY = '" + v_key + "'"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key)
    cursor.close()
    return True


def info_other(v_key):
    cursor = conn.cursor()
    sql =  "SELECT no, info, data_date\n"
    sql += "  FROM CNTR_OTHER\n"
    sql += " WHERE KEY = '" + str(v_key) + "'\n"
    sql += " ORDER BY NO"
    result = sql_execute(cursor, sql, execute_only=False, key=v_key)
    columns = [d[0].lower() for d in cursor.description]
    cursor.close()
    return [columns, result]


def updateOther(v_update_tuple):
    """
    v_update_tuple
    INSERT : (mod_type, [{key, no, info, data_date}])
    UPDATE : (mod_type, [{key, no, info, data_date}])
    DELETE : (mod_type, [{key, no}])
    mod_type: INSERT/UPDATE/DELETE
    """
    v_data_list = v_update_tuple[1]
    v_key = v_data_list[0]["key"]
    cursor = conn.cursor()
    if v_update_tuple[0] == "INSERT":
        sql = "INSERT INTO CNTR_OTHER VALUES\n" \
              "(:key, (SELECT NVL(MAX(NO),0)+1 FROM CNTR_OTHER WHERE KEY = :key), :info, " + \
              ":data_date, SYSDATE,'admin',SYSDATE,'admin')"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[0])
    elif v_update_tuple[0] == "UPDATE":
        first_check = 0
        for r_idx, row in enumerate(v_data_list):
            sql = "UPDATE CNTR_OTHER SET "
            for c_idx, col in enumerate(list(row.keys())[2:]):  # key, no 제외
                sql += (", " if first_check else "") + col+" = :"+col
                first_check += 1
            sql += "\n"
            sql += " WHERE KEY = :key AND NO = :no"
            sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list[r_idx])
    elif v_update_tuple[0] == "DELETE":
        sql = "DELETE CNTR_OTHER WHERE KEY = :key AND NO = :no"
        sql_execute(cursor, sql, execute_many=True, execute_only=True, er_rollback=True, key=v_key, ins_data=v_data_list)

        sql = "UPDATE CNTR_OTHER A\n" \
              "   SET NO = (SELECT R_NO\n" \
              "               FROM (SELECT KEY, NO, ROW_NUMBER() OVER (ORDER BY NO) AS R_NO\n" \
              "                       FROM CNTR_OTHER\n" \
              "                      WHERE KEY = :key) B\n" \
              "              WHERE A.KEY = B.KEY AND A.NO = B.NO)\n" \
              " WHERE A.KEY = :key"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key, ins_data={"key": v_key})
    elif v_update_tuple[0] == "ALL_DELETE":
        sql = "DELETE CNTR_OTHER WHERE KEY = '" + v_key + "'"
        sql_execute(cursor, sql, execute_only=True, er_rollback=True, key=v_key)
    cursor.close()
    return True


def loginInfo():
    cursor = conn.cursor()
    sql = "SELECT USER_NAME FROM MODEL_USERS ORDER BY SORT_ORDER"
    result = sql_execute(cursor, sql, execute_only=False, er_rollback=True)
    cursor.close()
    list = [r[0] for r in result]
    return list


def updatePassword(v_user_name, v_user_pw):
    cursor = conn.cursor()
    sql = "UPDATE MODEL_USERS SET USER_PW = '" + v_user_pw + "' WHERE USER_NAME = '" + v_user_name + "'"
    sql_execute(cursor, sql, execute_only=True, er_rollback=True)
    cursor.close()
    return True


def loginExec(v_user_name, v_user_pw):
    cursor = conn.cursor()
    sql = "SELECT COUNT(1) FROM MODEL_USERS WHERE USER_NAME = '" + v_user_name + "' AND USER_PW = '" + v_user_pw + "'"
    result = sql_execute(cursor, sql, execute_only=False, er_rollback=True)
    cursor.close()
    return True if result[0][0] == 1 else False


def saveImagePath(v_type, v_key, v_path=None):
    """
    v_type : insert or delete
    """
    cursor = conn.cursor()
    sql = "UPDATE MODEL_INFO SET IMAGE_PATH = '" + (v_path if v_type == "insert" else "") + "' WHERE KEY = '" + str(v_key) + "'"
    sql_execute(cursor, sql, execute_only=True, er_rollback=True)
    cursor.close()
    return True


if __name__ == "__main__":
    pass


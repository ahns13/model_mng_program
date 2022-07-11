import sys
import importlib

cx_Oracle = importlib.import_module("cx_Oracle")
username = "ADMIN"
password = "pw"
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")
cursor = conn.cursor()


def get_bind_cols(len_col):
    ins_txt = ""
    for i in range(len_col):
        ins_txt += ":" + str(i+1) + ","
    return ins_txt


def db_close():
    cursor.close()
    conn.close()


def db_cancel():
    cursor.close()
    conn.rollback()
    conn.close()


def sql_execute(v_exec_many, v_sql, v_ins_data=None):
    try:
        if v_exec_many:
            cursor.executemany(v_sql, v_ins_data)
        elif v_ins_data:
            cursor.execute(v_sql, v_ins_data)
        else:
            cursor.execute(v_sql)
        return True
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(v_sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


def get_file_list(v_dir_route):
    sql = ("SELECT A.KEY, A.NAME||A.BIRTH_DATE AS NAME_BIRTH, B.FILE_NAME, A.TEL, A.INSTA_ID\n"
           "  FROM MODEL_PROFILE A, MODEL_INFO B\n"
           " WHERE A.KEY = B.KEY\n"
           "   AND B.DIR_ROUTE = '" + v_dir_route + "'")
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        file_list = {"key": [], "nameBirth": [], "fileName": [], "instaId": [], "tel": []}
        for r in result:
            file_list["key"].append(r[0])
            file_list["nameBirth"].append(r[1] if r[1] else "")
            file_list["fileName"].append(r[2])
            file_list["tel"].append(r[3] if r[3] else "")
            file_list["instaId"].append(r[4] if r[4] else "")
        return file_list
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


def dup_ins_check(v_cls_model):
    sql = ("SELECT NAME, FILE_NAME"
           "  FROM MODEL_DUP_CHECK\n"
           " WHERE FILE_NAME = '" + v_cls_model.model_file_info["file_name"] + "'")
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        file_list = {"name": [], "fileName": []}
        for r in result:
            file_list["name"].append(r[0])
            file_list["fileName"].append(r[1])
        return file_list
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


def get_key():
    sql = "SELECT NVL(MAX(KEY)+1,1) FROM MODEL_PROFILE"
    cursor.execute(sql)
    return cursor.fetchall()[0][0]


def get_max_data(v_current_dir_route):
    sql = "SELECT FILE_NAME FROM MODEL_INFO\n" \
          " WHERE DIR_ROUTE = '" + v_current_dir_route + "'\n" \
          "   AND KEY = (SELECT MAX(KEY) FROM MODEL_INFO WHERE DIR_ROUTE = '" + v_current_dir_route + "')"
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        return result[0][0] if len(result) else ""
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


# model_profile insert
def model_profile_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO MODEL_PROFILE(KEY,NAME,REAL_NAME,MODEL_DESC,BIRTH_DATE,HEIGHT,WEIGHT,\n" \
          "SIZE_TOP,SIZE_PANTS,SIZE_SHOE,SIZE_OTHER,\n" \
          "TEL,EMAIL,INSTA_ID,DATA_DATE,INSERT_DATE,INSERT_EMP,UPDATE_DATE,UPDATE_EMP,FLAG) \n" \
          "VALUES(" + str(v_key_value) + ", " + get_bind_cols(14) + " SYSDATE, 'admin', SYSDATE, 'admin', 0)"

    ins_data = [
        v_cls_model.model_profile["name"],
        v_cls_model.model_profile["real_name"],
        v_cls_model.model_profile["model_desc"],
        v_cls_model.model_profile["birthYear"],
        v_cls_model.model_profile["height"],
        v_cls_model.model_profile["weight"],
        v_cls_model.model_profile["sizeTop"],
        v_cls_model.model_profile["sizePants"],
        v_cls_model.model_profile["sizeShoe"],
        v_cls_model.model_profile["sizeOther"],
        v_cls_model.model_profile["tel"],
        v_cls_model.model_profile["email"],
        v_cls_model.model_profile["insta_id"],
        v_cls_model.model_profile["data_date"]
    ]
    sql_execute(False, sql, ins_data)


# hoobynspec insert
def hoobynspec_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO HOBBYNSPEC VALUES(" + \
          str(v_key_value) + ", " + get_bind_cols(2) + " SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = [[idx+1, data] for idx, data in enumerate(v_cls_model.model_profile["hobbyNspec"])]
    sql_execute(True, sql, ins_data)


# career insert
def career_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CAREER VALUES(" + \
          str(v_key_value) + ", " + get_bind_cols(4) + " SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = []
    model_data = v_cls_model.model_career
    for key in model_data.keys():
        if key != "type":
            for type_key in model_data[key].keys():
                for c_idx, c_data in enumerate(model_data[key][type_key]):
                    ins_data.append([key, type_key, c_idx+1, c_data])

    sql_execute(True, sql, ins_data)


# contact insert
def contact_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CONTACT VALUES(" + \
          str(v_key_value) + ", " + get_bind_cols(8) + " SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = []
    model_data = v_cls_model.model_contact
    for idx, data in enumerate(model_data):
        ins_data.append([idx+1, data[0], data[1], data[2], data[3], data[4], data[5], data[6]])

    sql_execute(True, sql, ins_data)


# contract_amount insert
def contract_amount_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CNTR_AMOUNT(KEY, TYPE, C_MONTH, AMOUNT, AMOUNT2, DATA_DATE, AP, " + \
          "INSERT_DATE, INSERT_EMP, UPDATE_DATE, UPDATE_EMP) VALUES(" + \
          str(v_key_value) + ", " + get_bind_cols(5) + " SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data, row_data = [], []
    model_data = v_cls_model.model_contract_amt
    for key in model_data.keys():
        amount_data = model_data[key]
        for type_key in amount_data.keys():
            if type_key == "amount":
                for amt in amount_data[type_key]:
                    row_data.append([key, amt[0], amt[1], amt[2], amt[3]])  # month별 금액
            else:
                for el in row_data:
                    el.append(amount_data[type_key])  # AP
        ins_data.extend(row_data)
        row_data = []

    sql_execute(True, sql, ins_data)


# contract_info insert
def contract_info_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CNTR_OTHER(KEY, NO, INFO, DATA_DATE, INSERT_DATE, INSERT_EMP, UPDATE_DATE, UPDATE_EMP) VALUES(" + \
          str(v_key_value) + ", " + get_bind_cols(3) + " SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = []
    model_data = v_cls_model.model_contract_info
    for idx, data in enumerate(model_data):
        ins_data.append([idx+1, data[0], data[1]])

    sql_execute(True, sql, ins_data)


# file_info insert
def file_info_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO MODEL_INFO VALUES(" + \
          str(v_key_value) + ", " + get_bind_cols(4) + " SYSDATE, 'admin', SYSDATE, 'admin')"

    model_data = v_cls_model.model_file_info
    ins_data = [model_data["model_gubun"],
                model_data["model_dir_route"],
                model_data["file_name"],
                model_data["folder_path"]]

    sql_execute(False, sql, ins_data)


def model_dup_ins(v_cls_model):
    sql = ("INSERT INTO MODEL_DUP_CHECK VALUES("
           + str(v_cls_model.file_dup_bf_key) + ", '" + v_cls_model.model_profile["name"] + "', "
           + "(SELECT NVL(MAX(NO),0) FROM MODEL_DUP_CHECK WHERE DUP_KEY = " + str(v_cls_model.file_dup_bf_key) + ")+1, "
           "'" + v_cls_model.model_file_info["file_name"] + "', "
           "'" + v_cls_model.model_file_info["folder_path"] + "', SYSDATE)")

    sql_execute(False, sql)


import cx_Oracle, sys

id = "ADMIN"
pw = "AhnCsh181223"
conn = cx_Oracle.connect(id, pw, "modeldb_medium")
cursor = conn.cursor


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


def file_insert_check(v_cls_model):
    check_sql = ("SELECT A.NAME, B.FILE_NAME FROM MODEL_PROFILE A, MODEL_INFO B\n"
                 " WHERE A.KEY = B.KEY"
                 "   AND A.NAME = '" + v_cls_model.model_profile.name + "'")
    cursor.execute(check_sql)
    result = cursor.fetchall()
    if len(result):
        for r_data in result:
            if r_data[1] == v_cls_model.model_file_info.file_name:
                return "e"  # data 존재함
            elif r_data[1] != v_cls_model.model_file_info.file_name:
                return "c"  # 파일 체크 필요 > 중단
    else:
        return "x"  # data 없음


def get_key():
    check_sql = "SELECT NVL(MAX(KEY),0) FROM MODEL_PROFILE"
    cursor.execute(check_sql)
    return cursor.fetchall()[0][0]


# model_profile insert
def model_profile_ins(v_cls_model):
    key_val = get_key() + 1
    sql = "INSERT INTO MODEL_PROFILE VALUES(" + key_val + ", " + \
          get_bind_cols(12) + "SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = [
        v_cls_model.model_profile.name,
        v_cls_model.model_profile.real_name,
        v_cls_model.model_profile.birthYear,
        v_cls_model.model_profile.height,
        v_cls_model.model_profile.weight,
        v_cls_model.model_profile.sizeTop,
        v_cls_model.model_profile.sizePants,
        v_cls_model.model_profile.sizeShoe,
        v_cls_model.model_profile.insta_id,
        v_cls_model.model_profile.tel,
        v_cls_model.model_profile.email,
        v_cls_model.model_profile.data_date
    ]
    try:
        cursor.execute(sql, ins_data)
        conn.commit()
        return key_val
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


# hoobynspec insert
def hoobynspec_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO HOBBYNSPEC VALUES(" + \
          v_key_value + ", " + get_bind_cols(2) + "SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = [[idx+1, data] for idx, data in enumerate(v_cls_model.model_profile.hobbyNspec)]
    try:
        cursor.executemany(sql, ins_data)
        conn.commit()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


# career insert
def career_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CAREER VALUES(" + \
          v_key_value + ", " + get_bind_cols(4) + "SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = []
    model_data = v_cls_model.model_career
    for key in model_data.keys():
        if key != "type":
            for type_key in model_data[key].keys():
                for c_idx, c_data in enumerate(model_data[key][type_key]):
                    ins_data.append([key, type_key, c_idx+1, c_data])

    try:
        cursor.executemany(sql, ins_data)
        conn.commit()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


# contact insert
def contact_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CONTACT VALUES(" + \
          v_key_value + ", " + get_bind_cols(8) + "SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = []
    model_data = v_cls_model.model_contact
    for idx, data in enumerate(model_data):
        ins_data.append([idx, data[0], data[1], data[2], data[3], data[4], data[5], data[6]])

    try:
        cursor.executemany(sql, ins_data)
        conn.commit()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


# contract_amount insert
def contract_amount_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CNTR_AMOUNT(KEY, TYPE, C_MONTH, AMOUNT, DATA_DATE, AP, " + \
          "INSERT_DATE, INSERT_EMP, UPDATE_DATE, UPDATE_EMP) VALUES(" + \
          v_key_value + ", " + get_bind_cols(4) + "SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = []
    model_data = v_cls_model.model_contract_amt
    for key in model_data.keys():
        amount_data = model_data[key]
        for type_key in amount_data.keys():
            if type_key == "amount":
                for amt in amount_data[type_key]:
                    ins_data.append([key, amt[0], amt[1], amt[2]])  # month별 금액
            else:
                for el in ins_data:
                    el.append(amount_data[type_key])  # AP

    try:
        cursor.executemany(sql, ins_data)
        conn.commit()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


# contract_info insert
def contract_info_ins(v_cls_model, v_key_value):
    sql = "INSERT INTO CNTR_OTHER(KEY, NO, INFO, DATA_DATE, INSERT_DATE, INSERT_EMP, UPDATE_DATE, UPDATE_EMP) VALUES(" + \
          v_key_value + ", " + get_bind_cols(3) + "SYSDATE, 'admin', SYSDATE, 'admin')"

    ins_data = []
    model_data = v_cls_model.model_contract_info
    for idx, data in enumerate(model_data):
        ins_data.append([idx, data[0], data[1]])

    try:
        cursor.executemany(sql, ins_data)
        conn.commit()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        db_cancel()
        sys.exit()


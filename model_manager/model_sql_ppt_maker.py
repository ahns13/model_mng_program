import importlib
import sys

cx_Oracle = importlib.import_module("cx_Oracle")
username = "ADMIN"
password = "xxxx"
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")


def sql_execute(v_cur_cursor, v_sql, **kwargs):
    try:
        v_cur_cursor.execute(v_sql)
        return v_cur_cursor.fetchall()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(v_sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        v_cur_cursor.close()
        conn.rollback()
        conn.close()
        sys.exit()


def ppt_get_profile(v_key):
    v_sql = """
            SELECT A.NAME
                 , CASE WHEN A.REAL_NAME IS NOT NULL THEN '(本 '||A.REAL_NAME||')' END||A.MODEL_DESC AS NAME_INFO
                 , CASE WHEN A.BIRTH_DATE IS NOT NULL THEN SUBSTR(A.BIRTH_DATE,3)||'년' END AS BIRTH_DATE
                 , CASE WHEN A.HEIGHT IS NOT NULL THEN A.HEIGHT||'cm' END AS HEIGHT
                 , CASE WHEN A.WEIGHT IS NOT NULL THEN A.WEIGHT||'kg' END AS WEIGHT
                 , REPLACE(RTRIM(LTRIM(
                        CASE WHEN A.SIZE_OTHER IS NOT NULL
                                  THEN A.SIZE_OTHER||','||CASE WHEN A.SIZE_SHOE IS NOT NULL THEN '신발:'||A.SIZE_SHOE END
                             ELSE
                                  CASE WHEN A.SIZE_TOP IS NOT NULL THEN '상의:'||A.SIZE_TOP END||','||
                                  CASE WHEN A.SIZE_PANTS IS NOT NULL THEN '하의:'||A.SIZE_TOP END||','||
                                  CASE WHEN A.SIZE_SHOE IS NOT NULL THEN '신발:'||A.SIZE_SHOE END
                             END, ','), ','), ',', ', ') AS SIZES
                 , B.HOBBYNSPEC
              FROM MODEL_PROFILE A
                 , (
                    SELECT LISTAGG(HOBBYNSPEC, ', ') WITHIN GROUP (ORDER BY NO) AS HOBBYNSPEC
                      FROM HOBBYNSPEC
                     WHERE KEY = """+str(v_key)+"""
                   ) B
             WHERE A.KEY = """+str(v_key)
    cursor = conn.cursor()
    result = sql_execute(cursor, v_sql)
    columns = [d[0].lower() for d in cursor.description]
    return dict(zip(columns, result[0]))


def ppt_get_career(v_key):
    v_sql = """
            SELECT A.CAREER_TYPE, LISTAGG(A.CAREERS, ', ') WITHIN GROUP(ORDER BY A.NO) AS CAREERS
              FROM CAREER A
                   LEFT OUTER JOIN COMBO_MAP_LIST B
                     ON A.CAREER_TYPE = B.COL_NAME
                    AND B.COMBO_TYPE = 'CAREER'
                    AND B.COMBO_DETAIL_TYPE = 'DATA'
             WHERE KEY = """+str(v_key)+"""
             GROUP BY A.CAREER_TYPE, B.SORT_ORDER
             ORDER BY B.SORT_ORDER
            """
    cursor = conn.cursor()
    result = sql_execute(cursor, v_sql)
    return result


def ppt_get_contract(v_key):
    v_sql = """
            SELECT 1 AS GBN, 1 NO, EMAIL, NVL2(DATA_DATE,'('||DATA_DATE||')','') AS INFO1
              FROM MODEL_PROFILE 
             WHERE KEY = """+str(v_key)+""" AND EMAIL IS NOT NULL
             UNION ALL
            SELECT 2 AS GBN, 1 NO
                 , TEL||CASE WHEN TEL IS NOT NULL AND INSTA_ID IS NOT NULL THEN ' ' END||INSTA_ID, NVL2(DATA_DATE,'('||DATA_DATE||')','') AS INFO1
              FROM MODEL_PROFILE 
             WHERE KEY = """+str(v_key)+""" AND (TEL IS NOT NULL OR INSTA_ID IS NOT NULL)
             UNION ALL
            SELECT 3 AS GBN, NO, NVL2(MNG_GUBUN,CASE WHEN MNG_GUBUN='MAIN' THEN '★' ELSE MNG_GUBUN END,'')||NAME||
                   CASE WHEN POSITION IS NOT NULL THEN ' '||POSITION||' ' ELSE ' ' END||TEL||' '||NVL2(DATA_DATE,'('||DATA_DATE||')','') AS CONTACT
                 , NULL INFO1
              FROM CONTACT
             WHERE KEY = """+str(v_key)+"""
             UNION ALL
            SELECT 4 AS GBN, ROW_NUMBER() OVER (ORDER BY A.TYPE) AS NO
                 , CASE WHEN A.TYPE <> '해당없음' THEN A.TYPE||') ' ELSE NULL END||
                   LISTAGG(CASE WHEN C_MONTH = '12' THEN '1년 ' ELSE C_MONTH||'개월 ' END||AMOUNT||NVL2(AMOUNT2,'~'||AMOUNT2,''), ' / ') WITHIN GROUP(ORDER BY A.TYPE, TO_NUMBER(A.C_MONTH)) AS AMOUNT
                 , MIN(CASE WHEN B.AP IS NOT NULL THEN '('||B.AP||')' END||NVL2(DATA_DATE,'('||DATA_DATE||')','')) AS AP
              FROM CNTR_AMOUNT A LEFT OUTER JOIN CNTR_AMOUNT_AP B
                   ON A.KEY = B.KEY AND A.TYPE = B.TYPE
             WHERE A.KEY = """+str(v_key)+"""
             GROUP BY A.TYPE
             UNION ALL
            SELECT 5 AS GBN, NO
                 , INFO, NULL INFO2
              FROM CNTR_OTHER 
             WHERE KEY = """+str(v_key)+"""
             ORDER BY GBN, NO
            """
    cursor = conn.cursor()
    result = sql_execute(cursor, v_sql)
    return result


if __name__ == "__main__":
    pass


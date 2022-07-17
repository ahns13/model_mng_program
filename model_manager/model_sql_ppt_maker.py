import importlib
import sys

cx_Oracle = importlib.import_module("cx_Oracle")
username = "ADMIN"
password = "AhnCsh181223"
conn = cx_Oracle.connect(user=username, password=password, dsn="modeldb_medium")


def ppt_get_profile(v_key):
    try:
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
        cursor.execute(v_sql)
        result = cursor.fetchall()
        columns = [d[0].lower() for d in cursor.description]
        return dict(zip(columns, result[0]))
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(v_sql)
        print("error code : " + str(error.code))
        print(error.message)
        print(error.context)
        conn.rollback()
        conn.close()
        sys.exit()


if __name__ == "__main__":
    pass


from mysql.connector import connect
import pandas as pd
import logging
TABLE_NAME_MAP = {
    'OPC-R2': "data_opc_r2",
    'PMS5003': "data_pms5003"
}

QUERY = """
SELECT * FROM %s
WHERE (serial_number = '%s'
AND sample_time > '%s')
ORDER BY sample_time DESC
LIMIT %d;
"""

WINDOW_MAX = pd.Timedelta('5min')

get_connection = lambda: connect(
        host='db',
        database='mannequin',
        user='root',
        password='telosair'
    )


def get_data(sensor: str, serial: str, num: int = 3):
    table_name = TABLE_NAME_MAP.get(sensor)
    if not table_name:
        return None
    
    query = QUERY%(table_name, serial, str(pd.Timestamp.now().round('1S')-pd.Timedelta('4h') -WINDOW_MAX), num)
    logging.info(f"QUERY: {query}")

    conn = None
    try:
        conn = get_connection()
        ret = pd.read_sql_query(query,conn, index_col='id')[['pm2_5']].mean()
        logging.info(ret)
        return ret['pm2_5']
    except:
        return None
    finally:
        if conn is not None:
            conn.close()
    
def get_data_many(sensors: 'list[str]', serials: 'list[str]', num: int = 3):
    return [get_data(s, sn, num) for s, sn in zip(sensors, serials)]


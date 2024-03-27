from serial.tools.list_ports import comports
from serial import Serial
from typing import Tuple, Union
import logging
from mysql.connector import connect
from threading import Thread
from queue import Queue
from datetime import datetime
from time import sleep, time
VALID_PID_VID_PATTERNS = [
    (0x80cb, 0x239a) # QT-Py SAMD21
]
 
DEVICE_TYPE_PT = "PMS5003" #Plantower
DEVICE_TYPE_AS = "OPC-R2" #AlphaSense

TABLE_NAME_AS = "data_opc_r2"
TABLE_NAME_PT = "data_pms5003"

DEVICE_TYPE_TABLE_COLUMNS_MAP = {
    DEVICE_TYPE_AS: ['sample_time', 'serial_number', 'pm1', 'pm2_5', 'pm10'],
    DEVICE_TYPE_PT: ['sample_time', 'serial_number', 'pm1', 'pm2_5', 'pm10'],
}


"""
CREATE TABLE data_pms5003 (
id INT AUTO_INCREMENT PRIMARY KEY,
sample_time DATETIME NOT NULL,
serial_number VARCHAR(32) NOT NULL,
pm1 INT NOT NULL,
pm2_5 INT NOT NULL,
pm10 INT NOT NULL,
pn0_3 INT NOT NULL,
pn0_5 INT NOT NULL,
pn1 INT NOT NULL,
pn2_5 INT NOT NULL,
pn5 INT NOT NULL,
pn10 INT NOT NULL
);
"""
INSERT_QUERY_AS = f"insert into {TABLE_NAME_AS} (sample_time, serial_number, pm1, pm2_5, pm10) values (%s, %s, %s, %s, %s)"
INSERT_QUERY_PT = f"insert into {TABLE_NAME_PT} (sample_time, serial_number, pm1, pm2_5, pm10, pn0_3, pn0_5, pn1, pn2_5, pn5, pn10) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

DEVICE_TYPE_DICT_KEYS_MAP = {
    DEVICE_TYPE_AS: ['ts', 'serial_number', 'PM1', 'PM2.5', 'PM10'],
    DEVICE_TYPE_PT: ['ts', 'serial_number', 'PM1', 'PM2.5', 'PM10', 'PN0.3', 'PN0.5', 'PN1', 'PN2.5', 'PN5', 'PN10'],
}
LEN_DATA_TYPE_MAP = {
    10: DEVICE_TYPE_PT,
    32: DEVICE_TYPE_AS,
}

DEVICE_TYPE_HEADERS_MAP = {
    DEVICE_TYPE_PT: ["serial_number", "PM1","PM2.5","PM10","PN0.3","PN0.5","PN1","PN2.5","PN5","PN10"],
    DEVICE_TYPE_AS: ["timeMS","bin0","bin1","bin2","bin3","bin4","bin5","bin6","bin7","bin8",
                     "bin9","bin10","bin11","bin12","bin13","bin14","bin15","MToF0","MToF1",
                     "MToF2","MToF3","sampleFlowRate","temperature","relativeHumidity","samplingPeriod",
                     "rejectCountGlitch","rejectCountTof","PM1","PM2.5","PM10","checksum"]
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Data Acq.")

list_valid_ports = lambda: [port for port in comports() if (port.pid, port.vid) in VALID_PID_VID_PATTERNS]
"Enumerate through all ports and return those with a recognized PID:VID combo."

class SerialHandle(object):
    def __init__(self, name: str, path: str, serial_number:str, pid: int, vid: int):
        self.name = name
        self.path = path
        self.serial_number = serial_number
        self.pid = pid
        self.vid = vid
        self._port: Serial = None
    
    def open(self) -> bool:
        if (not self._port) or (not self._port.is_open):
            try:
                self._port = Serial(self.path, baudrate=115200)
            except OSError:
                return False
        return True
    
    def read_msg(self) -> dict:
        if not self.open():
            logger.error(f"Device at {self.path} has a port that will not open.")
        else:
            try:
                line = self._port.readline()
                # print(line)
                data = line.decode().strip().split(",")
                for i, val in enumerate(data[1:]):
                    data[i+1] = float(val)
                data_type = LEN_DATA_TYPE_MAP.get(len(data))
                if not data_type:
                    print("!")
                    logger.error(f"There is no matching pattern for data of length {len(data)}, from device {self.path}.")
                else:
                    ret = dict(zip(DEVICE_TYPE_HEADERS_MAP[data_type], data))
                    ret.update({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                    # ret.update({'serial_number': self.serial_number})
                    return ret
            except UnicodeDecodeError:
                logger.exception(f"Unicode Decode Error reading device at {self.path}.")
            except OSError:
                logger.exception(f"There was an exception reading the port at {self.path}.")
                self._port.close()
                self._port = None
            except ValueError:
                logger.exception(f"There was a non-numeric value in the data for device at {self.path}.")

        return {}

def make_serial_handle(port_info_obj) -> SerialHandle:
    return SerialHandle(
        port_info_obj.description,
        port_info_obj.device,
        port_info_obj.serial_number,
        port_info_obj.pid,
        port_info_obj.vid
    )

"""
import mysql.connector

# Connect to MySQL
connection = mysql.connector.connect(
  host='localhost',
  database='my_database',
  user='root',
  password='your_password')

# Check if the connection is established
if connection.is_connected():
    db_Info = connection.get_server_info()
    print("Connected to MySQL Server version ", db_Info)
    cursor = connection.cursor()

    # Insert Data
    query = "INSERT INTO your_table (column1, column2) VALUES (%s, %s)"
    values = ("value1", "value2")
    cursor.execute(query, values)

    connection.commit()
    print(cursor.rowcount, "Record inserted successfully into table")

    # Close the connection
    cursor.close()
    connection.close()
    print("MySQL connection is closed")

"""

build_insert_query = lambda table_name, columns, values: f"insert into {table_name} {tuple(columns)} values {tuple(values)}"

class SerialThread(Thread):
    def __init__(self, ser: SerialHandle, data_queue: Queue):
        self.ser = ser
        self.q = data_queue
        super().__init__(daemon=True)

    def run(self):
        while True:
            data = self.ser.read_msg()
            if data:
                self.q.put(data)
            else:
                sleep(1)

def main():
    ports = list_valid_ports()
    for port in ports:
        print(f"{port.description} Device at {port.device} has serial {port.serial_number}")

    data_queue = Queue()

    known_ports = set()
    for port in ports:
        known_ports.add(port.serial_number)
        th = SerialThread(make_serial_handle(port), data_queue)
        th.start()

    connection = connect(
        host='localhost',
        database='mannequin',
        user='root',
        password='telosair'
    )

    if connection.is_connected():
        db_Info = connection.get_server_info()
        logging.info("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
    
        last_serial_check = 0
        try:
            while True:
                if (data_queue.empty()) and (time() - last_serial_check >= 5):
                    ports = list_valid_ports()
                    for port in ports:
                        if port.serial_number not in known_ports:
                            print(f"New port at {port.name}.")
                            known_ports.add(port.serial_number)
                            SerialThread(make_serial_handle(port), data_queue).start()

                    last_serial_check = time()
                item = data_queue.get()
                # print(item)
                item_type = LEN_DATA_TYPE_MAP.get(len(item)-1)
                if not item_type:
                    # print(":(")
                    continue
                
                if item_type == DEVICE_TYPE_AS:

                    vals = [str(item[x]) for x in DEVICE_TYPE_DICT_KEYS_MAP[DEVICE_TYPE_AS]]
                    print(INSERT_QUERY_AS%tuple(vals))
                    cursor.execute(INSERT_QUERY_AS, vals)

                    connection.commit()
                    print(f"{cursor.rowcount} Record inserted successfully into table")

                elif item_type == DEVICE_TYPE_PT:
                    vals = [item[x] for x in DEVICE_TYPE_DICT_KEYS_MAP[DEVICE_TYPE_PT]]
                    # print(f"FORMAT STRING: {INSERT_QUERY_PT}")
                    # print(f"VALUES: {vals}")
                    # print(INSERT_QUERY_PT%tuple(vals))
                    cursor.execute(INSERT_QUERY_PT, vals)

                    connection.commit()
                    print(f"{cursor.rowcount} Record inserted successfully into table")


        except Exception as e:
            logger.exception(e)

        finally:
            connection.close()
            pass


if __name__=="__main__":
    main()

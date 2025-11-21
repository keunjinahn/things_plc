# -*- coding:utf-8 -*-
# 한글 주석 처리
__author__ = 'bychem'

import logging
import time
import json
import os
import sys
import platform
from logging import handlers
import signal
import json
from scapy.all import *
import MySQLdb
protocols = {1:'ICMP',6:'TCP',17:'UDP'}

class BychemGrep(object):
    def __init__(self, logger=None):
        file_logger = logging.getLogger("BychemGrep")
        file_logger.setLevel(logging.INFO)
        file_handler = handlers.RotatingFileHandler(
            "BychemGrep.log",
            maxBytes=(1024 * 1024 * 1),
            backupCount=5
        )

        formatter = logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s in [%(filename)s:%(lineno)d](%(process)d)')
        file_handler.setFormatter(formatter)
        file_logger.addHandler(file_handler)
        logger = file_logger
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('BychemGrep')
        else:
            self.logger = logger
        self.api_headers = {'Content-type': 'application/json'}
        self.logger.info("TrainProc start1...")
        self.plcdatas = {
            "temp_value_1": "",
            "temp_value_2":  "",
            "temp_value_3":  "",
            "temp_value_4":  "",
            "temp_value_5":  "",
            "temp_value_6":  "",
            "temp_value_7":  "",
            "dens_value_1":  "",
            "weight_value_1":   "",
            "weight_value_2":  "",
            "weight_value_3":  "",
            "bowl_c_value":  "",
            "bowl_h_value":  "",
            "bowl_r_value":  "",
            "bowl_ro_value":  "",
            "bowl_fo_value":  "",
            "screw_c_value":  "",
            "screw_h_value":  "",
            "screw_r_value":  "",
            "screw_ro_value":  "",
            "screw_fo_value":  "",
            "inbear_c_value":  "",
            "inbear_h_value":  "",
            "inbear_r_value":  "",
            "inbear_t_value":  "",
            "inbear_ro_value":  "",
            "inbear_fo_value":  "",
            "outbear_c_value":  "",
            "outbear_h_value":  "",
            "outbear_r_value":  "",
            "outbear_t_value":  "",
            "outbear_ro_value":  "",
            "outbear_fo_value":  ""
        }
        self.db = None
        self.capture_idx = 0
        return

    def connect_to_db(self):
        try:
            self.db = MySQLdb.connect(
                host='localhost',
                user='dbadmin',
                passwd='p@ssw0rd',
                db='bycam_sensor',
                charset='utf8',
                use_unicode=True
            )
            self.db.autocommit(True)
            return True

        except:
            print('Database connection failed')

            return False

    def disconnect(self):
        if self.db:
            self.db.close()

    def get_cursor(self):
        if self.db is None:
            return None

        return self.db.cursor(MySQLdb.cursors.DictCursor)

    def init_signal_handler(self):
        def signal_term_handler(signum, frame):
            self.logger.info("Got TERM signal. Stopping agent.")
            self.stop_agent()

        signal.signal(signal.SIGTERM, signal_term_handler)

    def showpacket(self,packet):

        src_ip = packet[0][1].src
        dst_ip = packet[0][1].dst
        proto = packet[0][1].proto

        if proto in protocols:
            if src_ip == '192.168.0.10' or src_ip == '192.168.0.16':
            #if src_ip == '192.168.0.16':
                print("packet :", packet[0][2].load)
                # print("protocol: %s: %s -> %s" % (protocols[proto], src_ip, dst_ip))
                if packet[0][2].load.find('R') != -1 :
                    result = self.setPlc(src_ip,packet[0][2].load)
                    if result == True :
                        self.insertdb()

    def setPlc(self,ip,data):
        # data = 'LGIS-GLOFA\x03\x01\xa0\x11\x00\x00\x80\x00\x00\xfa\x0f\x00|\x00\x06RE000E000E0005D00550074006700000000000100002000300000000000000000000000000000000000000000000000000000000000000000000000004C'
        # 06RAF00C600BB00C700C800C900C800000000000000170B00003F00000000000000000000000000000055
        if ip == '192.168.0.10' :
            data = data.split('R')[1]
            print("====> data len :", len(data))
            if len(data) == 122 :
                self.plcdatas["temp_value_1"] = data[:2]
                self.plcdatas["temp_value_2"] = data[4:6]
                self.plcdatas["temp_value_3"] = data[8:10]
                self.plcdatas["temp_value_4"] = data[12:14]
                self.plcdatas["temp_value_5"] = data[16:18]
                self.plcdatas["temp_value_6"] = data[20:22]
                self.plcdatas["temp_value_7"] = data[24:26]
                self.plcdatas["dens_value_1"] = data[26:30]
                self.plcdatas["weight_value_1"] = data[54:58]
                self.plcdatas["weight_value_2"] = data[62:66]
                self.plcdatas["weight_value_3"] = data[70:74]
                print("====> temp 1 :", self.plcdatas["temp_value_1"])
                print("====> temp 2 :", self.plcdatas["temp_value_2"])
                print("====> temp 3 :", self.plcdatas["temp_value_3"])
                print("====> temp 4 :", self.plcdatas["temp_value_4"])
                print("====> temp 5 :", self.plcdatas["temp_value_5"])
                print("====> temp 6 :", self.plcdatas["temp_value_6"])
                print("====> temp 7 :", self.plcdatas["temp_value_7"])
                print("====> dense :",self.plcdatas["dens_value_1"])
                print("====> weight_value_1 :", self.plcdatas["weight_value_1"])
                print("====> weight_value_2 :", self.plcdatas["weight_value_2"])
                print("====> weight_value_3 :", self.plcdatas["weight_value_3"])
                return True
        elif ip == '192.168.0.16' :
            data = data.split('R')[1]
            data1 = data[:38]
            data2 = data[38:80]
            data3 = data[80:120]
            data4 = data[120:160]
            self.plcdatas["bowl_c_value"] = data1[:2]
            self.plcdatas["bowl_h_value"] = data1[4:6]
            self.plcdatas["bowl_r_value"] = data1[8:10]
            self.plcdatas["bowl_ro_value"] = data1[19:21]
            self.plcdatas["bowl_fo_value"] = data1[22:24]
            self.plcdatas["screw_c_value"] = data2[2:4]
            self.plcdatas["screw_h_value"] = data2[6:8]
            self.plcdatas["screw_r_value"] = data2[10:12]
            self.plcdatas["screw_ro_value"] = data2[22:24]
            self.plcdatas["screw_fo_value"] = data2[25:27]
            self.plcdatas["inbear_c_value"] = data3[2:4]
            self.plcdatas["inbear_h_value"] = data3[6:8]
            self.plcdatas["inbear_r_value"] = data3[10:12]
            self.plcdatas["inbear_t_value"] = data3[14:16]
            self.plcdatas["inbear_ro_value"] = data3[22:24]
            self.plcdatas["inbear_fo_value"] = data3[25:27]
            self.plcdatas["outbear_c_value"] = data4[2:4]
            self.plcdatas["outbear_h_value"] = data4[6:8]
            self.plcdatas["outbear_r_value"] = data4[10:12]
            self.plcdatas["outbear_t_value"] = data4[14:16]
            self.plcdatas["outbear_ro_value"] = data4[22:24]
            self.plcdatas["outbear_fo_value"] = data4[25:27]
        return False

    def insertdb(self):
        if self.capture_idx % 3600 == 0:
            self.disconnect()
            if not self.connect_to_db():
                self.logger.error("Database initialize failed. Exit.")
                return False
        if self.capture_idx % 6 == 0 :
            cursor = self.get_cursor()
            jsonplcdata = json.dumps(self.plcdatas)
            # print("jsonplcdata :",jsonplcdata)
            sql = '''
                INSERT INTO tb_bycam_sensor(company_id,sensors_msg,created_date) values('0.0.0.0','{0}',now())
                '''.format(jsonplcdata)
            # print("slq : ",sql)
            cursor.execute(sql)
        self.capture_idx += 1

    def run(self):
        print("BychemGrep run...")
        if not self.connect_to_db():
            self.logger.error("Database initialize failed. Exit.")
            return False
        show_interfaces()
        sniff(iface='Realtek PCIe GbE Family Controller',filter='tcp and host 192.168.0.32', prn=self.showpacket,count=0)
        self.disconnect()

if __name__ == "__main__":
    app = BychemGrep(logger=None)
    app.run()


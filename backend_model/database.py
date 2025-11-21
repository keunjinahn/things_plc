#!/usr/bin/python
# -*- coding: utf-8 -*-
print ("module [backend_model.database] loaded")
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import random
import hashlib
from sqlalchemy import or_,and_
import os
import json
import uuid


from flask_sqlalchemy import SQLAlchemy


class DBManager:
    db = None

    @staticmethod
    def init(app):
        # print "-- DBManager init()"
        db = SQLAlchemy(app)
        DBManager.db = db

    @staticmethod
    def init_db():
        print("-- DBManager init_db()")
        db = DBManager.db
        db.drop_all()
        db.create_all()
        #DBManager.insert_dummy_data()

    @staticmethod
    def clear_db():
        print("-- DBManager clear_db()")
        #DBManager.db.drop_all()

    @staticmethod
    def insert_dummy_data():
        print ('insert_dummy_data')
        #DBManager.insert_dummy_device()
        DBManager.insert_dummy_data()

    @staticmethod
    def password_encoder(password):
        pass1 = hashlib.sha1(password).digest()
        pass2 = hashlib.sha1(pass1).hexdigest()
        hashed_pw = "*" + pass2.upper()
        return hashed_pw

    @staticmethod
    def get_random_date():
        end = datetime.utcnow()
        start = end + timedelta(days=-60)

        random_date = start + timedelta(
            # Get a random amount of seconds between `start` and `end`
            seconds=random.randint(0, int((end - start).total_seconds())),
        )

        return random_date

    @staticmethod
    def password_encoder_512(password):
        h = hashlib.sha512()
        h.update(password.encode('utf-8'))
        return h.hexdigest()

    @staticmethod
    def get_random_ip():
        ip_list = [u'28.23.43.1', u'40.12.33.11', u'100.123.234.11', u'61.34.22.44', u'56.34.56.77', u'123.234.222.55']

        return ip_list[random.randrange(0, 6)]

    def insert_dummy_device():
        print("insert_dummy_device")
        from backend_model.table_typhoon import Devices, Workplaces, ProblemItem

        Devices.query.delete()
        ProblemItem.query.delete()
        DBManager.db.session.commit()

        wp_list = Workplaces.query.limit(5).all()

        for wp in wp_list:
            dev = Devices()
            dev.CMPY_ID = wp.CMPY_ID
            dev.COLCTTRMNL_ID = str(random.randrange(10000, 99999))
            dev.JOB_BEGIN_TIME = '09:00'
            dev.JOB_END_TIME = '18:00'
            dev.SW_VER = '1.0.0'
            dev.COLCTTRMNL_STATUS_CD = str(random.randrange(301, 306))
            dev.RGSTER_ID = 1
            dev.RGST_DT = datetime.now()
            DBManager.db.session.add(dev)

        DBManager.db.session.commit()

        devices = Devices.query.all()

        problem_code_list = ['311', '312', '313', '314', '315', '316', '317']

        for i, dev in enumerate(devices):
            cnt = random.randrange(1, len(problem_code_list))
            selected_problem_list = random.choices(problem_code_list, k=cnt)

            selected_problem_list = list(set(selected_problem_list))

            for j, code in enumerate(selected_problem_list):
                pi = ProblemItem()
                pi.CMPY_ID = dev.CMPY_ID
                pi.COLCTTRMNL_ID = dev.COLCTTRMNL_ID
                pi.TROBL_CD = code
                pi.RGSTER_ID = 1
                pi.RGST_DT = datetime.now()

                DBManager.db.session.add(pi)

        DBManager.db.session.commit()

    def insert_dummy_data():
        Devices.query.filter(Devices)
        ph = ProblemHistory()
        #ph.CMPY_ID =



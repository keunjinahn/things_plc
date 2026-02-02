print ("module [backend.api_common] loaded")

import hashlib
from flask import make_response, jsonify, request, json, send_from_directory, g
from flask_restless import ProcessingException
from flask_restful import reqparse
from datetime import datetime, timedelta
import os
import json
from functools import wraps
import pandas as pd
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Color, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend import app, login_manager
from backend_model.table_plc import *
from backend import manager
db = DBManager.db
import random

def prePasswdUpdate(input_params=None, **kw):
    if 'user_pwd' in kw['data']:
        kw['data']['user_pwd'] = password_encoder_512(kw['data']['user_pwd'])
        
manager.create_api(UserTbl
                   , results_per_page=10000
                   , url_prefix='/api/v1'
                   , collection_name='user'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , allow_patch_many=True
                   , preprocessors={
                        'POST': [prePasswdUpdate],
                        'PATCH_SINGLE': [prePasswdUpdate],
                   })            

# PLC 데이터 항목 API 생성
manager.create_api(PlcDataItem
                   , results_per_page=10000
                   , url_prefix='/api/v1'
                   , collection_name='plc-data-items'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , allow_patch_many=True)

# PLC 실시간 데이터 API 생성
manager.create_api(PlcRealTimeData
                   , results_per_page=10000
                   , url_prefix='/api/v1'
                   , collection_name='plc-real-time-data'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , allow_patch_many=True)

# PLC 디바이스 API 생성
manager.create_api(PlcDevice
                   , results_per_page=10000
                   , url_prefix='/api/v1'
                   , collection_name='plc-devices'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , allow_patch_many=True)

# PLC 조회 메모리 관리 API 생성
manager.create_api(PlcQueryMemory
                   , results_per_page=10000
                   , url_prefix='/api/v1'
                   , collection_name='plc-query-memory'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , allow_patch_many=True)

@app.route('/api/v1/login', methods=['POST'])
def login_api():
    data = json.loads(request.data)
    result = ''
    print("111")
    if data['username'] is not None and data['password'] is not None:
        loginuser = db.session.query(UserTbl).filter(UserTbl.user_id == data["username"]).first()

        if loginuser is None:
            result = {'status': False, 'reason': 1}  # ID 없음
        else:
            if loginuser.user_pwd != password_encoder_512(data["password"]):
                result = {'status': False, 'reason': 2} # PW 틀림
                print("222")
            else:  # Login 성공
                if loginuser.user_status == 2:
                    result = {'status': False, 'reason': 3}  # Activation 안됨
                else:
                    print("333")
                    loginuser.token = generate_token(data['username'])
                    db.session.query(UserTbl).filter(UserTbl.user_id == data["username"])\
                        .update(dict(token=loginuser.token))
                    db.session.commit()

                    result = {'status': True, 'reason': 0, 'user': loginuser.serialize()}
    print("444:",result)
    return make_response(jsonify(result), 200)

@app.route("/api/v1/logout", methods=["POST"])
def logout_api():
    parser = reqparse.RequestParser()
    parser.add_argument("token", type=str, location="headers")
    token = parser.parse_args()["token"]
    result = ''
    if token is None:
        print("token is none")

    loginUser = UserTbl.query.filter_by(token=token).first()
    if loginUser is None:
        print("user is none")

    return make_response(jsonify(result), 200)

def generate_token(userID):
    m = hashlib.sha1()

    m.update(userID.encode('utf-8'))
    m.update(datetime.now().isoformat().encode('utf-8'))

    return m.hexdigest()

def check_token(search_params=None, **kw):
    parser = reqparse.RequestParser()
    parser.add_argument("token", type=str, location="headers")
    token = parser.parse_args()["token"]
    if token is None:
        raise ProcessingException(description="Not Authorized", code=410)
    user = UserTbl.query.filter_by(token=token).first()
    if user is None:
        raise ProcessingException(description="Not Authorized", code=411)

def check_token_single(search_params=None, **kw):
    parser = reqparse.RequestParser()
    parser.add_argument("token", type=str, location="headers")
    token = parser.parse_args()["token"]

    if token is None:
        raise ProcessingException(description="Not Authorized", code=410)

    user = UserTbl.query.filter_by(token=token).first()
    if user is None:
        raise ProcessingException(description="Not Authorized", code=411)

def password_encoder_512(password):
    h = hashlib.sha512()
    h.update(password.encode('utf-8'))
    return h.hexdigest()

@app.route('/api/v1/check_passwd', methods=['POST'])
def check_passwd_api():
    print("check_passwd...")
    input = json.loads(request.data)
    user_pwd = input['user_pwd']
    user_id = input['user_id']
    find_user = UserTbl.query.filter_by(user_id=user_id).filter_by(user_pwd=password_encoder_512(user_pwd)).first()
    if find_user is not None :
        return make_response(jsonify({"result":1}), 200)   
    return make_response(jsonify({"result":0}), 200)   

# PLC 데이터 그리드용 API
@app.route('/api/v1/plc/grid-data', methods=['GET'])
def get_plc_grid_data():
    """PLC 데이터 그리드 표시를 위한 데이터 조회 API"""
    try:
        # 활성화된 PLC 데이터 항목 조회
        data_items = db.session.query(PlcDataItem).filter(PlcDataItem.is_active == True).all()
        
        if not data_items:
            return make_response(jsonify({
                "success": True,
                "data": [],
                "message": "데이터 항목이 없습니다."
            }), 200)
        
        # 각 데이터 항목의 최신 실시간 데이터 조회
        grid_data = []
        for item in data_items:
            # 최신 실시간 데이터 조회
            latest_data = db.session.query(PlcRealTimeData)\
                .filter(PlcRealTimeData.data_item_id == item.id)\
                .order_by(PlcRealTimeData.timestamp.desc())\
                .first()
            
            # 디바이스 이름 조회 (안전하게 처리)
            device_name = None
            try:
                if hasattr(item, 'device') and item.device:
                    device_name = item.device.device_name
            except:
                device_name = None
            
            if latest_data:
                grid_data.append({
                    "item_id": item.id,
                    "item_name": item.item_name,
                    "item_type": item.item_type,
                    "address": item.address,
                    "unit": item.unit,
                    "description": item.description,
                    "value": float(latest_data.value) if latest_data.value else None,
                    "quality": latest_data.quality,
                    "timestamp": latest_data.timestamp.isoformat() if latest_data.timestamp else None,
                    "device_name": device_name
                })
            else:
                # 실시간 데이터가 없는 경우 기본값으로 설정
                grid_data.append({
                    "item_id": item.id,
                    "item_name": item.item_name,
                    "item_type": item.item_type,
                    "address": item.address,
                    "unit": item.unit,
                    "description": item.description,
                    "value": None,
                    "quality": "uncertain",
                    "timestamp": None,
                    "device_name": device_name
                })
        
        return make_response(jsonify({
            "success": True,
            "data": grid_data,
            "message": "데이터 조회 성공"
        }), 200)
        
    except Exception as e:
        print(f"PLC 그리드 데이터 조회 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "data": [],
            "message": f"데이터 조회 실패: {str(e)}"
        }), 500)

@app.route('/api/v1/plc/real-time-data', methods=['GET'])
def get_plc_real_time_data():
    """PLC 실시간 데이터 조회 API (필터링 지원)"""
    try:
        # 쿼리 파라미터 파싱
        item_id = request.args.get('item_id', type=int)
        quality = request.args.get('quality', type=str)
        limit = request.args.get('limit', type=int, default=110)
        
        # 기본 쿼리
        query = db.session.query(PlcRealTimeData)
        
        # 필터 적용
        if item_id:
            query = query.filter(PlcRealTimeData.data_item_id == item_id)
        if quality:
            query = query.filter(PlcRealTimeData.quality == quality)
        
        # 최신 데이터 순으로 정렬하고 제한
        real_time_data = query.order_by(PlcRealTimeData.timestamp.desc()).limit(limit).all()
        
        # 데이터 직렬화
        data = []
        for item in real_time_data:
            # 디바이스 이름 조회 (안전하게 처리)
            device_name = None
            try:
                if hasattr(item, 'data_item') and item.data_item and hasattr(item.data_item, 'device') and item.data_item.device:
                    device_name = item.data_item.device.device_name
            except:
                device_name = None
            data.append({
                "id": item.id,
                "data_item_id": item.data_item_id,
                "value": item.value,
                "quality": item.quality,
                "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                "item_name": item.data_item.item_name if item.data_item else None,
                "item_type": item.data_item.item_type if item.data_item else None,
                "address": item.data_item.address if item.data_item else None,
                "unit": item.data_item.unit if item.data_item else None,
                "device_name": device_name
            })
        print("data len : ", len(data))
        return make_response(jsonify({
            "success": True,
            "data": data,
            "message": "실시간 데이터 조회 성공"
        }), 200)
        
    except Exception as e:
        print(f"PLC 실시간 데이터 조회 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "data": [],
            "message": f"데이터 조회 실패: {str(e)}"
        }), 500)

@app.route('/api/v1/plc/data-items', methods=['GET'])
def get_plc_data_items():
    """PLC 데이터 항목 조회 API (활성화된 항목만)"""
    try:
        # 활성화된 데이터 항목만 조회
        data_items = db.session.query(PlcDataItem).filter(PlcDataItem.is_active == True).all()
        
        # 데이터 직렬화
        items = []
        for item in data_items:
            # 디바이스 이름 조회 (안전하게 처리)
            device_name = None
            try:
                if hasattr(item, 'device') and item.device:
                    device_name = item.device.device_name
            except:
                device_name = None
            
            items.append({
                "id": item.id,
                "plc_device_id": item.plc_device_id,
                "item_name": item.item_name,
                "item_type": item.item_type,
                "address": item.address,
                "modbus_address": item.modbus_address,
                "modbus_function": item.modbus_function,
                "description": item.description,
                "unit": item.unit,
                "min_value": float(item.min_value) if item.min_value else None,
                "max_value": float(item.max_value) if item.max_value else None,
                "is_active": item.is_active,
                "action_item": item.action_item,
                "line_number": item.line_number,
                "source_line": item.source_line,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "device_name": device_name
            })
        
        return make_response(jsonify({
            "success": True,
            "data": items,
            "message": "데이터 항목 조회 성공"
        }), 200)
        
    except Exception as e:
        print(f"PLC 데이터 항목 조회 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "data": [],
            "message": f"데이터 조회 실패: {str(e)}"
        }), 500)

@app.route('/api/v1/plc/memory-items', methods=['GET'])
def get_plc_memory_items():
    """PLC 메모리 항목 전체 조회 API (is_active 필터 없음)"""
    try:
        # 전체 데이터 항목 조회 (is_active 필터 없음)
        data_items = db.session.query(PlcDataItem).order_by(PlcDataItem.item_type, PlcDataItem.modbus_address).all()
        
        # 데이터 직렬화
        items = []
        for item in data_items:
            # 디바이스 이름 조회 (안전하게 처리)
            device_name = None
            try:
                if hasattr(item, 'device') and item.device:
                    device_name = item.device.device_name
            except:
                device_name = None
            
            items.append({
                "id": item.id,
                "plc_device_id": item.plc_device_id,
                "item_name": item.item_name,
                "item_type": item.item_type,
                "address": item.address,
                "modbus_address": item.modbus_address,
                "modbus_function": item.modbus_function,
                "description": item.description,
                "unit": item.unit,
                "min_value": float(item.min_value) if item.min_value else None,
                "max_value": float(item.max_value) if item.max_value else None,
                "is_active": item.is_active,
                "action_item": item.action_item,
                "line_number": item.line_number,
                "source_line": item.source_line,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "device_name": device_name
            })
        
        return make_response(jsonify({
            "success": True,
            "data": items,
            "message": "메모리 항목 조회 성공"
        }), 200)
        
    except Exception as e:
        print(f"PLC 메모리 항목 조회 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "data": [],
            "message": f"데이터 조회 실패: {str(e)}"
        }), 500)

@app.route('/api/v1/plc/memory-items/<int:item_id>/toggle-active', methods=['PATCH'])
def toggle_plc_memory_item_active(item_id):
    """PLC 메모리 항목의 is_active 상태 토글"""
    try:
        # 항목 조회
        item = db.session.query(PlcDataItem).filter(PlcDataItem.id == item_id).first()
        
        if not item:
            return make_response(jsonify({
                "success": False,
                "message": "항목을 찾을 수 없습니다"
            }), 404)
        
        # is_active 상태 토글
        item.is_active = not item.is_active
        db.session.commit()
        
        return make_response(jsonify({
            "success": True,
            "data": {
                "id": item.id,
                "is_active": item.is_active
            },
            "message": "상태 업데이트 성공"
        }), 200)
        
    except Exception as e:
        db.session.rollback()
        print(f"PLC 메모리 항목 상태 업데이트 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "message": f"상태 업데이트 실패: {str(e)}"
        }), 500)

@app.route('/api/v1/plc/memory-items/<int:item_id>/toggle-action-item', methods=['PATCH'])
def toggle_plc_memory_item_action(item_id):
    """PLC 메모리 항목의 action_item 상태 토글 (단일 선택: 체크 시 다른 항목 모두 un체크)"""
    try:
        # 항목 조회
        item = db.session.query(PlcDataItem).filter(PlcDataItem.id == item_id).first()

        if not item:
            return make_response(jsonify({
                "success": False,
                "message": "항목을 찾을 수 없습니다"
            }), 404)

        # action_item이 체크되는 경우 (현재 false -> true)
        if not item.action_item:
            # 다른 모든 항목의 action_item을 false로 설정
            db.session.query(PlcDataItem).filter(PlcDataItem.id != item_id).update({PlcDataItem.action_item: False})
            # 현재 항목을 true로 설정
            item.action_item = True
        else:
            # action_item이 un체크되는 경우 (현재 true -> false)
            item.action_item = False

        db.session.commit()

        return make_response(jsonify({
            "success": True,
            "data": {
                "id": item.id,
                "action_item": item.action_item
            },
            "message": "액션 항목 상태 업데이트 성공"
        }), 200)

    except Exception as e:
        db.session.rollback()
        print(f"PLC 메모리 항목 액션 상태 업데이트 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "message": f"액션 상태 업데이트 실패: {str(e)}"
        }), 500)

@app.route('/api/v1/plc/query-memory-realtime', methods=['GET'])
def get_plc_query_memory_realtime():
    """plc_query_memory 기반 실시간 데이터 조회 API

    1. plc_query_memory 테이블의 항목들을 조회
    2. memory_address와 plc_data_items의 item_name이 일치하는 id를 찾음
    3. plc_real_time_data에서 해당 data_item_id의 가장 최근 value를 조회
    """
    try:
        # 1. plc_query_memory 테이블에서 활성화된 항목들 조회
        query_memory_items = db.session.query(PlcQueryMemory)\
            .filter(PlcQueryMemory.is_active == True)\
            .order_by(PlcQueryMemory.id)\
            .all()

        if not query_memory_items:
            return make_response(jsonify({
                "success": True,
                "data": [],
                "message": "조회 메모리 항목이 없습니다."
            }), 200)

        result_data = []

        for query_item in query_memory_items:
            # 2. memory_address와 plc_data_items의 item_name이 일치하는 항목 찾기
            data_item = db.session.query(PlcDataItem)\
                .filter(PlcDataItem.item_name == query_item.memory_address)\
                .first()

            if data_item:
                # 3. plc_real_time_data에서 해당 data_item_id의 가장 최근 value 조회
                latest_data = db.session.query(PlcRealTimeData)\
                    .filter(PlcRealTimeData.data_item_id == data_item.id)\
                    .order_by(PlcRealTimeData.timestamp.desc())\
                    .first()

                result_data.append({
                    "query_memory_id": query_item.id,
                    "item_name": query_item.item_name,
                    "memory_address": query_item.memory_address,
                    "description": query_item.description,
                    "data_item_id": data_item.id,
                    "action_item": data_item.action_item,
                    "value": float(latest_data.value) if latest_data and latest_data.value else None,
                    "quality": latest_data.quality if latest_data else "uncertain",
                    "timestamp": latest_data.timestamp.isoformat() if latest_data and latest_data.timestamp else None
                })
            else:
                # data_item을 찾지 못한 경우
                result_data.append({
                    "query_memory_id": query_item.id,
                    "item_name": query_item.item_name,
                    "memory_address": query_item.memory_address,
                    "description": query_item.description,
                    "data_item_id": None,
                    "action_item": False,
                    "value": None,
                    "quality": "uncertain",
                    "timestamp": None
                })

        return make_response(jsonify({
            "success": True,
            "data": result_data,
            "message": "조회 메모리 실시간 데이터 조회 성공"
        }), 200)

    except Exception as e:
        print(f"조회 메모리 실시간 데이터 조회 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "data": [],
            "message": f"데이터 조회 실패: {str(e)}"
        }), 500)


@app.route('/api/v1/plc/realtime-data-input', methods=['POST'])
def post_plc_realtime_data_input():
    """PLC 실시간 데이터 입력 API (plc_real_time_data 테이블에 저장)

    요청 Body:
    {
        "data_item_id": int,   // plc_data_items 테이블의 id
        "value": number,       // 10진수 값
        "quality": string      // 데이터 품질 (기본값: 'good')
    }
    """
    try:
        data = json.loads(request.data)

        data_item_id = data.get('data_item_id')
        value = data.get('value')
        quality = data.get('quality', 'good')

        if data_item_id is None:
            return make_response(jsonify({
                "success": False,
                "message": "data_item_id가 필요합니다."
            }), 400)

        if value is None:
            return make_response(jsonify({
                "success": False,
                "message": "value가 필요합니다."
            }), 400)

        # data_item 존재 여부 확인
        data_item = db.session.query(PlcDataItem).filter(PlcDataItem.id == data_item_id).first()
        if not data_item:
            return make_response(jsonify({
                "success": False,
                "message": f"data_item_id {data_item_id}에 해당하는 항목이 없습니다."
            }), 404)

        # 새 실시간 데이터 레코드 생성
        new_record = PlcRealTimeData(
            data_item_id=data_item_id,
            value=float(value),
            quality=quality,
            timestamp=datetime.now()
        )

        db.session.add(new_record)
        db.session.commit()

        # 16진수 변환 (로그용)
        hex_value = hex(int(value)).upper().replace('0X', '0x')

        print(f"실시간 데이터 저장: data_item_id={data_item_id}, value={value} ({hex_value}), quality={quality}")

        return make_response(jsonify({
            "success": True,
            "data": {
                "id": new_record.id,
                "data_item_id": new_record.data_item_id,
                "value": new_record.value,
                "hex_value": hex_value,
                "quality": new_record.quality,
                "timestamp": new_record.timestamp.isoformat() if new_record.timestamp else None
            },
            "message": "데이터 저장 성공"
        }), 201)

    except Exception as e:
        db.session.rollback()
        print(f"실시간 데이터 저장 오류: {str(e)}")
        return make_response(jsonify({
            "success": False,
            "message": f"데이터 저장 실패: {str(e)}"
        }), 500)

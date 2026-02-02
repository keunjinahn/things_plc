<template>
    <div ref="sceneContainer" class="plc-monitor-3d">
        <!-- 3D 장면 오버레이 -->
        <div class="overlay-container">
            <!-- PLC 모니터링 헤더 -->
            <div class="monitor-header">
                <div class="header-content">
                    <h1 class="page-title">
                        <i class="las la-microchip"></i>
                        용접철망 디지털트윈
                    </h1>
                    <p class="page-subtitle">3D 실시간 데이터 모니터링</p>
                </div>
                <div class="header-actions">
                    <button class="btn btn-primary" @click="refreshData">
                        <i class="las la-sync"></i>
                        새로고침
                    </button>
                    <button class="btn btn-success" @click="startMonitoring">
                        <i class="las la-play"></i>
                        시작
                    </button>
                    <button class="btn btn-warning" @click="pauseMonitoring">
                        <i class="las la-pause"></i>
                        일시정지
                    </button>
                </div>
            </div>

            <!-- PLC 상태 정보 패널 -->
            <div class="status-panel">
                <div class="status-card">
                    <div class="status-icon">
                        <i class="las la-server"></i>
                    </div>
                    <div class="status-content">
                        <h4>PLC 연결</h4>
                        <p class="status-value connected">연결됨</p>
                        <small>192.168.1.100:2004</small>
                    </div>
                </div>
                
                <div class="status-card">
                    <div class="status-icon">
                        <i class="las la-database"></i>
                    </div>
                    <div class="status-content">
                        <h4>데이터 수집</h4>
                        <p class="status-value active">활성</p>
                        <small>104개 항목, 1초 주기</small>
                    </div>
                </div>
                
                <div class="status-card">
                    <div class="status-icon">
                        <i class="las la-chart-line"></i>
                    </div>
                    <div class="status-content">
                        <h4>데이터 품질</h4>
                        <p class="status-value good">98.5%</p>
                        <small>최근 24시간</small>
                    </div>
                </div>
                
                <div class="status-card">
                    <div class="status-icon">
                        <i class="las la-cube"></i>
                    </div>
                    <div class="status-content">
                        <h4>철망 제품 상태</h4>
                        <p class="status-value active">
                            대기: {{ currentItem3Index + 1 }}개 / 중간: {{ movedItem3Count }}개 / 적재: {{ stackedItem3Count }}개
                        </p>
                        <div class="button-group">
                            <div class="button-row">
                                <span class="button-label">제품 이동</span>
                                <button @click="onItem3Click" class="apply-btn" :disabled="item3AnimationState === 'moving' || currentItem3Index < 0">
                                    {{ item3AnimationState === 'moving' ? '이동 중...' : '적용' }}
                                </button>
                            </div>
                            <div class="button-row">
                                <span class="button-label">제품 회전</span>
                                <button @click="onProductRotate" class="apply-btn" :disabled="item3RotationState === 'rotating' || item3Models.length === 0">
                                    {{ item3RotationState === 'rotating' ? '회전 중...' : '적용' }}
                                </button>
                            </div>
                            <div class="button-row">
                                <span class="button-label">제품 적재</span>
                                <button @click="onProductStack" class="apply-btn" :disabled="item3StackState === 'stacking' || item3Models.length === 0">
                                    {{ item3StackState === 'stacking' ? '적재 중...' : '적용' }}
                                </button>
                            </div>
                            <div class="button-row">
                                <span class="button-label">초기화</span>
                                <button @click="onResetItems" class="apply-btn reset-btn" :disabled="item3AnimationState === 'moving' || item3RotationState === 'rotating' || item3StackState === 'stacking'">
                                    초기화
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="status-card">
                    <div class="status-icon">
                        <i class="las la-layer-group"></i>
                    </div>
                    <div class="status-content">
                        <h4>적층상태</h4>
                        <div class="stack-status-list">
                            <div class="stack-status-row">
                                <span class="stack-label">현재 적층 수량</span>
                                <span class="stack-value current">{{ movedItem3Count }}</span>
                            </div>
                            <div class="stack-status-row">
                                <span class="stack-label">묶음 적층 수량</span>
                                <span class="stack-value bundle">{{ bundleStackCount }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 실시간 데이터 표시 -->
            <div class="data-panel">
                <h3>실시간 데이터</h3>
                <div class="data-grid">
                    <div
                        class="data-item"
                        :class="{ 'blinking': isActionItemBlinking(item) }"
                        v-for="(item, index) in filteredRealTimeData"
                        :key="index"
                    >
                        <span class="data-label">{{ item.item_name }}</span>
                        <span class="data-address">{{ item.memory_address }}</span>
                        <span class="data-value" :class="getValueClass(item.value)">
                            {{ formatValue(item.value) }}
                        </span>
                    </div>
                </div>
            </div>

            <!-- 카메라 컨트롤 안내 -->
            <div class="camera-controls">
                <div class="control-info">
                    <i class="las la-mouse"></i>
                    <span>마우스로 회전, 휠로 확대/축소</span>
                </div>
                <div class="control-info">
                    <i class="las la-keyboard"></i>
                    <span>스페이스바로 자동 회전</span>
                </div>
            </div>

            <!-- 데이터 입력 버튼 (오른쪽 하단) -->
            <button class="data-input-btn" @click="openDataInputPopup">
                <i class="las la-edit"></i>
                데이터
            </button>

            <!-- 데이터 입력 팝업 레이어 (Modeless, 드래그 가능) -->
            <div
                class="data-input-popup"
                v-if="showDataInputPopup"
                :style="{ left: popupPosition.x + 'px', top: popupPosition.y + 'px' }"
            >
                <div class="popup-header" @mousedown="startDragPopup">
                    <h3><i class="las la-database"></i> 데이터 입력</h3>
                    <button class="popup-close-btn" @click="closeDataInputPopup" @mousedown.stop>
                        <i class="las la-times"></i>
                    </button>
                </div>
                <div class="popup-body">
                    <div class="data-input-list">
                        <div
                            class="data-input-item"
                            v-for="(item, index) in realTimeData"
                            :key="index"
                        >
                            <div class="input-item-row">
                                <span class="input-item-name">{{ item.item_name }}</span>
                                <span class="input-item-current">{{ formatValue(item.value) }}</span>
                                <input
                                    type="number"
                                    v-model.number="dataInputValues[item.memory_address]"
                                    :placeholder="formatValue(item.value)"
                                    class="data-input-field"
                                    @keyup.enter="submitDataValue(item)"
                                />
                                <span class="hex-preview" v-if="dataInputValues[item.memory_address] !== undefined && dataInputValues[item.memory_address] !== ''">
                                    0x{{ toHex(dataInputValues[item.memory_address]) }}
                                </span>
                                <button
                                    class="submit-btn"
                                    @click="submitDataValue(item)"
                                    :disabled="dataInputValues[item.memory_address] === undefined || dataInputValues[item.memory_address] === ''"
                                >
                                    적용
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="popup-footer">
                    <button class="popup-close-action" @click="closeDataInputPopup">
                        <i class="las la-times"></i> 닫기
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

// PLC 주소 상수 (하드코딩)
const PLC_ADDRESS_PRODUCT_MOVE = 'D4123';    // 제품이동 주소
const PLC_ADDRESS_PRODUCT_ROTATE = 'D4407';  // 제품회전 주소
const PLC_ADDRESS_PRODUCT_STACK = 'D4625';   // 제품적재 주소

export default {
    name: 'PLCMonitor3D',
    data() {
        return {
            // Three.js 관련 변수
            scene: null,
            camera: null,
            renderer: null,
            controls: null,
            clock: null,
            deviceModel: null,
            isRotating: false,
            rotationSpeed: Math.PI / 36,
            
            // PLC 모니터링 관련 데이터
            plcStatus: {
                connected: true,
                ip: '192.168.1.100',
                port: 2004,
                protocol: 'Modbus TCP'
            },
            dataCollection: {
                active: true,
                items: 104,
                interval: 1000,
                lastUpdate: new Date()
            },
            database: {
                status: 'good',
                records: 1250,
                size: '2.5MB',
                backup: 'latest'
            },
            
            // 실시간 데이터
            realTimeData: [],
            
            // is_active가 true인 항목들만 필터링 (동적으로 로드)
            targetItems: [],
            
            // action_item이 true인 항목 (Item3 클릭 효과용)
            actionItemName: null,
            
            // 애니메이션 관련
            animationId: null,
            dataUpdateInterval: null,
            
            // 3D 모델 관련 - 철망 리스트로 관리
            item3Models: [], // 철망 모델 배열
            item3Count: 10, // 총 철망 개수 (bundleStackCount와 동기화)
            item3HeightGap: 0.01, // 철망 간 높이 간격 (5배 줄임)
            item3BaseY: -0.48, // 기본 Y 위치
            item3OriginalModel: null, // 원본 철망 모델 (복제용)
            item3ModelCenter: null, // 모델 중심점
            item3ModelSize: null, // 모델 크기

            // 각 철망의 개별 상태 관리
            item3States: [], // 각 철망의 상태 배열 [{position, rotation, animationState, ...}, ...]

            // 현재 애니메이션 중인 철망 인덱스 (맨 위부터 = 배열의 마지막부터)
            currentItem3Index: -1,

            // 적재된 철망 개수 (목표 위치에 쌓인 개수)
            stackedItem3Count: 0,

            // 묶음 적층 수량 (디폴트 10개)
            bundleStackCount: 10,

            // 현재 적층 수량 (실시간 데이터에서 조회)
            currentStackCount: 0,
            // 이전 적층 수량 (변화 감지용)
            prevStackCount: 0,
            // 대기 중인 이동 개수
            pendingMoves: 0,

            // 묶음회전중 상태 (실시간 데이터에서 조회)
            bundleRotatingValue: 0,
            bundleRotatingItem: null,  // 해당 항목 정보 저장

            // 배출 제품 이송 상태 (실시간 데이터에서 조회)
            productTransferValue: 0,
            productTransferItem: null,  // 해당 항목 정보 저장

            // 적층수량 항목 정보 저장 (DB 업데이트용)
            stackCountItem: null,

            // 애니메이션 완료 후 값 재설정 대기 항목
            pendingRotateReset: null,
            pendingStackReset: null,

            // 공통 애니메이션 관련
            item3AnimationState: 'idle', // 'idle', 'moving', 'completed'
            item3AnimationProgress: 0,
            item3StartPosition: { x: -2.0, y: -0.48, z: 0 }, // 시작 위치 (초기 위치)
            item3TargetPosition: { x: 0, y: -0.48, z: 0 }, // 목표 위치 (중간 지점)

            // 회전 애니메이션 관련
            item3RotationState: 'idle', // 'idle', 'rotating', 'completed'
            item3RotationProgress: 0,
            item3StartRotation: 0, // 시작 회전 각도
            item3TargetRotation: 0, // 목표 회전 각도 (90도)

            // 적재 애니메이션 관련
            item3StackState: 'idle', // 'idle', 'stacking', 'completed'
            item3StackProgress: 0,
            item3StackStartPosition: { x: 0, y: 0, z: 0 }, // 적재 시작 위치
            item3StackTargetPosition: { x: 0, y: 0, z: 0 }, // 적재 목표 위치 (X축 +2)
            item3FinalStackX: 1.95, // 최종 적재 X 위치 (기존 1.3의 150%)

            // 중간 위치에 쌓인 철망 개수
            movedItem3Count: 0,

            // 버튼 상태값 (1 또는 0) - 하드코딩된 초기값
            productMoveState: 0,      // 제품이동 상태 (D4123)
            productRotateState: 0,    // 제품회전 상태 (D4407)
            productStackState: 0,     // 제품적재 상태 (D4625)

            // 데이터 입력 팝업 관련
            showDataInputPopup: false,  // 팝업 표시 여부
            dataInputValues: {},        // 각 항목별 입력값 저장 { memory_address: value }
            popupPosition: { x: 100, y: 150 },  // 팝업 위치
            isDraggingPopup: false,     // 드래그 중 여부
            dragOffset: { x: 0, y: 0 }  // 드래그 오프셋
        };
    },
    computed: {
        // plc_query_memory 기반 실시간 데이터 표시 (이미 필터링된 데이터)
        filteredRealTimeData() {
            return this.realTimeData.map(item => ({
                item_name: item.item_name || '',
                memory_address: item.memory_address || '',
                value: item.value,
                quality: item.quality || 'uncertain',
                timestamp: item.timestamp
            }));
        }
    },
    watch: {
        // 묶음수량 변경 시 철망 개수 재생성
        bundleStackCount(newCount, oldCount) {
            if (newCount !== oldCount && newCount > 0 && this.item3OriginalModel) {
                console.log(`묶음수량 변경: ${oldCount} -> ${newCount}`);
                this.regenerateItem3Models(newCount);
            }
        }
    },
    mounted() {
        this.initialize3DScene();
        this.fetchQueryMemoryRealTimeData();
        this.startDataUpdate();
        window.addEventListener('keydown', this.handleKeyPress);
    },
    beforeDestroy() {
        this.stopDataUpdate();
        this.cleanup();
        window.removeEventListener('keydown', this.handleKeyPress);
        document.removeEventListener('mousemove', this.onDragPopup);
        document.removeEventListener('mouseup', this.stopDragPopup);
    },
    methods: {
        initialize3DScene() {
            const container = this.$refs.sceneContainer;
            const width = container.clientWidth;
            const height = container.clientHeight;

            // Scene 설정
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0x4a5568);
            this.scene.fog = new THREE.Fog(0x4a5568, 20, 100);

            // Clock 초기화
            this.clock = new THREE.Clock();

            // Camera 설정
            this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
            this.camera.position.set(5, 5, 5);
            this.camera.lookAt(0, 0, 0);

            // Renderer 설정 - 더 밝게
            this.renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                alpha: true,
                toneMapping: THREE.ACESFilmicToneMapping,
                toneMappingExposure: 1.2
            });
            this.renderer.setSize(width, height);
            this.renderer.setPixelRatio(window.devicePixelRatio);
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            this.renderer.outputEncoding = THREE.sRGBEncoding;
            container.appendChild(this.renderer.domElement);

            // 조명 설정 - 더 밝게
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
            this.scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5);
            directionalLight.position.set(10, 10, 5);
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 2048;
            directionalLight.shadow.mapSize.height = 2048;
            this.scene.add(directionalLight);

            // 추가 조명 - 측면 조명
            const sideLight = new THREE.DirectionalLight(0xffffff, 0.8);
            sideLight.position.set(-10, 5, 5);
            this.scene.add(sideLight);

            // 추가 조명 - 후면 조명
            const backLight = new THREE.DirectionalLight(0xffffff, 0.6);
            backLight.position.set(0, 5, -10);
            this.scene.add(backLight);

            // 바닥 생성
            this.createFloor();

            // PLC 장비 모델 로드
            this.loadDeviceModel();
            
            // Item3 모델 로드
            this.loadItem3Model();

            // OrbitControls 설정
            this.controls = new OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.screenSpacePanning = false;
            this.controls.minDistance = 2;
            this.controls.maxDistance = 20;
            this.controls.maxPolarAngle = Math.PI / 2;

            // 애니메이션 시작
            this.animate();

            // 리사이즈 이벤트
            window.addEventListener('resize', this.onWindowResize);
        },

        createFloor() {
            const floorGeometry = new THREE.PlaneGeometry(20, 20);
            const floorMaterial = new THREE.MeshStandardMaterial({
                color: 0x718096,
                roughness: 0.6,
                metalness: 0.1
            });
            const floor = new THREE.Mesh(floorGeometry, floorMaterial);
            floor.rotation.x = -Math.PI / 2;
            floor.receiveShadow = true;
            this.scene.add(floor);

            // 그리드 추가 - 더 밝게
            const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0x666666);
            this.scene.add(gridHelper);
        },

        loadDeviceModel() {
            const loader = new GLTFLoader();
            
            // GLB 파일 로드 (상대 경로로 수정)
            loader.load('/plc/3D/device_v2blend.glb', (gltf) => {
                this.deviceModel = gltf.scene;
                
                // 모델 스케일 조정
                this.deviceModel.scale.set(2, 2, 2);
                
                // 모델 위치 설정
                this.deviceModel.position.set(0, 0, 0);
                
                // 그림자 설정
                this.deviceModel.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                        
                        // 재질 개선
                        if (child.material) {
                            child.material.metalness = 0.8;
                            child.material.roughness = 0.2;
                        }
                    }
                });
                
                this.scene.add(this.deviceModel);
                console.log('PLC 장비 모델 로드 완료');
                
            }, undefined, (error) => {
                console.error('모델 로드 실패:', error);
                // 모델 로드 실패 시 기본 박스 생성
                this.createFallbackDevice();
            });
        },

        createFallbackDevice() {
            // 모델 로드 실패 시 기본 PLC 장비 생성
            const deviceGroup = new THREE.Group();
            
            // 메인 본체 - 더 밝게
            const bodyGeometry = new THREE.BoxGeometry(2, 1, 1);
            const bodyMaterial = new THREE.MeshStandardMaterial({
                color: 0x555555,
                metalness: 0.6,
                roughness: 0.3
            });
            const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
            body.castShadow = true;
            body.receiveShadow = true;
            deviceGroup.add(body);
            
            // LED 표시등들
            const ledGeometry = new THREE.SphereGeometry(0.1, 8, 8);
            const ledPositions = [
                { x: -0.8, y: 0.6, z: 0.5, color: 0x00ff00 },
                { x: 0, y: 0.6, z: 0.5, color: 0xffff00 },
                { x: 0.8, y: 0.6, z: 0.5, color: 0xff0000 }
            ];
            
            ledPositions.forEach(pos => {
                const ledMaterial = new THREE.MeshBasicMaterial({
                    color: pos.color,
                    emissive: pos.color,
                    emissiveIntensity: 0.5
                });
                const led = new THREE.Mesh(ledGeometry, ledMaterial);
                led.position.set(pos.x, pos.y, pos.z);
                deviceGroup.add(led);
            });
            
            // 포트 표시 - 더 밝게
            const portGeometry = new THREE.CylinderGeometry(0.05, 0.05, 0.2, 8);
            const portMaterial = new THREE.MeshStandardMaterial({ color: 0x888888 });
            for (let i = 0; i < 4; i++) {
                const port = new THREE.Mesh(portGeometry, portMaterial);
                port.position.set(-0.6 + i * 0.4, -0.4, 0.5);
                port.rotation.x = Math.PI / 2;
                deviceGroup.add(port);
            }
            
            this.deviceModel = deviceGroup;
            this.scene.add(this.deviceModel);
            console.log('기본 PLC 장비 생성 완료');
        },

        loadItem3Model() {
            const loader = new GLTFLoader();

            // Item3 GLB 파일 로드
            loader.load('/plc/3D/item3.glb', (gltf) => {
                const originalModel = gltf.scene;

                // 모델 스케일 조정
                originalModel.scale.set(2, 2, 2);
                originalModel.updateMatrixWorld(true);

                // 바운딩 박스로 geometry 중심 계산
                const box = new THREE.Box3().setFromObject(originalModel);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());

                // 원본 모델 및 정보 저장 (재생성용)
                this.item3OriginalModel = originalModel;
                this.item3ModelCenter = center;
                this.item3ModelSize = size;

                // bundleStackCount에 따라 철망 생성
                this.item3Count = this.bundleStackCount;
                this.createItem3Models(this.item3Count);

                console.log(`Item3 모델 ${this.item3Count}개 로드 완료 (묶음수량 기준)`);
                console.log(`Geometry 크기: ${size.x.toFixed(2)} x ${size.y.toFixed(2)} x ${size.z.toFixed(2)}`);

            }, undefined, (error) => {
                console.error('Item3 모델 로드 실패:', error);
            });
        },

        // 철망 모델 생성 (지정된 개수만큼)
        createItem3Models(count) {
            if (!this.item3OriginalModel || !this.item3ModelCenter) {
                console.warn('원본 모델이 로드되지 않았습니다.');
                return;
            }

            const center = this.item3ModelCenter;
            const initialX = -2.0;
            const initialZ = 0;

            this.item3Models = [];
            this.item3States = [];

            for (let i = 0; i < count; i++) {
                // 모델 복제
                const clonedModel = this.item3OriginalModel.clone();

                // 피벗 그룹 생성 (이 그룹이 회전의 중심이 됨)
                const item3Group = new THREE.Group();

                // 복제된 모델을 그룹에 추가하고, 중심이 그룹 원점에 오도록 오프셋
                clonedModel.position.set(-center.x, -center.y, -center.z);
                item3Group.add(clonedModel);

                // 각 철망의 Y 위치 계산 (아래에서 위로 쌓임, i=0이 맨 아래)
                const initialY = this.item3BaseY + center.y + (i * this.item3HeightGap);

                // 모델 초기 위치 설정
                item3Group.position.set(initialX, initialY, initialZ);
                item3Group.rotation.y = 0;

                // 그림자 설정
                clonedModel.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;

                        // 재질 개선
                        if (child.material) {
                            child.material = child.material.clone();
                            child.material.metalness = 0.7;
                            child.material.roughness = 0.3;
                        }
                    }
                });

                // 배열에 추가
                this.item3Models.push(item3Group);

                // 각 철망의 상태 초기화
                this.item3States.push({
                    position: { x: initialX, y: initialY, z: initialZ },
                    rotation: 0,
                    animationState: 'idle',
                    animationProgress: 0,
                    startPosition: { x: initialX, y: initialY, z: initialZ },
                    targetPosition: { x: 0, y: initialY, z: initialZ },
                    startRotation: 0,
                    targetRotation: 0
                });

                // Scene에 추가
                if (this.deviceModel) {
                    this.deviceModel.add(item3Group);
                } else {
                    this.scene.add(item3Group);
                }
            }

            // 현재 애니메이션 대상 인덱스 초기화 (맨 위 = 마지막 인덱스)
            this.currentItem3Index = count - 1;
            this.item3Count = count;
        },

        // 기존 철망 모델 제거
        clearItem3Models() {
            // Scene에서 기존 철망 모델 제거
            for (const model of this.item3Models) {
                if (this.deviceModel) {
                    this.deviceModel.remove(model);
                } else if (this.scene) {
                    this.scene.remove(model);
                }
                // 메모리 해제
                model.traverse((child) => {
                    if (child.geometry) {
                        child.geometry.dispose();
                    }
                    if (child.material) {
                        if (Array.isArray(child.material)) {
                            child.material.forEach(m => m.dispose());
                        } else {
                            child.material.dispose();
                        }
                    }
                });
            }
            this.item3Models = [];
            this.item3States = [];
        },

        // 철망 모델 재생성 (묶음수량 변경 시)
        regenerateItem3Models(newCount) {
            // 기존 모델 제거
            this.clearItem3Models();

            // 애니메이션 상태 초기화
            this.movedItem3Count = 0;
            this.stackedItem3Count = 0;
            this.item3AnimationState = 'idle';
            this.item3AnimationProgress = 0;
            this.item3RotationState = 'idle';
            this.item3RotationProgress = 0;
            this.item3StackState = 'idle';
            this.item3StackProgress = 0;
            this.pendingMoves = 0;
            this.currentStackCount = 0;
            this.prevStackCount = 0;
            this.bundleRotatingValue = 0;
            this.productTransferValue = 0;
            this.pendingRotateReset = null;
            this.pendingStackReset = null;

            // 새 개수로 모델 생성
            this.createItem3Models(newCount);

            console.log(`철망 모델 재생성 완료: ${newCount}개`);
        },

        animate() {
            this.animationId = requestAnimationFrame(this.animate);
            
            const elapsedTime = this.clock.getElapsedTime();
            
            // 자동 회전 - device_v2blend만 회전 (item3은 자식으로 따라감)
            if (this.isRotating && this.deviceModel) {
                this.deviceModel.rotation.y += this.rotationSpeed * 0.1;
            }
            
            // LED 깜빡임 효과
            if (this.deviceModel) {
                this.deviceModel.traverse((child) => {
                    if (child.material && child.material.emissive) {
                        const intensity = 0.5 + Math.sin(elapsedTime * 5) * 0.3;
                        child.material.emissiveIntensity = intensity;
                    }
                });
            }
            
            // Item3 모델 애니메이션
            if (this.item3Models.length > 0) {
                // 제품 이동 애니메이션 - 현재 철망 1개만 이동
                if (this.item3AnimationState === 'moving' && this.currentItem3Index >= 0) {
                    const currentModel = this.item3Models[this.currentItem3Index];
                    const currentState = this.item3States[this.currentItem3Index];

                    if (currentModel && currentState) {
                        this.item3AnimationProgress += 0.01;

                        // easing 적용
                        const t = this.item3AnimationProgress;
                        const easeT = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

                        const startX = currentState.startPosition.x;
                        const endX = currentState.targetPosition.x;
                        const startY = currentState.startPosition.y;
                        const endY = currentState.targetPosition.y;

                        currentModel.position.x = startX + (endX - startX) * easeT;
                        currentModel.position.y = startY + (endY - startY) * easeT;
                        currentModel.position.z = currentState.startPosition.z;

                        if (this.item3AnimationProgress >= 1) {
                            this.item3AnimationProgress = 1;
                            this.item3AnimationState = 'completed';
                            currentState.animationState = 'moved';

                            // 목표 위치로 정확히 설정
                            currentModel.position.x = endX;
                            currentModel.position.y = endY;

                            // 이동 완료 처리
                            this.movedItem3Count++;
                            this.currentItem3Index--;

                            console.log(`철망 이동 완료. 이동된 개수: ${this.movedItem3Count}, 다음 인덱스: ${this.currentItem3Index}`);

                            // 대기 중인 이동 처리
                            this.processNextMove();
                        }
                    }
                }

                // 제품 회전 애니메이션 - 모든 철망 한꺼번에 회전
                if (this.item3RotationState === 'rotating') {
                    this.item3RotationProgress += 0.01;

                    const t = this.item3RotationProgress;
                    const easeT = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

                    // 모든 철망 회전
                    for (let i = 0; i < this.item3Models.length; i++) {
                        const model = this.item3Models[i];
                        const state = this.item3States[i];
                        if (model && state) {
                            model.rotation.y = state.startRotation + (state.targetRotation - state.startRotation) * easeT;
                        }
                    }

                    if (this.item3RotationProgress >= 1) {
                        this.item3RotationProgress = 1;
                        this.item3RotationState = 'completed';

                        // 최종 각도 설정
                        for (let i = 0; i < this.item3Models.length; i++) {
                            const model = this.item3Models[i];
                            const state = this.item3States[i];
                            if (model && state) {
                                model.rotation.y = state.targetRotation;
                                state.rotation = state.targetRotation;
                                state.animationState = 'rotated';
                            }
                        }
                        console.log('모든 철망 회전 완료');

                        // 회전 완료 후 값을 0으로 재설정
                        if (this.pendingRotateReset) {
                            this.resetDataValue(this.pendingRotateReset);
                            this.pendingRotateReset = null;
                            this.bundleRotatingValue = 0;
                        }
                    }
                }

                // 제품 적재 애니메이션 - 모든 철망 한꺼번에 이동
                if (this.item3StackState === 'stacking') {
                    this.item3StackProgress += 0.01;

                    const t = this.item3StackProgress;
                    const easeT = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

                    // 모든 철망 이동
                    for (let i = 0; i < this.item3Models.length; i++) {
                        const model = this.item3Models[i];
                        const state = this.item3States[i];
                        if (model && state && state.stackStartPosition && state.stackTargetPosition) {
                            const startX = state.stackStartPosition.x;
                            const endX = state.stackTargetPosition.x;
                            const startY = state.stackStartPosition.y;
                            const endY = state.stackTargetPosition.y;

                            model.position.x = startX + (endX - startX) * easeT;
                            model.position.y = startY + (endY - startY) * easeT;
                        }
                    }

                    if (this.item3StackProgress >= 1) {
                        this.item3StackProgress = 1;
                        this.item3StackState = 'completed';

                        // 최종 위치 설정
                        for (let i = 0; i < this.item3Models.length; i++) {
                            const model = this.item3Models[i];
                            const state = this.item3States[i];
                            if (model && state && state.stackTargetPosition) {
                                model.position.x = state.stackTargetPosition.x;
                                model.position.y = state.stackTargetPosition.y;
                                state.animationState = 'stacked';
                            }
                        }
                        this.stackedItem3Count = this.item3Count;
                        // 적재 후 현재 적층 수량 0으로 설정
                        this.movedItem3Count = 0;
                        this.currentStackCount = 0;
                        console.log('모든 철망 적재 완료');

                        // 적재 완료 후 적층수량 DB에 0으로 입력
                        if (this.stackCountItem) {
                            this.resetDataValue(this.stackCountItem);
                            console.log('적층수량 DB 0으로 업데이트');
                        }

                        // 적재 완료 후 값을 0으로 재설정
                        if (this.pendingStackReset) {
                            this.resetDataValue(this.pendingStackReset);
                            this.pendingStackReset = null;
                            this.productTransferValue = 0;
                        }
                    }
                }
            }
            
            // 카메라 자동 회전
            if (this.isRotating) {
                const radius = 8;
                const angle = elapsedTime * 0.2;
                this.camera.position.x = Math.cos(angle) * radius;
                this.camera.position.z = Math.sin(angle) * radius;
                this.camera.lookAt(0, 0, 0);
            }
            
            // 컨트롤 업데이트
            if (this.controls) {
                this.controls.update();
            }
            
            // 렌더링
            if (this.renderer && this.scene && this.camera) {
                this.renderer.render(this.scene, this.camera);
            }
        },

        handleKeyPress(event) {
            if (event.code === 'Space') {
                event.preventDefault();
                this.isRotating = !this.isRotating;
                console.log('자동 회전:', this.isRotating ? '시작' : '정지');
            }
        },

        onWindowResize() {
            const container = this.$refs.sceneContainer;
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        },

        // 1초마다 DB에서 실시간 데이터 가져오기
        startDataUpdate() {
            // 기존 인터벌이 있으면 정리
            if (this.dataUpdateInterval) {
                clearInterval(this.dataUpdateInterval);
            }
            // 1초마다 DB에서 데이터 가져오기
            this.dataUpdateInterval = setInterval(() => {
                this.fetchQueryMemoryRealTimeData();
            }, 1000);
        },
        
        stopDataUpdate() {
            if (this.dataUpdateInterval) {
                clearInterval(this.dataUpdateInterval);
                this.dataUpdateInterval = null;
            }
        },

        // plc_query_memory 기반 실시간 데이터 조회
        // 1. plc_query_memory 테이블 항목들을 조회
        // 2. memory_address와 plc_data_items의 item_name이 일치하는 id를 찾음
        // 3. plc_real_time_data에서 해당 data_item_id의 가장 최근 value를 조회
        async fetchQueryMemoryRealTimeData() {
            try {
                const response = await this.$http.get('/plc/query-memory-realtime');

                if (response.data.success && response.data.data) {
                    // 조회된 데이터를 realTimeData에 설정
                    this.realTimeData = response.data.data;

                    // targetItems 업데이트 (action_item 체크용)
                    this.targetItems = response.data.data
                        .map(item => item.item_name || item.memory_address)
                        .filter(name => name);

                    // action_item이 true인 항목 찾기
                    const actionItem = response.data.data.find(item => item.action_item === true);
                    this.actionItemName = actionItem ? (actionItem.item_name || actionItem.memory_address) : null;

                    // 묶음수량 값 찾기 (item_name에 '묶음' 포함)
                    const bundleItem = response.data.data.find(item =>
                        (item.item_name && item.item_name.includes('묶음')) ||
                        (item.item_name && item.item_name.toLowerCase().includes('bundle'))
                    );

                    if (bundleItem && bundleItem.value !== null && bundleItem.value !== undefined) {
                        const newBundleCount = Math.floor(Number(bundleItem.value));
                        if (newBundleCount > 0 && newBundleCount !== this.bundleStackCount) {
                            console.log(`묶음수량 업데이트: ${this.bundleStackCount} -> ${newBundleCount}`);
                            this.bundleStackCount = newBundleCount;
                        }
                    }

                    // 적층수량 값 찾기 (현재 적층된 개수)
                    const stackItem = response.data.data.find(item =>
                        (item.item_name && item.item_name.includes('적층')) ||
                        (item.item_name && item.item_name.includes('현재')) ||
                        (item.item_name && item.item_name.toLowerCase().includes('stack'))
                    );

                    // 적층수량 항목 정보 저장 (적재 완료 시 DB 업데이트용)
                    if (stackItem) {
                        this.stackCountItem = stackItem;
                    }

                    if (stackItem && stackItem.value !== null && stackItem.value !== undefined) {
                        const newStackCount = Math.floor(Number(stackItem.value));

                        // 적층수량이 증가했을 때 제품 이동 수행
                        if (newStackCount > this.currentStackCount && newStackCount <= this.bundleStackCount) {
                            const increaseCount = newStackCount - this.currentStackCount;
                            console.log(`적층수량 증가 감지: ${this.currentStackCount} -> ${newStackCount} (${increaseCount}개 이동)`);

                            // 증가한 만큼 제품 이동 수행
                            for (let i = 0; i < increaseCount; i++) {
                                this.triggerProductMove();
                            }
                        }

                        // 적층수량이 0으로 리셋되면 철망 초기화
                        if (newStackCount === 0 && this.currentStackCount > 0) {
                            console.log('적층수량 리셋 감지: 철망 초기화');
                            this.onResetItems();
                        }

                        this.prevStackCount = this.currentStackCount;
                        this.currentStackCount = newStackCount;
                    }

                    // 묶음회전중 값 찾기
                    const rotateItem = response.data.data.find(item =>
                        (item.item_name && item.item_name.includes('회전')) ||
                        (item.item_name && item.item_name.toLowerCase().includes('rotate'))
                    );

                    if (rotateItem) {
                        this.bundleRotatingItem = rotateItem;
                        const rotateValue = Math.floor(Number(rotateItem.value || 0));

                        // 값이 1이고 이전에 1이 아니었을 때 회전 수행
                        if (rotateValue === 1 && this.bundleRotatingValue !== 1) {
                            console.log('묶음회전중 감지: 제품 회전 수행');
                            this.triggerProductRotate(rotateItem);
                        }
                        this.bundleRotatingValue = rotateValue;
                    }

                    // 배출 제품 이송 값 찾기
                    const transferItem = response.data.data.find(item =>
                        (item.item_name && item.item_name.includes('배출')) ||
                        (item.item_name && item.item_name.includes('이송')) ||
                        (item.item_name && item.item_name.toLowerCase().includes('transfer'))
                    );

                    if (transferItem) {
                        this.productTransferItem = transferItem;
                        const transferValue = Math.floor(Number(transferItem.value || 0));

                        // 값이 1이고 이전에 1이 아니었을 때 적재 수행
                        if (transferValue === 1 && this.productTransferValue !== 1) {
                            console.log('배출 제품 이송 감지: 제품 적재 수행');
                            this.triggerProductStack(transferItem);
                        }
                        this.productTransferValue = transferValue;
                    }

                    // action_item 값에 따라 Item3 애니메이션 제어
                    this.checkActionItemAndControlItem3();
                } else {
                    console.warn('조회 메모리 데이터를 가져올 수 없습니다:', response.data.message);
                    this.realTimeData = [];
                    this.targetItems = [];
                    this.actionItemName = null;
                }
            } catch (error) {
                console.error('조회 메모리 실시간 데이터 조회 오류:', error);
                this.realTimeData = [];
                this.targetItems = [];
                this.actionItemName = null;
            }
        },

        // 기존 랜덤 업데이트 메서드 제거
        // updateRealTimeData() {
        //     // 실시간 데이터 업데이트
        //     this.realTimeData.forEach(item => {
        //         if (item.quality === 'good') {
        //             // 16진수 값 랜덤 업데이트
        //             item.value = Math.floor(Math.random() * 65536);
        //         }
        //     });
        // },

        formatValue(value) {
            if (value === null || value === undefined) return '--';
            // 소수점 버리고 10진수로 표시
            const intValue = Math.floor(Number(value));
            return intValue.toString();
        },

        getValueClass(value) {
            if (value === null || value === undefined) return 'value-null';
            return 'value-good';
        },

        isActionItemBlinking(item) {
            // action_item이 설정되어 있고, 해당 항목의 값이 1이면 깜박임
            if (!this.actionItemName) {
                return false;
            }
            // item_name 또는 memory_address가 actionItemName과 일치하는지 확인
            if (item.item_name !== this.actionItemName && item.memory_address !== this.actionItemName) {
                return false;
            }
            const value = Math.floor(Number(item.value || 0));
            return value === 1;
        },

        async refreshData() {
            console.log('데이터 새로고침 - 조회 메모리 실시간 데이터 가져오기');
            await this.fetchQueryMemoryRealTimeData();
        },

        startMonitoring() {
            console.log('모니터링 시작');
            this.isRotating = true;
        },

        pauseMonitoring() {
            console.log('모니터링 일시정지');
            this.isRotating = false;
        },

        // action_item 값 확인 및 Item3 애니메이션 제어
        checkActionItemAndControlItem3() {
            // action_item이 설정되지 않았거나 item3Model이 없으면 리턴
            if (!this.actionItemName || !this.item3Model) {
                return;
            }
            
            // action_item에 해당하는 데이터 찾기
            const actionItemData = this.realTimeData.find(item => item.name === this.actionItemName);
            if (!actionItemData) {
                return;
            }
            
            // 10진수로 변환하고 소수점 버리기
            const actionItemValue = Math.floor(Number(actionItemData.value || 0));
            
            if (actionItemValue === 1) {
                // action_item 값이 1일 경우: 애니메이션 시작
                if (this.item3AnimationState === 'idle' || this.item3AnimationState === 'completed') {
                    this.startItem3Animation();
                }
            }
            // action_item 값이 0일 경우: 복구하지 않음 (제거됨)
        },
        
        // deviceModel의 중간 지점 계산
        calculateDeviceModelCenter() {
            if (!this.deviceModel) {
                return { x: 0, y: -0.48, z: -0.5 };
            }
            
            // 바운딩 박스 계산
            const box = new THREE.Box3().setFromObject(this.deviceModel);
            const center = box.getCenter(new THREE.Vector3());
            
            // 중간 지점에서 오른쪽으로 10% 더 이동
            // 오른쪽 끝까지의 거리의 10%를 더함
            const rightOffset = (box.max.x - center.x) * 0.05;
            const targetX = center.x + rightOffset;
            
            // deviceModel 기준 중간 지점 + 오른쪽 10% (X축만 사용, Y, Z는 초기 위치와 동일하게 유지)
            return {
                x: targetX + 0.5,
                y: this.item3StartPosition.y, // 초기 위치의 Y값(-0.48)과 동일
                z: this.item3StartPosition.z  // 초기 위치의 Z값(-0.5)과 동일
            };
        },
        
        // Item3 애니메이션 시작 (맨 위 철망부터 이동, 중간에 쌓임)
        startItem3Animation() {
            if (this.currentItem3Index < 0 || this.item3Models.length === 0) {
                console.log('이동할 철망이 없습니다.');
                return;
            }

            const currentState = this.item3States[this.currentItem3Index];
            const currentModel = this.item3Models[this.currentItem3Index];

            if (currentModel && (this.item3AnimationState === 'idle' || this.item3AnimationState === 'completed')) {
                // deviceModel의 중간 지점 계산
                const targetPos = this.calculateDeviceModelCenter();

                // 중간 위치에 쌓일 때의 Y 위치 계산 (맨 밑부터 쌓임)
                const targetY = this.item3BaseY + (this.movedItem3Count * this.item3HeightGap);
                const centerYOffset = currentModel.position.y - this.item3BaseY - (this.currentItem3Index * this.item3HeightGap);

                // 현재 철망의 상태 업데이트
                currentState.startPosition = {
                    x: currentModel.position.x,
                    y: currentModel.position.y,
                    z: currentModel.position.z
                };
                currentState.targetPosition = {
                    x: targetPos.x,
                    y: targetY + centerYOffset, // 중간 위치에 쌓이도록 Y 조정
                    z: targetPos.z
                };

                // 애니메이션 시작
                this.item3AnimationState = 'moving';
                this.item3AnimationProgress = 0;
                currentState.animationState = 'moving';

                console.log(`철망[${this.currentItem3Index}] 이동 시작: (${currentState.startPosition.x.toFixed(2)}, ${currentState.startPosition.y.toFixed(2)}) -> (${currentState.targetPosition.x.toFixed(2)}, ${currentState.targetPosition.y.toFixed(2)})`);
            }
        },
        
        // Item3 모델 클릭 이벤트 (수동 제어용) - 제품 이동 적용
        onItem3Click() {
            if (this.currentItem3Index < 0) {
                console.log('이동할 철망이 없습니다.');
                return;
            }

            // 하드코딩된 값 설정: 제품이동 D4123 = 1
            const value = 1;
            this.productMoveState = value;
            // PLC에 값 전송
            this.writePlcValue(PLC_ADDRESS_PRODUCT_MOVE, value);

            // 애니메이션 제어: 중간 지점까지 수평 이동
            if (this.item3AnimationState === 'idle' || this.item3AnimationState === 'completed') {
                this.item3AnimationState = 'idle'; // 리셋
                this.startItem3Animation();
            }
        },

        // 제품 이동 트리거 (적층수량 증가 시 자동 호출)
        triggerProductMove() {
            if (this.currentItem3Index < 0) {
                console.log('이동할 철망이 없습니다.');
                return;
            }

            // 이미 애니메이션 중이면 큐에 추가
            if (this.item3AnimationState === 'moving') {
                // 이동 대기열에 추가
                if (!this.pendingMoves) {
                    this.pendingMoves = 0;
                }
                this.pendingMoves++;
                console.log(`제품 이동 대기열 추가: ${this.pendingMoves}개 대기 중`);
                return;
            }

            // 애니메이션 시작
            this.item3AnimationState = 'idle';
            this.startItem3Animation();
        },

        // 대기 중인 이동 처리 (애니메이션 완료 후 호출)
        processNextMove() {
            if (this.pendingMoves && this.pendingMoves > 0) {
                this.pendingMoves--;
                console.log(`대기열 이동 처리: ${this.pendingMoves}개 남음`);
                // 약간의 딜레이 후 다음 이동 시작
                setTimeout(() => {
                    if (this.currentItem3Index >= 0) {
                        this.item3AnimationState = 'idle';
                        this.startItem3Animation();
                    }
                }, 100);
            }
        },

        // 제품 회전 트리거 (묶음회전중 값이 1일 때 자동 호출)
        triggerProductRotate(item) {
            if (this.item3Models.length === 0) {
                console.log('회전할 철망이 없습니다.');
                return;
            }

            // 이미 회전 중이면 무시
            if (this.item3RotationState === 'rotating') {
                console.log('이미 회전 중입니다.');
                return;
            }

            // 회전 애니메이션 시작
            this.item3RotationState = 'idle';
            this.startItem3Rotation();

            // 회전 완료 후 값을 0으로 재설정
            this.pendingRotateReset = item;
        },

        // 제품 적재 트리거 (배출 제품 이송 값이 1일 때 자동 호출)
        triggerProductStack(item) {
            if (this.item3Models.length === 0) {
                console.log('적재할 철망이 없습니다.');
                return;
            }

            // 이미 적재 중이면 무시
            if (this.item3StackState === 'stacking') {
                console.log('이미 적재 중입니다.');
                return;
            }

            // 적재 애니메이션 시작
            this.item3StackState = 'idle';
            this.startItem3Stack();

            // 적재 완료 후 값을 0으로 재설정
            this.pendingStackReset = item;
        },

        // 실시간 데이터 값을 0으로 재설정
        async resetDataValue(item) {
            if (!item || !item.data_item_id) {
                console.warn('재설정할 항목 정보가 없습니다.');
                return;
            }

            try {
                const response = await this.$http.post('/plc/realtime-data-input', {
                    data_item_id: item.data_item_id,
                    value: 0,
                    quality: 'good'
                });

                if (response.data && response.data.success) {
                    console.log(`값 재설정 완료: ${item.item_name} = 0`);
                } else {
                    console.error('값 재설정 실패:', response.data?.message);
                }
            } catch (error) {
                console.error('값 재설정 오류:', error);
            }
        },

        // 제품 회전 적용 (모든 철망 한꺼번에)
        onProductRotate() {
            if (this.item3Models.length === 0) {
                console.log('회전할 철망이 없습니다.');
                return;
            }

            // 하드코딩된 값 설정: 제품회전 D4407 = 1
            const value = 1;
            this.productRotateState = value;
            // PLC에 값 전송
            this.writePlcValue(PLC_ADDRESS_PRODUCT_ROTATE, value);
            console.log(`제품 회전 적용: ${PLC_ADDRESS_PRODUCT_ROTATE} = ${value}`);

            // 3D 철망 90도 회전 애니메이션 시작
            if (this.item3RotationState === 'idle' || this.item3RotationState === 'completed') {
                this.item3RotationState = 'idle'; // 리셋
                this.startItem3Rotation();
            }
        },
        
        // Item3 회전 애니메이션 시작 (모든 철망 한꺼번에 90도 회전)
        startItem3Rotation() {
            if (this.item3Models.length === 0) {
                console.log('회전할 철망이 없습니다.');
                return;
            }

            if (this.item3RotationState === 'idle' || this.item3RotationState === 'completed') {
                // 모든 철망의 회전 각도 설정
                for (let i = 0; i < this.item3Models.length; i++) {
                    const model = this.item3Models[i];
                    const state = this.item3States[i];
                    if (model && state) {
                        state.startRotation = model.rotation.y;
                        state.targetRotation = state.startRotation + (Math.PI / 2); // 90도
                        state.animationState = 'rotating';
                    }
                }

                // 회전 애니메이션 시작
                this.item3RotationState = 'rotating';
                this.item3RotationProgress = 0;

                console.log(`모든 철망(${this.item3Models.length}개) 회전 시작: 90도`);
            }
        },
        
        // 제품 적재 적용 (모든 철망 한꺼번에)
        onProductStack() {
            if (this.item3Models.length === 0) {
                console.log('적재할 철망이 없습니다.');
                return;
            }

            // 하드코딩된 값 설정: 제품적재 D4625 = 1
            const value = 1;
            this.productStackState = value;
            // PLC에 값 전송
            this.writePlcValue(PLC_ADDRESS_PRODUCT_STACK, value);
            console.log(`제품 적재 적용: ${PLC_ADDRESS_PRODUCT_STACK} = ${value}`);

            // 3D 철망 적재 애니메이션 시작
            if (this.item3StackState === 'idle' || this.item3StackState === 'completed') {
                this.item3StackState = 'idle'; // 리셋
                this.startItem3Stack();
            }
        },

        // 초기화 - 묶음수량에 따라 철망 재생성
        onResetItems() {
            if (!this.item3OriginalModel) {
                console.log('원본 모델이 로드되지 않았습니다.');
                return;
            }

            // 묶음수량에 따라 철망 재생성
            this.regenerateItem3Models(this.bundleStackCount);

            console.log(`철망 초기화 완료 (묶음수량: ${this.bundleStackCount}개)`);
        },

        // Item3 적재 애니메이션 시작 (모든 철망 한꺼번에 이동)
        startItem3Stack() {
            if (this.item3Models.length === 0) {
                console.log('적재할 철망이 없습니다.');
                return;
            }

            if (this.item3StackState === 'idle' || this.item3StackState === 'completed') {
                // 모든 철망의 시작/목표 위치 설정
                for (let i = 0; i < this.item3Models.length; i++) {
                    const model = this.item3Models[i];
                    const state = this.item3States[i];
                    if (model && state) {
                        // 현재 위치를 시작 위치로 저장
                        state.stackStartPosition = {
                            x: model.position.x,
                            y: model.position.y,
                            z: model.position.z
                        };

                        // 목표 Y 위치 계산: 맨 밑부터 쌓임 (i=0이 맨 밑)
                        const centerYOffset = model.position.y - this.item3BaseY - (i * this.item3HeightGap);
                        const targetY = this.item3BaseY + (i * this.item3HeightGap) + centerYOffset;

                        // 목표 위치: X는 최종 적재 위치, Y는 현재 높이 유지
                        state.stackTargetPosition = {
                            x: this.item3FinalStackX,
                            y: targetY,
                            z: state.stackStartPosition.z
                        };

                        state.animationState = 'stacking';
                    }
                }

                // 적재 애니메이션 시작
                this.item3StackState = 'stacking';
                this.item3StackProgress = 0;

                console.log(`모든 철망(${this.item3Models.length}개) 적재 시작: X -> ${this.item3FinalStackX}`);
            }
        },
        
        // PLC에 값 쓰기
        async writePlcValue(address, value) {
            try {
                const response = await this.$http.post('/api/v1/plc/write', {
                    address: address,
                    value: value
                });

                if (response.data.success) {
                    console.log(`PLC 쓰기 성공: ${address} = ${value}`);
                } else {
                    console.error(`PLC 쓰기 실패: ${response.data.message}`);
                }
            } catch (error) {
                console.error(`PLC 쓰기 오류 (${address}):`, error);
            }
        },

        // 10진수를 16진수 문자열로 변환
        toHex(value) {
            if (value === null || value === undefined || value === '') return '0';
            const intValue = Math.floor(Number(value));
            if (isNaN(intValue)) return '0';
            return intValue.toString(16).toUpperCase();
        },

        // 데이터 입력 팝업 열기
        openDataInputPopup() {
            this.showDataInputPopup = true;
            this.dataInputValues = {};
            // 초기 위치 설정 (화면 중앙 우측)
            const container = this.$refs.sceneContainer;
            if (container) {
                this.popupPosition = {
                    x: container.clientWidth - 350,
                    y: 150
                };
            }
        },

        // 데이터 입력 팝업 닫기
        closeDataInputPopup() {
            this.showDataInputPopup = false;
            this.dataInputValues = {};
        },

        // 팝업 드래그 시작
        startDragPopup(event) {
            this.isDraggingPopup = true;
            this.dragOffset = {
                x: event.clientX - this.popupPosition.x,
                y: event.clientY - this.popupPosition.y
            };
            document.addEventListener('mousemove', this.onDragPopup);
            document.addEventListener('mouseup', this.stopDragPopup);
        },

        // 팝업 드래그 중
        onDragPopup(event) {
            if (!this.isDraggingPopup) return;
            this.popupPosition = {
                x: event.clientX - this.dragOffset.x,
                y: event.clientY - this.dragOffset.y
            };
        },

        // 팝업 드래그 종료
        stopDragPopup() {
            this.isDraggingPopup = false;
            document.removeEventListener('mousemove', this.onDragPopup);
            document.removeEventListener('mouseup', this.stopDragPopup);
        },

        // 데이터 값 제출 (10진수 입력 → 16진수로 저장)
        async submitDataValue(item) {
            const memoryAddress = item.memory_address;
            const decimalValue = this.dataInputValues[memoryAddress];

            if (decimalValue === undefined || decimalValue === '' || decimalValue === null) {
                console.warn('입력값이 없습니다.');
                return;
            }

            const intValue = Math.floor(Number(decimalValue));
            if (isNaN(intValue)) {
                console.warn('유효한 숫자가 아닙니다.');
                return;
            }

            // 16진수 값 (로그용)
            const hexValue = intValue.toString(16).toUpperCase();

            try {
                // data_item_id를 사용하여 plc_real_time_data에 값 저장
                if (item.data_item_id) {
                    const response = await this.$http.post('/plc/realtime-data-input', {
                        data_item_id: item.data_item_id,
                        value: intValue,
                        quality: 'good'
                    });

                    if (response.data && response.data.success) {
                        console.log(`데이터 저장 성공: ${memoryAddress} = ${intValue} (0x${hexValue})`);
                        // 입력 필드 초기화
                        this.$set(this.dataInputValues, memoryAddress, '');
                        // 데이터 새로고침
                        await this.fetchQueryMemoryRealTimeData();
                    } else {
                        console.error('데이터 저장 실패:', response.data?.message);
                    }
                } else {
                    console.error('data_item_id가 없습니다. 데이터를 저장할 수 없습니다.');
                }
            } catch (error) {
                console.error('데이터 저장 오류:', error);
            }
        },

        cleanup() {
            if (this.animationId) {
                cancelAnimationFrame(this.animationId);
            }
            if (this.dataUpdateInterval) {
                clearInterval(this.dataUpdateInterval);
            }
            if (this.renderer) {
                this.renderer.dispose();
            }
            window.removeEventListener('resize', this.onWindowResize);
        }
    }
};
</script>

<style scoped>
.plc-monitor-3d {
    position: relative;
    width: 100%;
    height: 100vh;
    overflow: hidden;
    background: linear-gradient(135deg, #4a5568 0%, #718096 100%);
}

.overlay-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 10;
}

/* 헤더 스타일 */
.monitor-header {
    position: absolute;
    top: 20px;
    left: 20px;
    right: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    color: white;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    pointer-events: auto;
}

.header-content h1 {
    margin: 0;
    font-size: 28px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
    text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
}

.header-content p {
    margin: 5px 0 0 0;
    opacity: 0.9;
    font-size: 14px;
    color: #88ccff;
}

.header-actions {
    display: flex;
    gap: 10px;
}

.header-actions .btn {
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
}

.header-actions .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

/* 상태 패널 */
.status-panel {
    position: absolute;
    top: 120px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 15px;
    pointer-events: auto;
}

.status-card {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px 20px;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    color: white;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    min-width: 250px;
    transition: all 0.3s ease;
}

.status-card:hover {
    transform: translateX(-5px);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
}

.status-icon {
    font-size: 24px;
    color: #00ffff;
    text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.status-content h4 {
    margin: 0 0 5px 0;
    font-size: 14px;
    color: #88ccff;
    font-weight: 500;
}

.status-value {
    margin: 0 0 5px 0;
    font-size: 16px;
    font-weight: 700;
}

.status-value.connected {
    color: #00ff00;
    text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
}

.status-value.active {
    color: #00ffff;
    text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.status-value.good {
    color: #ffff00;
    text-shadow: 0 0 10px rgba(255, 255, 0, 0.5);
}

.status-content small {
    color: #aaaaaa;
    font-size: 12px;
}

.button-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.button-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
}

.button-label {
    font-size: 0.75rem;
    color: #88ccff;
    font-weight: 500;
    flex: 1;
}

.apply-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.4rem 0.8rem;
    border-radius: 0.4rem;
    font-size: 0.7rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    min-width: 60px;
}

.apply-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.apply-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.apply-btn.reset-btn {
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
}

.apply-btn.reset-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, #c0392b 0%, #a93226 100%);
}

/* 적층상태 패널 */
.stack-status-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
}

.stack-status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.stack-label {
    font-size: 0.75rem;
    color: #88ccff;
    font-weight: 500;
}

.stack-value {
    font-size: 1.2rem;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    min-width: 40px;
    text-align: right;
}

.stack-value.current {
    color: #ff4444;
    text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
}

.stack-value.bundle {
    color: #ffffff;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

/* 데이터 패널 */
.data-panel {
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 20px;
    color: white;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    pointer-events: auto;
    max-width: 400px;
}

.data-panel h3 {
    margin: 0 0 15px 0;
    font-size: 18px;
    color: #00ffff;
    text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    display: flex;
    align-items: center;
    gap: 8px;
}

.data-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.data-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
    padding: 10px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

.data-item:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
}

.data-item.blinking {
    animation: blink 0.5s ease-in-out infinite;
    border-color: #00ffff;
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

@keyframes blink {
    0%, 100% {
        opacity: 1;
        background: rgba(0, 255, 255, 0.2);
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    }
    50% {
        opacity: 0.6;
        background: rgba(0, 255, 255, 0.4);
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
    }
}

.data-label {
    font-size: 12px;
    color: #88ccff;
    font-weight: 500;
}

.data-address {
    font-size: 10px;
    color: #aaaaaa;
    font-family: 'Courier New', monospace;
}

.data-value {
    font-size: 14px;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    letter-spacing: 0.5px;
}

.data-value.value-good {
    color: #00ff00;
    text-shadow: 0 0 5px rgba(0, 255, 0, 0.3);
}

.data-value.value-null {
    color: #ff6666;
    text-shadow: 0 0 5px rgba(255, 102, 102, 0.3);
}

/* 카메라 컨트롤 안내 */
.camera-controls {
    position: absolute;
    bottom: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    pointer-events: auto;
}

.control-info {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(10px);
    border-radius: 8px;
    color: #aaaaaa;
    font-size: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.control-info i {
    color: #00ffff;
    font-size: 14px;
}

/* 데이터 입력 버튼 (오른쪽 하단) */
.data-input-btn {
    position: absolute;
    bottom: 100px;
    right: 20px;
    padding: 8px 14px;
    background: linear-gradient(135deg, #00c9ff 0%, #92fe9d 100%);
    color: #1a1a2e;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 3px 10px rgba(0, 201, 255, 0.4);
    transition: all 0.3s ease;
    pointer-events: auto;
    z-index: 100;
}

.data-input-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 201, 255, 0.6);
}

.data-input-btn i {
    font-size: 14px;
}

/* 데이터 입력 팝업 (Modeless) */
.data-input-popup {
    position: fixed;
    background: rgba(20, 20, 40, 0.95);
    border-radius: 10px;
    width: 320px;
    max-height: 400px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.15);
    overflow: hidden;
    z-index: 1000;
    pointer-events: auto;
}

.popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    background: rgba(0, 201, 255, 0.15);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    cursor: move;
    user-select: none;
}

.popup-header h3 {
    margin: 0;
    color: #00c9ff;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.popup-close-btn {
    background: transparent;
    border: none;
    color: #aaa;
    font-size: 16px;
    cursor: pointer;
    padding: 2px;
    line-height: 1;
    transition: color 0.3s ease;
}

.popup-close-btn:hover {
    color: #ff6b6b;
}

.popup-body {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
}

.data-input-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.data-input-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 6px 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.data-input-item:hover {
    background: rgba(255, 255, 255, 0.08);
}

.input-item-row {
    display: flex;
    align-items: center;
    gap: 6px;
}

.input-item-name {
    font-size: 11px;
    font-weight: 500;
    color: #88ccff;
    min-width: 60px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.input-item-current {
    font-size: 10px;
    color: #00ff00;
    font-family: 'Courier New', monospace;
    min-width: 35px;
    text-align: right;
}

.data-input-field {
    width: 60px;
    padding: 4px 6px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: #fff;
    font-size: 11px;
    font-family: 'Courier New', monospace;
}

.data-input-field:focus {
    outline: none;
    border-color: #00c9ff;
}

.data-input-field::placeholder {
    color: #555;
}

.hex-preview {
    font-size: 9px;
    color: #ffaa00;
    font-family: 'Courier New', monospace;
    min-width: 45px;
}

.submit-btn {
    padding: 6px 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.submit-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(102, 126, 234, 0.4);
}

.submit-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.popup-footer {
    padding: 10px 12px;
    background: rgba(0, 0, 0, 0.2);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: flex-end;
}

.popup-close-action {
    padding: 8px 20px;
    background: rgba(255, 100, 100, 0.2);
    color: #ff8888;
    border: 1px solid rgba(255, 100, 100, 0.3);
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s ease;
}

.popup-close-action:hover {
    background: rgba(255, 100, 100, 0.3);
    border-color: rgba(255, 100, 100, 0.5);
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .monitor-header {
        flex-direction: column;
        gap: 15px;
        text-align: center;
        top: 10px;
        left: 10px;
        right: 10px;
    }
    
    .header-actions {
        flex-wrap: wrap;
        justify-content: center;
    }
    
    .status-panel {
        top: 140px;
        right: 10px;
        left: 10px;
        flex-direction: row;
        overflow-x: auto;
        gap: 10px;
    }
    
    .status-card {
        min-width: 200px;
        flex-shrink: 0;
    }
    
    .data-panel {
        bottom: 10px;
        left: 10px;
        right: 10px;
        max-width: none;
    }
    
    .data-grid {
        grid-template-columns: 1fr;
    }
    
    .camera-controls {
        bottom: 10px;
        right: 10px;
        left: 10px;
        flex-direction: row;
        justify-content: center;
    }

    .data-input-btn {
        bottom: 70px;
        right: 10px;
        padding: 6px 10px;
        font-size: 11px;
    }

    .data-input-popup {
        width: 280px;
        max-height: 350px;
    }
}
</style>

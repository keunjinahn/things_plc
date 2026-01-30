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
                        <p class="status-value active">로드됨</p>
                        <div class="button-group">
                            <div class="button-row">
                                <span class="button-label">제품 이동</span>
                                <button @click="onItem3Click" class="apply-btn" :disabled="item3AnimationState === 'moving'">
                                    {{ item3AnimationState === 'moving' ? '이동 중...' : '적용' }}
                                </button>
                            </div>
                            <div class="button-row">
                                <span class="button-label">제품 회전</span>
                                <button @click="onProductRotate" class="apply-btn">
                                    적용
                                </button>
                            </div>
                            <div class="button-row">
                                <span class="button-label">제품 적제</span>
                                <button @click="onProductStack" class="apply-btn">
                                    적용
                                </button>
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
                        <span class="data-label">{{ item.name }}</span>
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
            
            // 3D 모델 관련
            item3Model: null,
            item3AnimationState: 'idle', // 'idle', 'moving', 'completed'
            item3AnimationProgress: 0,
            item3StartPosition: { x: -1.5, y: -0.48, z: -0.5 }, // 시작 위치 (초기 위치)
            item3TargetPosition: { x: 0, y: -0.48, z: -0.5 }, // 목표 위치 (중간 지점, Y값은 초기 위치와 동일)
            
            // 회전 애니메이션 관련
            item3RotationState: 'idle', // 'idle', 'rotating', 'completed'
            item3RotationProgress: 0,
            item3StartRotation: 0, // 시작 회전 각도
            item3TargetRotation: 0, // 목표 회전 각도 (90도)
            item3RotationCenter: { x: 0, y: 0, z: 0 }, // 회전 중심점 (철망 사각형의 중심)
            item3StartPositionForRotation: { x: 0, y: 0, z: 0 }, // 회전 시작 시 위치
            item3TargetPositionAfterRotation: { x: 0, y: 0, z: 0 }, // 회전 완료 후 목표 위치
            item3GeometryOffset: { x: 0, y: 0, z: 0 }, // 모델 원점에서 geometry 중심까지의 오프셋
            
            // 적재 애니메이션 관련
            item3StackState: 'idle', // 'idle', 'stacking', 'completed'
            item3StackProgress: 0,
            item3StackStartPosition: { x: 0, y: 0, z: 0 }, // 적재 시작 위치
            item3StackTargetPosition: { x: 0, y: 0, z: 0 }, // 적재 목표 위치 (X축 +2)
            
            // 버튼 상태값 (1 또는 0) - 하드코딩된 초기값
            productMoveState: 0,      // 제품이동 상태 (D4123)
            productRotateState: 0,    // 제품회전 상태 (D4407)
            productStackState: 0      // 제품적재 상태 (D4625)
        };
    },
    computed: {
        // 이미지에 표시된 항목들만 필터링
        filteredRealTimeData() {
            return this.realTimeData.filter(item => {
                const itemName = item.name || item.item_name || item.address || '';
                return this.targetItems.includes(itemName);
            });
        }
    },
    mounted() {
        this.initialize3DScene();
        this.fetchActiveItems();
        this.fetchRealTimeDataFromDB();
        this.startDataUpdate();
        window.addEventListener('keydown', this.handleKeyPress);
    },
    beforeDestroy() {
        this.stopDataUpdate();
        this.cleanup();
        window.removeEventListener('keydown', this.handleKeyPress);
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
                const loadedModel = gltf.scene;

                // 모델 스케일 조정
                loadedModel.scale.set(2, 2, 2);
                loadedModel.updateMatrixWorld(true);

                // 바운딩 박스로 geometry 중심 계산
                const box = new THREE.Box3().setFromObject(loadedModel);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());

                // 피벗 그룹 생성 (이 그룹이 회전의 중심이 됨)
                this.item3Model = new THREE.Group();

                // 로드된 모델을 그룹에 추가하고, 중심이 그룹 원점에 오도록 오프셋
                loadedModel.position.set(-center.x, -center.y, -center.z);
                this.item3Model.add(loadedModel);

                // 모델 초기 위치 설정 (피벗 그룹의 위치 = geometry 중심 위치)
                const initialX = -2.0;
                const initialY = -0.48 + center.y; // 중심 높이 보정
                const initialZ = -0.0;
                this.item3Model.position.set(initialX, initialY, initialZ);

                // 시작 위치 저장 (초기 위치)
                this.item3StartPosition = { x: initialX, y: initialY, z: initialZ };

                // 모델 회전 조정 (회전하지 않음)
                this.item3Model.rotation.y = 0;

                // 그림자 설정
                loadedModel.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;

                        // 재질 개선
                        if (child.material) {
                            child.material.metalness = 0.7;
                            child.material.roughness = 0.3;
                        }
                    }
                });

                // Item3을 device_v2blend의 자식으로 추가하여 상대적 위치 유지
                if (this.deviceModel) {
                    this.deviceModel.add(this.item3Model);
                    console.log('Item3 모델을 device_v2blend에 추가 완료 (중심 피벗)');
                    console.log(`Geometry 크기: ${size.x.toFixed(2)} x ${size.y.toFixed(2)} x ${size.z.toFixed(2)}`);
                } else {
                    this.scene.add(this.item3Model);
                    console.log('Item3 모델 로드 완료 (device_v2blend 없음)');
                }

            }, undefined, (error) => {
                console.error('Item3 모델 로드 실패:', error);
            });
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
            
            // Item3 모델 애니메이션 - 제품 이동 버튼 클릭 시 중간 지점까지 수평 이동
            if (this.item3Model) {
                if (this.item3AnimationState === 'moving') {
                    // 애니메이션 진행률 업데이트
                    this.item3AnimationProgress += 0.005; // 약 2초에 완료
                    
                    if (this.item3AnimationProgress >= 1) {
                        this.item3AnimationProgress = 1;
                        this.item3AnimationState = 'completed'; // 완료 상태로 변경
                    }
                    
                    // 시작 위치에서 목표 위치(중간 지점)까지 수평 이동
                    const startX = this.item3StartPosition.x;
                    const endX = this.item3TargetPosition.x;
                    const targetX = startX + (endX - startX) * this.item3AnimationProgress;
                    this.item3Model.position.x = targetX;
                    
                    // Y, Z축은 고정 (수평 이동만)
                    this.item3Model.position.y = this.item3StartPosition.y;
                    this.item3Model.position.z = this.item3StartPosition.z;
                } else if (this.item3AnimationState === 'completed') {
                    // 완료 상태에서는 목표 위치에 그대로 유지 (복구하지 않음)
                    this.item3Model.position.x = this.item3TargetPosition.x;
                    this.item3Model.position.y = this.item3TargetPosition.y;
                    this.item3Model.position.z = this.item3TargetPosition.z;
                }
                
                // Item3 모델 회전 애니메이션 - 제품 회전 버튼 클릭 시 90도 제자리 회전
                // 피벗 그룹을 사용하므로 rotation.y만 변경하면 중심 기준 회전됨
                if (this.item3RotationState === 'rotating') {
                    // 회전 애니메이션 진행률 업데이트
                    this.item3RotationProgress += 0.01; // 약 1초에 완료

                    if (this.item3RotationProgress >= 1) {
                        this.item3RotationProgress = 1;
                        this.item3RotationState = 'completed';
                        this.item3Model.rotation.y = this.item3TargetRotation;
                    } else {
                        // 현재 회전 각도 계산 (easing 적용)
                        const t = this.item3RotationProgress;
                        const easeT = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; // easeInOutQuad
                        const currentAngle = this.item3StartRotation + (this.item3TargetRotation - this.item3StartRotation) * easeT;
                        this.item3Model.rotation.y = currentAngle;
                    }
                } else if (this.item3RotationState === 'completed') {
                    // 완료 상태에서는 최종 각도 유지
                    this.item3Model.rotation.y = this.item3TargetRotation;
                }
                
                // Item3 모델 적재 애니메이션 - 제품 적재 버튼 클릭 시 X축으로 2만큼 수평 이동
                if (this.item3StackState === 'stacking') {
                    // 적재 애니메이션 진행률 업데이트
                    this.item3StackProgress += 0.01; // 약 1초에 완료
                    
                    if (this.item3StackProgress >= 1) {
                        this.item3StackProgress = 1;
                        this.item3StackState = 'completed'; // 완료 상태로 변경
                        // 목표 위치로 정확히 설정
                        this.item3Model.position.x = this.item3StackTargetPosition.x;
                        this.item3Model.position.y = this.item3StackTargetPosition.y;
                        this.item3Model.position.z = this.item3StackTargetPosition.z;
                    } else {
                        // 시작 위치에서 목표 위치(X축 +2)까지 수평 이동
                        const startX = this.item3StackStartPosition.x;
                        const endX = this.item3StackTargetPosition.x;
                        const targetX = startX + (endX - startX) * this.item3StackProgress;
                        this.item3Model.position.x = targetX;
                        
                        // Y, Z축은 고정 (수평 이동만)
                        this.item3Model.position.y = this.item3StackStartPosition.y;
                        this.item3Model.position.z = this.item3StackStartPosition.z;
                    }
                } else if (this.item3StackState === 'completed') {
                    // 완료 상태에서는 목표 위치에 그대로 유지
                    this.item3Model.position.x = this.item3StackTargetPosition.x;
                    this.item3Model.position.y = this.item3StackTargetPosition.y;
                    this.item3Model.position.z = this.item3StackTargetPosition.z;
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
                this.fetchRealTimeDataFromDB();
            }, 1000);
        },
        
        stopDataUpdate() {
            if (this.dataUpdateInterval) {
                clearInterval(this.dataUpdateInterval);
                this.dataUpdateInterval = null;
            }
        },

        // is_active가 true인 항목들 조회
        async fetchActiveItems() {
            try {
                const response = await this.$http.get('/plc/data-items');
                
                if (response.data.success && response.data.data) {
                    // is_active가 true인 항목들의 item_name을 targetItems에 설정
                    this.targetItems = response.data.data
                        .filter(item => item.is_active === true)
                        .map(item => item.item_name || item.address)
                        .filter(name => name); // 빈 값 제거
                    
                    // action_item이 true인 항목 찾기
                    const actionItem = response.data.data.find(item => item.action_item === true);
                    this.actionItemName = actionItem ? (actionItem.item_name || actionItem.address) : null;
                    
                    console.log('활성화된 항목 로드 완료:', this.targetItems.length, '개');
                    if (this.actionItemName) {
                        console.log('액션 항목:', this.actionItemName);
                    }
                } else {
                    console.warn('활성화된 항목 조회 실패:', response.data.message);
                    this.targetItems = [];
                    this.actionItemName = null;
                }
            } catch (error) {
                console.error('활성화된 항목 조회 오류:', error);
                this.targetItems = [];
                this.actionItemName = null;
            }
        },

        // 실제 DB에서 실시간 데이터 가져오기
        async fetchRealTimeDataFromDB() {
            try {
                // 활성화된 항목이 없으면 조회하지 않음
                if (this.targetItems.length === 0) {
                    this.realTimeData = [];
                    return;
                }

                // 전체 데이터를 한 번에 가져오는 방법 (더 효율적)
                const response = await this.$http.get('/plc/real-time-data', {
                    params: {
                        limit: 100 // 충분한 데이터 가져오기
                    }
                });
                
                if (response.data.success && response.data.data) {
                    // DB 데이터를 realTimeData 형식에 맞게 변환
                    const allData = response.data.data.map(item => ({
                        name: item.item_name || item.address || `Item${item.data_item_id}`,
                        value: item.value || 0,
                        quality: item.quality || 'good',
                        timestamp: item.timestamp
                    }));
                    
                    // targetItems에 있는 항목들만 필터링하고 순서대로 정렬
                    this.realTimeData = this.targetItems.map(itemName => {
                        const found = allData.find(item => item.name === itemName);
                        return found || {
                            name: itemName,
                            value: 0,
                            quality: 'uncertain',
                            timestamp: null
                        };
                    });
                    
                    // action_item 값에 따라 Item3 애니메이션 제어
                    this.checkActionItemAndControlItem3();
                } else {
                    console.warn('DB에서 데이터를 가져올 수 없습니다:', response.data.message);
                    // 기본 데이터 설정
                    this.realTimeData = this.targetItems.map(itemName => ({
                        name: itemName,
                        value: 0,
                        quality: 'uncertain',
                        timestamp: null
                    }));
                }
            } catch (error) {
                console.error('실시간 데이터 조회 오류:', error);
                // 에러 발생 시 기본 데이터 설정
                this.realTimeData = this.targetItems.map(itemName => ({
                    name: itemName,
                    value: 0,
                    quality: 'uncertain',
                    timestamp: null
                }));
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
            if (!this.actionItemName || item.name !== this.actionItemName) {
                return false;
            }
            const value = Math.floor(Number(item.value || 0));
            return value === 1;
        },

        async refreshData() {
            console.log('데이터 새로고침 - 활성화된 항목 및 실시간 데이터 가져오기');
            await this.fetchActiveItems();
            await this.fetchRealTimeDataFromDB();
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
        
        // Item3 애니메이션 시작
        startItem3Animation() {
            if (this.item3Model && (this.item3AnimationState === 'idle' || this.item3AnimationState === 'completed')) {
                // deviceModel의 중간 지점 계산
                this.item3TargetPosition = this.calculateDeviceModelCenter();
                
                // 시작 위치 저장 (현재 위치에서 시작)
                this.item3StartPosition = {
                    x: this.item3Model.position.x,
                    y: this.item3Model.position.y,
                    z: this.item3Model.position.z
                };
                
                // 애니메이션 시작
                this.item3AnimationState = 'moving';
                this.item3AnimationProgress = 0;
                console.log(`Item3 애니메이션 시작: 시작(${this.item3StartPosition.x}) -> 중간(${this.item3TargetPosition.x})`);
            }
        },
        
        // Item3 모델 클릭 이벤트 (수동 제어용) - 제품 이동 적용
        onItem3Click() {
            // 하드코딩된 값 설정: 제품이동 D4123 = 1
            const value = 1; // 하드코딩된 값
            this.productMoveState = value;
            // PLC에 값 전송
            this.writePlcValue(PLC_ADDRESS_PRODUCT_MOVE, value);
            
            // 애니메이션 제어: 중간 지점까지 수평 이동
            if (value === 1 && this.item3AnimationState === 'idle') {
                this.startItem3Animation();
            }
        },
        
        // 제품 회전 적용
        onProductRotate() {
            // 하드코딩된 값 설정: 제품회전 D4407 = 1
            const value = 1; // 하드코딩된 값
            this.productRotateState = value;
            // PLC에 값 전송
            this.writePlcValue(PLC_ADDRESS_PRODUCT_ROTATE, value);
            console.log(`제품 회전 적용: ${PLC_ADDRESS_PRODUCT_ROTATE} = ${value}`);
            
            // 3D 철망 90도 회전 애니메이션 시작
            this.startItem3Rotation();
        },
        
        // Item3 회전 애니메이션 시작 (철망 사각형 중심점 기준 제자리 회전)
        // 피벗 그룹을 사용하므로 단순히 rotation.y만 변경하면 됨
        startItem3Rotation() {
            if (this.item3Model && (this.item3RotationState === 'idle' || this.item3RotationState === 'completed')) {
                // 현재 회전 각도를 시작 각도로 저장
                this.item3StartRotation = this.item3Model.rotation.y;

                // 목표 각도: 현재 각도에서 90도 추가 (라디안으로 변환)
                this.item3TargetRotation = this.item3StartRotation + (Math.PI / 2); // 90도 = π/2 라디안

                // 회전 애니메이션 시작
                this.item3RotationState = 'rotating';
                this.item3RotationProgress = 0;
                console.log(`Item3 제자리 회전 시작: ${(this.item3StartRotation * 180 / Math.PI).toFixed(1)}도 -> ${(this.item3TargetRotation * 180 / Math.PI).toFixed(1)}도`);
            }
        },
        
        // 제품 적재 적용
        onProductStack() {
            // 하드코딩된 값 설정: 제품적재 D4625 = 1
            const value = 1; // 하드코딩된 값
            this.productStackState = value;
            // PLC에 값 전송
            this.writePlcValue(PLC_ADDRESS_PRODUCT_STACK, value);
            console.log(`제품 적재 적용: ${PLC_ADDRESS_PRODUCT_STACK} = ${value}`);
            
            // 3D 철망 X축으로 2만큼 수평 이동 애니메이션 시작
            this.startItem3Stack();
        },
        
        // Item3 적재 애니메이션 시작 (X축으로 2만큼 수평 이동)
        startItem3Stack() {
            if (this.item3Model && (this.item3StackState === 'idle' || this.item3StackState === 'completed')) {
                // 현재 위치를 시작 위치로 저장
                this.item3StackStartPosition = {
                    x: this.item3Model.position.x,
                    y: this.item3Model.position.y,
                    z: this.item3Model.position.z
                };
                
                // 목표 위치: 현재 위치에서 X축으로 2만큼 이동
                this.item3StackTargetPosition = {
                    x: this.item3StackStartPosition.x + 1.3,
                    y: this.item3StackStartPosition.y,
                    z: this.item3StackStartPosition.z
                };
                
                // 적재 애니메이션 시작
                this.item3StackState = 'stacking';
                this.item3StackProgress = 0;
                console.log(`Item3 적재 애니메이션 시작: X축 ${this.item3StackStartPosition.x} -> ${this.item3StackTargetPosition.x}`);
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
}
</style>

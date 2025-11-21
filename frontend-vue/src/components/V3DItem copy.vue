<template>
  <div ref="sceneContainer" class="scene-container">
    <div class="ai-title-container">
      <div class="ai-title">지능형 수중위치추척</div>
      <div class="ai-status">
        <span class="dot-animation">딥러닝 추론중</span>
        <span class="dots">
          <span class="dot">.</span>
          <span class="dot">.</span>
          <span class="dot">.</span>
        </span>
      </div>
    </div>
    
    <div class="result-overlay">
      <div class="result-content">
        <h3>분석 결과</h3>
        <div class="result-values">
          <div class="result-value">
            <span>X:</span>
            <span>{{ formattedX }}</span>
          </div>
          <div class="result-value">
            <span>Y:</span>
            <span>{{ formattedY }}</span>
          </div>
          <div class="result-value">
            <span>Z:</span>
            <span>{{ formattedZ }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="overlay-container">
      <div class="info-panel">
        <h3>수중 통신 장비 정보</h3>
        <div class="device-info">
          <h4>장비 1</h4>
          <p>GPS: {{ device1Position }}</p>
          <p>수온: {{ Math.round(device1Temp) }}°C</p>
          <p>거리: {{ device1Distance }}m</p>
        </div>
        <div class="device-info">
          <h4>장비 2</h4>
          <p>GPS: {{ device2Position }}</p>
          <p>수온: {{ Math.round(device2Temp) }}°C</p>
          <p>거리: {{ device2Distance }}m</p>
        </div>
      </div>
      <div v-if="cameraStatus" class="camera-status">
        {{ cameraStatus }}
      </div>
    </div>
  </div>
</template>

<script>
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'

export default {
  name: 'UnderwaterScene',
  props: {
    resultXYZ: {
      type: Object,
      default: () => ({ x: 0, y: 0, z: 0 })
    }
  },
  computed: {
    formattedX() {
      return this.resultXYZ?.x ? Number(this.resultXYZ.x).toFixed(2) : '0.00'
    },
    formattedY() {
      return this.resultXYZ?.y ? Number(this.resultXYZ.y).toFixed(2) : '0.00'
    },
    formattedZ() {
      return this.resultXYZ?.z ? Number(this.resultXYZ.z).toFixed(2) : '0.00'
    }
  },
  watch: {
    resultXYZ: {
      handler(newVal) {
        console.log('resultXYZ updated:', newVal)
        if (newVal && this.positionText1 && this.positionText3) {
          // 송신기 1 위치 계산
          const newPosition1 = new THREE.Vector3(
            newVal.x * 2,  // X 좌표 스케일 조정
            newVal.y * 2,  // Y 좌표 스케일 조정
            newVal.z * 2   // Z 좌표 스케일 조정
          )
          
          // 송신기 2 위치 계산 (반대 방향으로)
          const newPosition2 = new THREE.Vector3(
            -newVal.x * 2,  // X 좌표 반대 방향
            newVal.y * 2,   // Y 좌표 동일
            -newVal.z * 2   // Z 좌표 반대 방향
          )

          // 위치 텍스트 업데이트
          const updatePositionText = (sprite, position) => {
            const canvas = document.createElement('canvas')
            canvas.width = 1280  // 256 * 5
            canvas.height = 320  // 64 * 5
            const context = canvas.getContext('2d')
            
            context.fillStyle = 'rgba(0, 0, 0, 0.5)'
            context.fillRect(0, 0, canvas.width, canvas.height)
            
            context.font = 'Bold 120px Arial'
            context.fillStyle = 'rgba(255, 255, 255, 0.9)'
            context.textAlign = 'center'
            context.textBaseline = 'middle'
            context.fillText(
              `X:${position.x.toFixed(2)} Y:${position.y.toFixed(2)} Z:${position.z.toFixed(2)}`,
              canvas.width/2,
              canvas.height/2
            )
            
            // 텍스처 업데이트
            if (sprite.material.map) {
              sprite.material.map.dispose()
            }
            sprite.material.map = new THREE.CanvasTexture(canvas)
            sprite.material.needsUpdate = true
          }

          // 스프라이트 위치 및 텍스트 업데이트
          this.positionText1.position.copy(newPosition1)
          this.positionText1.position.y += 7.5
          updatePositionText(this.positionText1, newPosition1)

          this.positionText3.position.copy(newPosition2)
          this.positionText3.position.y += 7.5
          updatePositionText(this.positionText3, newPosition2)
        }
      },
      deep: true,
      immediate: true
    }
  },
  data() {
    return {
      device1Position: '37°12\'N, 126°45\'E',
      device2Position: '37°12\'N, 126°46\'E',
      device1Temp: 18.5,
      device2Temp: 18.2,
      device1Distance: 0,
      device2Distance: 0,
      tempUpdateInterval: null,
      distanceUpdateInterval: null,
      isRotating: false,  // 카메라 회전 상태
      rotationSpeed: Math.PI / 36,  // 5도(약 0.0873 라디안)를 60프레임으로 나눈 값
      cameraStatus: '',  // 카메라 상태 메시지
      controls: null,  // OrbitControls 인스턴스 저장
      distanceSprite1: null,
      distanceSprite3: null,
      underwaterModel: null,
      underwaterModel1: null,
      underwaterModel2: null,
      scene: null,
      camera: null,
      renderer: null,
      clock: null,
      initialCameraPosition: null
    }
  },
  mounted() {
    this.init()
    this.animate()
    // 온도 데이터 주기적 업데이트
    this.tempUpdateInterval = setInterval(this.updateTemperatures, 5000)
    // 거리 데이터 주기적 업데이트
    this.distanceUpdateInterval = setInterval(this.updateDistances, 1000)
    
    // 스페이스바 이벤트 리스너 추가
    window.addEventListener('keydown', this.handleKeyPress)
  },
  beforeDestroy() {
    if (this.tempUpdateInterval) {
      clearInterval(this.tempUpdateInterval)
    }
    if (this.distanceUpdateInterval) {
      clearInterval(this.distanceUpdateInterval)
    }
    // 이벤트 리스너 제거
    window.removeEventListener('keydown', this.handleKeyPress)
  },
  methods: {
    handleKeyPress(event) {
      if (event.code === 'Space') {
        event.preventDefault()  // 스페이스바의 기본 동작 방지
        this.isRotating = !this.isRotating  // 회전 상태 토글
        console.log('회전 상태:', this.isRotating)
        
        if (this.isRotating) {
          this.controls.enabled = false  // 회전 시작시 OrbitControls 비활성화
          this.cameraStatus = '카메라 이동'
          console.log('카메라 회전 시작')
        } else {
          this.controls.enabled = true   // 회전 종료시 OrbitControls 활성화
          this.cameraStatus = '카메라 멈춤'
          console.log('카메라 회전 정지')
        }
      }
    },
    updateTemperatures() {
      // 온도 데이터 랜덤 변화 (18~19도 사이)
      this.device1Temp = 18 + Math.random()
      this.device2Temp = 18 + Math.random()
    },
    updateDistances() {
      // 0~1m 사이의 랜덤한 거리 변화
      this.device1Distance = (20 + Math.random()).toFixed(2)
      this.device2Distance = (20 + Math.random()).toFixed(2)
    },
    init() {
      const container = this.$refs.sceneContainer
      const width = container.clientWidth
      const height = container.clientHeight

      // Scene 설정
      this.scene = new THREE.Scene()
      this.scene.background = new THREE.Color(0x0077be)  // 더 진한 바다색
      this.scene.fog = new THREE.Fog(0x0077be, 30, 100)

      // Clock 초기화
      this.clock = new THREE.Clock()

      // Camera 설정
      this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 200)  // aspect ratio 수정
      this.camera.position.set(0, 25, 35)
      this.camera.lookAt(0, 0, 0)

      // Renderer 설정
      this.renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true
      })
      this.renderer.setSize(width, height)
      this.renderer.setPixelRatio(window.devicePixelRatio)
      this.renderer.shadowMap.enabled = true
      container.appendChild(this.renderer.domElement)

      // 조명 설정
      const ambientLight = new THREE.AmbientLight(0xffffff, 1.0)  // 전체 밝기 증가
      this.scene.add(ambientLight)

      const dirLight = new THREE.DirectionalLight(0xffffff, 2.5)  // 직사광 밝기 증가
      dirLight.position.set(50, 100, 50)
      dirLight.castShadow = true
      this.scene.add(dirLight)

      // 모래 바닥 텍스처 로딩 수정
      const floorMat = new THREE.MeshStandardMaterial({
        color: 0xd2b48c,
        roughness: 0.8,
        metalness: 0.2
      })

      // 바닥 텍스처 로딩
      new THREE.TextureLoader().load('/textures/sand.jpg', 
        // 텍스처 로드 성공
        (texture) => {
          texture.wrapS = texture.wrapT = THREE.RepeatWrapping
          texture.repeat.set(50, 50)
          floorMat.map = texture
          floorMat.needsUpdate = true
        },
        // 로딩 중
        undefined,
        // 에러 처리
        (err) => {
          console.error('텍스처 로딩 실패:', err)
          // 텍스처 로드 실패시 기본 색상 사용
          floorMat.color.setHex(0xd2b48c)
        }
      )

      // 바닥 지오메트리
      const floorGeo = new THREE.PlaneGeometry(100, 100, 128, 128)
      floorGeo.rotateX(-Math.PI / 2)  // 회전 수정
      const floor = new THREE.Mesh(floorGeo, floorMat)
      floor.receiveShadow = true
      this.scene.add(floor)

      // 수면 Plane (움직이는 vertex displacement)
      const waterGeo = new THREE.PlaneGeometry(100, 100, 64, 64)
      waterGeo.rotateX(-Math.PI / 2)

      const waterMat = new THREE.MeshPhongMaterial({
        color: 0x88ccff,
        transparent: true,
        opacity: 0.3,
        shininess: 200,
        side: THREE.DoubleSide
      })

      const water = new THREE.Mesh(waterGeo, waterMat)
      water.position.y = 18
      this.scene.add(water)

      // 수중 무선 통신 장비 생성
      const createUnderwaterDevice = (x, z, isTransmitter = false) => {
        const deviceGroup = new THREE.Group()
        
        if (isTransmitter) {
          // 다이버 형태로 변경
          // 몸체 (실린더)
          const bodyGeometry = new THREE.CylinderGeometry(0.13, 0.13, 0.67, 16)  // 크기 1/3로 감소
          const bodyMaterial = new THREE.MeshPhongMaterial({
            color: 0x000000,  // 검은색 잠수복
            shininess: 30
          })
          const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
          body.rotation.x = Math.PI / 2  // 수평으로 눕히기
          deviceGroup.add(body)

          // 머리 (구체)
          const headGeometry = new THREE.SphereGeometry(0.13, 16, 16)  // 크기 1/3로 감소
          const headMaterial = new THREE.MeshPhongMaterial({
            color: 0x000000,  // 검은색 잠수복
            shininess: 30
          })
          const head = new THREE.Mesh(headGeometry, headMaterial)
          head.position.z = 0.4  // 위치 1/3로 감소
          deviceGroup.add(head)

          // 산소통 (실린더)
          const tankGeometry = new THREE.CylinderGeometry(0.07, 0.07, 0.5, 16)  // 크기 1/3로 감소
          const tankMaterial = new THREE.MeshPhongMaterial({
            color: 0x444444,  // 회색
            shininess: 50
          })
          const tank = new THREE.Mesh(tankGeometry, tankMaterial)
          tank.rotation.x = Math.PI / 2
          tank.position.y = 0.1  // 위치 1/3로 감소
          deviceGroup.add(tank)

          // 팔 (왼쪽)
          const leftArmGeometry = new THREE.CylinderGeometry(0.03, 0.03, 0.33, 8)  // 크기 1/3로 감소
          const armMaterial = new THREE.MeshPhongMaterial({
            color: 0x000000,
            shininess: 30
          })
          const leftArm = new THREE.Mesh(leftArmGeometry, armMaterial)
          leftArm.position.set(0.17, 0, 0.1)  // 위치 1/3로 감소
          leftArm.rotation.z = Math.PI / 4
          deviceGroup.add(leftArm)

          // 팔 (오른쪽)
          const rightArm = new THREE.Mesh(leftArmGeometry, armMaterial)
          rightArm.position.set(-0.17, 0, 0.1)  // 위치 1/3로 감소
          rightArm.rotation.z = -Math.PI / 4
          deviceGroup.add(rightArm)

          // 다리 (왼쪽)
          const legGeometry = new THREE.CylinderGeometry(0.04, 0.04, 0.4, 8)  // 크기 1/3로 감소
          const legMaterial = new THREE.MeshPhongMaterial({
            color: 0x000000,
            shininess: 30
          })
          const leftLeg = new THREE.Mesh(legGeometry, legMaterial)
          leftLeg.position.set(0.07, 0, -0.27)  // 위치 1/3로 감소
          leftLeg.rotation.x = -Math.PI / 6
          deviceGroup.add(leftLeg)

          // 다리 (오른쪽)
          const rightLeg = new THREE.Mesh(legGeometry, legMaterial)
          rightLeg.position.set(-0.07, 0, -0.27)  // 위치 1/3로 감소
          rightLeg.rotation.x = -Math.PI / 6
          deviceGroup.add(rightLeg)

          // 오리발 (왼쪽)
          const finGeometry = new THREE.BoxGeometry(0.07, 0.02, 0.13)  // 크기 1/3로 감소
          const finMaterial = new THREE.MeshPhongMaterial({
            color: 0x0000ff,  // 파란색
            shininess: 30
          })
          const leftFin = new THREE.Mesh(finGeometry, finMaterial)
          leftFin.position.set(0.07, 0, -0.43)  // 위치 1/3로 감소
          leftFin.rotation.x = Math.PI / 6
          deviceGroup.add(leftFin)

          // 오리발 (오른쪽)
          const rightFin = new THREE.Mesh(finGeometry, finMaterial)
          rightFin.position.set(-0.07, 0, -0.43)  // 위치 1/3로 감소
          rightFin.rotation.x = Math.PI / 6
          deviceGroup.add(rightFin)

          // 마스크의 유리 부분 (반투명)
          const glassGeometry = new THREE.SphereGeometry(0.08, 16, 16)  // 크기 1/3로 감소
          const glassMaterial = new THREE.MeshPhongMaterial({
            color: 0x88ccff,
            transparent: true,
            opacity: 0.6,
            shininess: 100
          })
          const glass = new THREE.Mesh(glassGeometry, glassMaterial)
          glass.position.z = 0.47  // 위치 1/3로 감소
          glass.scale.z = 0.5  // 납작하게
          deviceGroup.add(glass)

          // 통신 장비 (등에 부착)
          const commDeviceGeometry = new THREE.BoxGeometry(0.13, 0.07, 0.2)  // 크기 1/3로 감소
          const commDeviceMaterial = new THREE.MeshPhongMaterial({
            color: 0x333333,
            shininess: 50
          })
          const commDevice = new THREE.Mesh(commDeviceGeometry, commDeviceMaterial)
          commDevice.position.y = 0.13  // 위치 1/3로 감소
          commDevice.position.z = -0.07  // 위치 1/3로 감소
          deviceGroup.add(commDevice)

          // LED 표시등
          const ledGeometry = new THREE.SphereGeometry(0.02, 8, 8)  // 크기 1/3로 감소
          const ledMaterial = new THREE.MeshPhongMaterial({
            color: 0x00ff00,
            emissive: 0x00ff00,
            emissiveIntensity: 0.5
          })
          const led = new THREE.Mesh(ledGeometry, ledMaterial)
          led.position.set(0, 0.13, 0)  // 위치 1/3로 감소
          commDevice.add(led)
          
          deviceGroup.position.set(x, 3.6, z)
        } else {
          // 선박 형태
          // 선체
          const loader = new GLTFLoader()
          loader.load('/model/D0405211D92.glb', (gltf) => {
            const model = gltf.scene
            model.scale.set(5, 5, 5) // 크기를 5배로 증가
            model.rotation.y = Math.PI / 2 // Y축 기준 90도 회전
            
            // 선체의 재질을 더 밝고 금속성이 있게 수정
            model.traverse((child) => {
              if (child.isMesh) {
                child.material = new THREE.MeshStandardMaterial({
                  color: 0x888888,  // 밝은 회색
                  metalness: 0.8,   // 금속성 증가
                  roughness: 0.2,   // 광택 증가
                  envMapIntensity: 1.0  // 환경 반사 강도
                })
              }
            })
            
            deviceGroup.add(model)
            
            // 신호등 추가
            const createSignalLight = (color, position) => {
              const lightGeometry = new THREE.SphereGeometry(0.025, 16, 16)  // 크기를 0.075에서 0.025로 줄임 (3배 작게)
              const lightMaterial = new THREE.MeshPhongMaterial({
                color: color,
                emissive: color,
                emissiveIntensity: 0.5,
                shininess: 100
              })
              const light = new THREE.Mesh(lightGeometry, lightMaterial)
              light.position.copy(position)
              return light
            }

            // 신호등 컨테이너 생성
            const lightsContainer = new THREE.Group()
            
            // 배 중앙을 (0,0,0)으로 보고 신호등 배치 (오른쪽으로 40% 이동)
            const signalLight1 = createSignalLight(0xff0000, new THREE.Vector3(0.4, 0, 0))  // 빨간색, 왼쪽
            const signalLight2 = createSignalLight(0xffff00, new THREE.Vector3(0.6, 0, 0))     // 노란색, 중앙
            const signalLight3 = createSignalLight(0x00ff00, new THREE.Vector3(0.8, 0, 0))   // 초록색, 오른쪽
            
            // 신호등에 발광 효과 추가 (크기와 위치 조정)
            const createGlow = (color, position) => {
              const glowGeometry = new THREE.SphereGeometry(0.033, 16, 16)  // 크기를 0.1에서 0.033로 줄임 (3배 작게)
              const glowMaterial = new THREE.MeshBasicMaterial({
                color: color,
                transparent: true,
                opacity: 0.3
              })
              const glow = new THREE.Mesh(glowGeometry, glowMaterial)
              glow.position.copy(position)
              return glow
            }

            // 발광 효과 추가 (위치 조정)
            const glow1 = createGlow(0xff0000, new THREE.Vector3(0.4, 0, 0))
            const glow2 = createGlow(0xffff00, new THREE.Vector3(0.6, 0, 0))
            const glow3 = createGlow(0x00ff00, new THREE.Vector3(0.8, 0, 0))
            
            // 모든 신호등과 발광효과를 컨테이너에 추가
            lightsContainer.add(signalLight1, signalLight2, signalLight3)
            lightsContainer.add(glow1, glow2, glow3)
            
            // 컨테이너의 위치를 배의 중심으로 조정
            lightsContainer.position.set(0, 0, 0)
            
            // 컨테이너를 모델에 추가
            model.add(lightsContainer)

            // 신호등 정보를 객체에 저장
            deviceGroup.userData.signalLights = {
              red: { light: signalLight1, glow: glow1 },
              yellow: { light: signalLight2, glow: glow2 },
              green: { light: signalLight3, glow: glow3 }
            }
            
            deviceGroup.position.set(x, 17.5, z)  // 수면 위에 위치
          })
        }
        
        return {
          mesh: deviceGroup,
          basePosition: new THREE.Vector3(x, isTransmitter ? 3.6 : 17.5, z)  // 송신기 높이를 3.6으로 조정 (수면 높이 18의 20%)
        }
      }
      
      // 장비 생성
      const device1 = createUnderwaterDevice(-10, -10, true)  // 첫 번째 다이버 (왼쪽 앞)
      const device2 = createUnderwaterDevice(40, 0, false)    // 선박 (오른쪽으로 40% 이동)
      const device3 = createUnderwaterDevice(10, 10, true)   // 두 번째 다이버 (오른쪽 뒤)
      
      this.scene.add(device1.mesh)
      this.scene.add(device2.mesh)
      this.scene.add(device3.mesh)

      // 위치 표시 박스 생성 함수
      const createPositionBox = (position, color) => {
        const boxGeometry = new THREE.BoxGeometry(5, 5, 5)  // 크기를 1에서 5로 변경
        const boxMaterial = new THREE.MeshBasicMaterial({
          color: color,
          transparent: true,
          opacity: 0.3,
          wireframe: true
        })
        const box = new THREE.Mesh(boxGeometry, boxMaterial)
        box.position.copy(position)
        return box
      }

      // 위치 표시 박스와 텍스트 생성
      const positionBox1 = createPositionBox(device1.mesh.position, 0xff0000)
      const positionBox3 = createPositionBox(device3.mesh.position, 0x00ff00)
      
      // 위치 텍스트 스프라이트 생성 함수
      const createPositionText = (position) => {
        const canvas = document.createElement('canvas')
        canvas.width = 1280  // 256 * 5
        canvas.height = 320  // 64 * 5
        const context = canvas.getContext('2d')
        
        context.fillStyle = 'rgba(0, 0, 0, 0.5)'
        context.fillRect(0, 0, canvas.width, canvas.height)
        
        context.font = 'Bold 120px Arial'
        context.fillStyle = 'rgba(255, 255, 255, 0.9)'
        context.textAlign = 'center'
        context.textBaseline = 'middle'
        context.fillText(
          `X:${position.x.toFixed(2)} Y:${position.y.toFixed(2)} Z:${position.z.toFixed(2)}`,
          canvas.width/2,
          canvas.height/2
        )
        
        const texture = new THREE.CanvasTexture(canvas)
        const spriteMaterial = new THREE.SpriteMaterial({
          map: texture,
          transparent: true
        })
        
        const sprite = new THREE.Sprite(spriteMaterial)
        sprite.scale.set(10, 2.5, 1)  // 2 * 5, 0.5 * 5
        sprite.position.copy(position)
        sprite.position.y += 7.5  // 박스 위에 표시
        
        return sprite
      }

      // 위치 텍스트 스프라이트 생성
      this.positionText1 = createPositionText(device1.mesh.position)
      this.positionText3 = createPositionText(device3.mesh.position)
      
      this.scene.add(positionBox1)
      this.scene.add(positionBox3)
      this.scene.add(this.positionText1)
      this.scene.add(this.positionText3)

      // 위치 업데이트 함수
      const updatePositionIndicators = () => {
        // 박스 위치 업데이트
        positionBox1.position.copy(device1.mesh.position)
        positionBox3.position.copy(device3.mesh.position)
        
        // 텍스트 위치 업데이트
        this.positionText1.position.copy(device1.mesh.position)
        this.positionText1.position.y += 7.5
        this.positionText3.position.copy(device3.mesh.position)
        this.positionText3.position.y += 7.5
      }

      // 통신 신호 파티클 시스템
      const createSignalParticles = () => {
        const particleCount = 900
        const particles = new THREE.BufferGeometry()
        const positions = new Float32Array(particleCount * 3)
        const colors = new Float32Array(particleCount * 3)
        
        for (let i = 0; i < particleCount; i++) {
          positions[i * 3] = 0
          positions[i * 3 + 1] = 0
          positions[i * 3 + 2] = 0
          
          colors[i * 3] = 1
          colors[i * 3 + 1] = 0.2
          colors[i * 3 + 2] = 0.2
        }
        
        particles.setAttribute('position', new THREE.BufferAttribute(positions, 3))
        particles.setAttribute('color', new THREE.BufferAttribute(colors, 3))
        
        const particleMaterial = new THREE.PointsMaterial({
          size: 0.3,
          vertexColors: true,
          transparent: true,
          opacity: 0.6
        })
        
        return new THREE.Points(particles, particleMaterial)
      }
      
      const signalParticles1 = createSignalParticles()  // 첫 번째 다이버의 신호
      const signalParticles2 = createSignalParticles()  // 두 번째 다이버의 신호
      this.scene.add(signalParticles1)
      this.scene.add(signalParticles2)

      // 통신 신호 파티클 업데이트 함수
      const updateSignalParticles = (particles, startPos, endPos, progress) => {
        const positions = particles.geometry.attributes.position.array
        const colors = particles.geometry.attributes.color.array
        
        // 3개의 방사형 신호 생성
        const numArcs = 5
        const pointsPerArc = positions.length / 3 / numArcs
        
        // 각각 다른 높이에서 시작하는 3개의 방사형 신호
        for (let signalIndex = 0; signalIndex < 3; signalIndex++) {
          const verticalOffset = (signalIndex - 1) * 1  // 높이 차이를 줄임
          
          for (let arc = 0; arc < numArcs; arc++) {
            const arcProgress = ((progress + arc / numArcs) % 1)
            
            for (let i = 0; i < pointsPerArc; i++) {
              const idx = (signalIndex * pointsPerArc * numArcs + arc * pointsPerArc + i) * 3
              // -90도에서 90도 사이의 각도로 제한 (반원)
              const angle = (-Math.PI/2) + (i / pointsPerArc) * Math.PI
              
              // 반경 계산 (진행에 따라 점점 커짐)
              const radius = arcProgress * 25
              
              // 위치 계산 (방사형) - 송신기 위치에서 시작
              const x = startPos.x + Math.cos(angle) * radius
              const y = startPos.y + verticalOffset + radius * 0.3  // 상승 각도를 줄임
              const z = startPos.z + Math.sin(angle) * radius
              
              positions[idx] = x
              positions[idx + 1] = y
              positions[idx + 2] = z
              
              // 색상 및 투명도 (거리에 따른 페이드 아웃)
              const fadeEffect = Math.max(0, 1 - arcProgress)
              colors[idx] = 1
              colors[idx + 1] = 0.2 * fadeEffect
              colors[idx + 2] = 0.2 * fadeEffect
            }
          }
        }
        
        particles.geometry.attributes.position.needsUpdate = true
        particles.geometry.attributes.color.needsUpdate = true
      }

      // 거리 표시용 스프라이트 텍스트 생성 함수
      const createDistanceSprite = () => {
        const canvas = document.createElement('canvas')
        canvas.width = 512
        canvas.height = 256
        const context = canvas.getContext('2d')
        
        // 캔버스 초기화
        context.fillStyle = 'rgba(0, 0, 0, 0.5)'
        context.fillRect(0, 0, canvas.width, canvas.height)
        
        // AI 분석 효과를 위한 초기 설정
        const drawAIEffect = (progress) => {
          // 배경 초기화
          context.fillStyle = 'rgba(0, 0, 0, 0.5)'
          context.fillRect(0, 0, canvas.width, canvas.height)
          
          // AI 분석 원형 파형 그리기
          const centerX = canvas.width / 2
          const centerY = canvas.height / 2
          const maxRadius = 100
          
          // 3개의 동심원 그리기
          for (let i = 0; i < 3; i++) {
            const radius = (progress * maxRadius * (i + 1) / 3) % maxRadius
            context.beginPath()
            context.arc(centerX, centerY, radius, 0, Math.PI * 2)
            context.strokeStyle = `rgba(0, 255, 255, ${0.5 - (radius / maxRadius) * 0.3})`
            context.lineWidth = 2
            context.stroke()
          }
          
          // 십자선 그리기
          const crossSize = 10
          context.beginPath()
          context.moveTo(centerX - crossSize, centerY)
          context.lineTo(centerX + crossSize, centerY)
          context.moveTo(centerX, centerY - crossSize)
          context.lineTo(centerX, centerY + crossSize)
          context.strokeStyle = 'rgba(0, 255, 255, 0.8)'
          context.lineWidth = 1
          context.stroke()
          
          // 거리 텍스트 그리기
          context.font = 'Bold 120px Arial'
          context.fillStyle = 'rgba(0, 255, 255, 0.9)'
          context.textAlign = 'center'
          context.textBaseline = 'middle'
          context.fillText('분석중...', centerX, centerY - 60)
        }
        
        // 초기 AI 분석 효과 그리기
        drawAIEffect(0)
        
        // 텍스처 생성
        const texture = new THREE.CanvasTexture(canvas)
        const spriteMaterial = new THREE.SpriteMaterial({
          map: texture,
          transparent: true
        })
        
        const sprite = new THREE.Sprite(spriteMaterial)
        sprite.scale.set(4, 2, 1)
        
        // AI 효과 함수를 userData에 저장
        sprite.userData = { 
          context,
          texture,
          drawAIEffect,
          analysisStartTime: 0,
          isAnalyzing: true,
          lastAnalysisTime: 0
        }
        
        return sprite
      }

      // 두 개의 거리 스프라이트 생성
      this.distanceSprite1 = createDistanceSprite()
      this.distanceSprite3 = createDistanceSprite()
      this.scene.add(this.distanceSprite1)
      this.scene.add(this.distanceSprite3)

      // 거리 측정을 위한 라인 생성
      const createDistanceLine = (color) => {
        const material = new THREE.LineBasicMaterial({
          color: color,
          linewidth: 2,
          transparent: true,
          opacity: 0.7
        })
        const geometry = new THREE.BufferGeometry()
        const line = new THREE.Line(geometry, material)
        return line
      }

      // 두 개의 거리 측정 라인 생성
      const distanceLine1 = createDistanceLine(0xff0000)
      const distanceLine3 = createDistanceLine(0x00ff00)
      this.scene.add(distanceLine1)
      this.scene.add(distanceLine3)

      // 애니메이션 연결
      this.controls = new OrbitControls(this.camera, this.renderer.domElement)
      this.controls.enableDamping = true // 부드러운 모션
      this.controls.dampingFactor = 0.05
      this.controls.screenSpacePanning = false
      this.controls.minDistance = 10
      this.controls.maxDistance = 100
      this.controls.maxPolarAngle = Math.PI / 2 // 아래로 카메라가 못 내려가게 제한
      this.controls.enabled = true // OrbitControls 활성화 상태 관리
      
      // 초기 카메라 위치 저장
      this.initialCameraPosition = {
        x: this.camera.position.x,
        y: this.camera.position.y,
        z: this.camera.position.z
      }
      console.log('초기 카메라 위치:', this.initialCameraPosition)

      // GLB 로더 생성
      const loader = new GLTFLoader();
      
      // 첫 번째 수중 모델 로드 (송신기1 옆)
      loader.load('/model/nude03_m_highpoly.glb', (gltf) => {
        const model1 = gltf.scene;
        model1.scale.set(2.1, 2.1, 2.1);  // 크기를 0.7에서 2.1로 증가 (3배)
        model1.rotation.x = -Math.PI / 2;
        model1.position.set(-10, 3.6, -10);  // 첫 번째 송신기와 동일한 위치로 변경
        
        this.scene.add(model1);
        this.underwaterModel1 = model1;

        // 모델의 재질 설정
        model1.traverse((child) => {
          if (child.isMesh) {
            child.material.transparent = true;
            child.material.opacity = 0.85;
            child.material.emissive = new THREE.Color(0x00aaff);
            child.material.emissiveIntensity = 0.4;
            child.material.metalness = 0.3;
            child.material.roughness = 0.6;
          }
        });
      });

      // 두 번째 수중 모델 로드 (송신기2 옆)
      loader.load('/model/nude03_m_highpoly.glb', (gltf) => {
        const model2 = gltf.scene;
        model2.scale.set(2.1, 2.1, 2.1);  // 크기를 0.7에서 2.1로 증가 (3배)
        model2.rotation.x = -Math.PI / 2;
        model2.position.set(10, 3.6, 10);  // 두 번째 송신기와 동일한 위치로 변경
        
        this.scene.add(model2);
        this.underwaterModel2 = model2;

        // 모델의 재질 설정
        model2.traverse((child) => {
          if (child.isMesh) {
            child.material.transparent = true;
            child.material.opacity = 0.85;
            child.material.emissive = new THREE.Color(0x00aaff);
            child.material.emissiveIntensity = 0.4;
            child.material.metalness = 0.3;
            child.material.roughness = 0.6;
          }
        });
      });

      // 애니메이션 루프
      const animate = () => {
        requestAnimationFrame(animate)
        const time = this.clock.getElapsedTime()

        // 카메라 자동 회전
        if (this.isRotating && this.camera && this.initialCameraPosition) {
          console.log('카메라 회전 중:', time)
          const radius = Math.sqrt(
            Math.pow(this.initialCameraPosition.x, 2) + 
            Math.pow(this.initialCameraPosition.z, 2)
          )
          
          // 회전 각도 계산 (시간에 따라 증가)
          const angle = time * this.rotationSpeed
          
          // 카메라 위치 업데이트
          this.camera.position.x = radius * Math.cos(angle)
          this.camera.position.z = radius * Math.sin(angle)
          this.camera.position.y = this.initialCameraPosition.y
          this.camera.lookAt(0, 0, 0)

          console.log('카메라 새 위치:', {
            x: this.camera.position.x,
            y: this.camera.position.y,
            z: this.camera.position.z
          })
        }

        // 해저 바닥 물결 애니메이션
        const floorPosition = floor.geometry.attributes.position
        for (let i = 0; i < floorPosition.count; i++) {
          const x = floorPosition.getX(i)
          const z = floorPosition.getZ(i)
          // 시간에 따라 변화하는 물결 효과
          const y = Math.sin(x * 0.1 + time * 0.2) * 0.3 + 
                   Math.cos(z * 0.1 + time * 0.3) * 0.3 +
                   Math.sin((x + z) * 0.1 + time * 0.4) * 0.2
          floorPosition.setY(i, y)
        }
        floorPosition.needsUpdate = true

        // 물결 애니메이션
        const waterPos = waterGeo.attributes.position
        for (let i = 0; i < waterPos.count; i++) {
          const x = waterPos.getX(i)
          const z = waterPos.getZ(i)
          const y = Math.sin(x * 0.2 + time) * 0.2 + Math.cos(z * 0.2 + time * 0.8) * 0.2
          waterPos.setY(i, y)
        }
        waterPos.needsUpdate = true
        water.material.opacity = 0.25 + Math.sin(time * 2) * 0.05

        // 다이버 움직임
        device1.mesh.rotation.y = Math.sin(time * 0.5) * 0.1
        device3.mesh.rotation.y = Math.sin(time * 0.5 + Math.PI) * 0.1  // 반대 위상

        // 신호 업데이트 - 첫 번째 다이버
        updateSignalParticles(
          signalParticles1,
          device1.mesh.position,
          device2.mesh.position,
          (time % 3) / 3
        )

        // 신호 업데이트 - 두 번째 다이버
        updateSignalParticles(
          signalParticles2,
          device3.mesh.position,
          device2.mesh.position,
          ((time + 1.5) % 3) / 3  // 시간 차이를 두어 번갈아가며 신호 발생
        )

        // 선박 움직임 애니메이션
        device2.mesh.rotation.x = Math.sin(time * 0.5) * 0.05
        device2.mesh.position.y = 17.5 + Math.sin(time * 0.8) * 0.2

        // 신호등 깜빡임 애니메이션
        if (device2.mesh.userData.signalLights) {
          const lights = device2.mesh.userData.signalLights
          const updateLight = (light, intensity) => {
            light.light.material.emissiveIntensity = intensity
            light.glow.material.opacity = intensity * 0.3
          }
          
          updateLight(lights.red, 0.5 + Math.sin(time * 5) * 0.5)
          updateLight(lights.yellow, 0.5 + Math.sin(time * 4.5 + Math.PI/2) * 0.5)
          updateLight(lights.green, 0.5 + Math.sin(time * 4.7 + Math.PI) * 0.5)
        }

        // 거리 측정 라인 업데이트
        const updateDistanceLine = (line, startPos, endPos, sprite) => {
          const positions = new Float32Array([
            startPos.x, startPos.y, startPos.z,
            endPos.x, endPos.y, endPos.z
          ])
          line.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
          line.geometry.attributes.position.needsUpdate = true

          // 거리 계산
          const distance = startPos.distanceTo(endPos)
          
          // 스프라이트 위치 업데이트
          sprite.position.set(
            (startPos.x + endPos.x) / 2,
            (startPos.y + endPos.y) / 2 + 1,
            (startPos.z + endPos.z) / 2
          )

          const currentTime = this.clock.getElapsedTime()
          
          // AI 분석 애니메이션 처리
          if (sprite.userData.isAnalyzing) {
            if (sprite.userData.analysisStartTime === 0) {
              sprite.userData.analysisStartTime = currentTime
            }
            
            const analysisDuration = 2.0 // 분석 지속 시간 (초)
            //const analysisInterval = 4.0  // 분석 주기 (4초)
            const progress = (currentTime - sprite.userData.analysisStartTime) / analysisDuration
            
            if (progress < 1.0) {
              // 분석 중 애니메이션
              sprite.userData.drawAIEffect(progress)
              sprite.userData.texture.needsUpdate = true
            } else {
              // 분석 완료
              sprite.userData.isAnalyzing = false
              sprite.userData.lastAnalysisTime = currentTime
            }
          } else {
            // 다음 분석 시작 시간 체크
            const timeSinceLastAnalysis = currentTime - (sprite.userData.lastAnalysisTime || 0)
            if (timeSinceLastAnalysis >= 4.0) {  // 4초마다 분석 상태 리셋
              sprite.userData.isAnalyzing = true
              sprite.userData.analysisStartTime = 0
            } else {
              // 분석 완료 후 일반 거리 표시
              const context = sprite.userData.context
              context.clearRect(0, 0, context.canvas.width, context.canvas.height)
              context.fillStyle = 'rgba(0, 0, 0, 0.5)'
              context.fillRect(0, 0, context.canvas.width, context.canvas.height)
              
              // 결과 텍스트 그리기
              context.font = 'Bold 120px Arial'
              context.fillStyle = 'rgba(0, 255, 255, 0.9)'
              context.textAlign = 'center'
              context.textBaseline = 'middle'
              context.fillText(`${distance.toFixed(2)}m`, context.canvas.width/2, context.canvas.height/2)
              
              sprite.userData.texture.needsUpdate = true
            }
          }
        }

        // 배와 다이버 사이의 거리 라인과 스프라이트 업데이트
        updateDistanceLine(distanceLine1, device2.mesh.position, device1.mesh.position, this.distanceSprite1)
        updateDistanceLine(distanceLine3, device2.mesh.position, device3.mesh.position, this.distanceSprite3)

        // 위치 표시 업데이트
        updatePositionIndicators()

        // 애니메이션 루프 내부
        if (this.controls) {
          this.controls.update()
        }

        // 수중 모델 움직임 애니메이션
        if (this.underwaterModel1) {
          this.underwaterModel1.position.y = 3.6 + Math.sin(Date.now() * 0.001) * 0.3;
          this.underwaterModel1.rotation.z = Math.sin(Date.now() * 0.0005) * 0.1;
          this.underwaterModel1.position.x = -10 + Math.sin(Date.now() * 0.0008) * 0.2;
        }

        if (this.underwaterModel2) {
          this.underwaterModel2.position.y = 3.6 + Math.cos(Date.now() * 0.001) * 0.3;
          this.underwaterModel2.rotation.z = Math.sin(Date.now() * 0.0005 + Math.PI) * 0.1;
          this.underwaterModel2.position.x = 10 + Math.sin(Date.now() * 0.0008 + Math.PI) * 0.2;
        }

        this.renderer.render(this.scene, this.camera)
      }

      // resize 이벤트 핸들러 수정
      const handleResize = () => {
        const newWidth = container.clientWidth
        const newHeight = container.clientHeight
        this.camera.aspect = newWidth / newHeight
        this.camera.updateProjectionMatrix()
        this.renderer.setSize(newWidth, newHeight)
      }

      window.addEventListener('resize', handleResize)

      animate()
    },
    animate() {
      requestAnimationFrame(this.animate)
      
      // 카메라 자동 회전
      if (this.isRotating && this.camera && this.initialCameraPosition) {
        const time = this.clock.getElapsedTime()
        const radius = Math.sqrt(
          Math.pow(this.initialCameraPosition.x, 2) + 
          Math.pow(this.initialCameraPosition.z, 2)
        )
        
        // 회전 각도 계산 (시간에 따라 증가)
        const angle = time * this.rotationSpeed
        
        // 카메라 위치 업데이트
        this.camera.position.x = radius * Math.cos(angle)
        this.camera.position.z = radius * Math.sin(angle)
        this.camera.position.y = this.initialCameraPosition.y
        this.camera.lookAt(0, 0, 0)
      }

      // 첫 번째 모델 애니메이션 - 송신기1 위치 기준
      if (this.underwaterModel1) {
        this.underwaterModel1.position.y = 3.6 + Math.sin(Date.now() * 0.001) * 0.3;
        this.underwaterModel1.rotation.z = Math.sin(Date.now() * 0.0005) * 0.1;
        this.underwaterModel1.position.x = -10 + Math.sin(Date.now() * 0.0008) * 0.2;
      }

      // 두 번째 모델 애니메이션 - 송신기2 위치 기준
      if (this.underwaterModel2) {
        this.underwaterModel2.position.y = 3.6 + Math.cos(Date.now() * 0.001) * 0.3;
        this.underwaterModel2.rotation.z = Math.sin(Date.now() * 0.0005 + Math.PI) * 0.1;
        this.underwaterModel2.position.x = 10 + Math.sin(Date.now() * 0.0008 + Math.PI) * 0.2;
      }
      
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera)
      }
    }
  }
}
</script>

<style scoped>
.scene-container {
  position: relative;
  width: 100%;  /* 부모 요소의 전체 너비 사용 */
  height: 100vh;  /* 뷰포트 높이 전체 사용 */
  overflow: hidden;
}

.overlay-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;  /* 부모 요소의 전체 너비 사용 */
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.info-panel {
  position: absolute;
  bottom: 20px;  /* 위치를 다시 하단으로 변경 */
  left: 20px;
  background-color: rgba(0, 0, 0, 0.3);  /* 투명도 원복 */
  color: white;
  padding: 15px;
  border-radius: 8px;
  pointer-events: auto;
  font-family: Arial, sans-serif;
  min-width: 200px;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.info-panel h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #00ff00;
}

.device-info {
  margin-bottom: 15px;
}

.device-info:last-child {
  margin-bottom: 0;
}

.device-info h4 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #88ccff;
}

.device-info p {
  margin: 3px 0;
  font-size: 13px;
  color: #ffffff;
}

.distance-info {
  color: #00ff00;
  font-weight: bold;
}

.camera-status {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background-color: rgba(0, 0, 0, 0.5);
  color: #ffffff;
  padding: 10px 20px;
  border-radius: 5px;
  font-size: 14px;
  pointer-events: none;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-title-container {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 2;
  color: #00ffff;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.ai-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.ai-status {
  font-size: 16px;
  display: flex;
  align-items: center;
}

.dot-animation {
  color: #00ffff;
  margin-right: 5px;
}

.dots {
  display: inline-flex;
}

.dot {
  opacity: 0;
  animation: dotAnimation 1.5s infinite;
  margin-left: 2px;
}

.dot:nth-child(2) {
  animation-delay: 0.5s;
}

.dot:nth-child(3) {
  animation-delay: 1s;
}

@keyframes dotAnimation {
  0% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}

.result-overlay {
  position: fixed;
  top: 50%;
  right: 20px;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.6);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 255, 0.5);
  color: #fff;
  z-index: 9999;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
  min-width: 180px;
  pointer-events: auto;
  backdrop-filter: blur(3px);
}

.result-content {
  h3 {
    margin: 0 0 12px 0;
    font-size: 18px;
    color: rgba(0, 255, 255, 0.9);
    text-align: center;
    text-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
    font-weight: bold;
  }
}

.result-values {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(0, 255, 255, 0.05);
  padding: 8px;
  border-radius: 4px;
}

.result-value {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  font-size: 16px;
  
  span:first-child {
    color: rgba(0, 255, 255, 0.9);
    font-weight: bold;
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
  }
  
  span:last-child {
    font-family: monospace;
    min-width: 80px;
    text-align: right;
    color: rgba(255, 255, 255, 0.9);
    background: rgba(0, 255, 255, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
  }
}
</style>

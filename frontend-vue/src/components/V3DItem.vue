<template>
  <div ref="sceneContainer" class="scene-container"></div>
</template>

<script>
import * as THREE from 'three';

export default {
  name: 'V3DItem',
  mounted() {
    this.init3D();
  },
  methods: {
    init3D() {
      const container = this.$refs.sceneContainer;
      const width = container.clientWidth || 800;
      const height = container.clientHeight || 600;

      // Scene, Camera, Renderer
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xf0f0f0);
      const camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
      camera.position.set(100, 120, 180);
      camera.lookAt(0, 0, 0);

      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(width, height);
      container.appendChild(renderer.domElement);

      // Light
      const light = new THREE.DirectionalLight(0xffffff, 1);
      light.position.set(100, 200, 100);
      scene.add(light);

      // 1. 프레임(초록색)
      const frameMaterial = new THREE.MeshPhongMaterial({ color: 0x33cc33 });
      const frame1 = new THREE.Mesh(new THREE.BoxGeometry(10, 80, 10), frameMaterial);
      frame1.position.set(-40, 40, -40);
      scene.add(frame1);

      const frame2 = frame1.clone();
      frame2.position.set(40, 40, -40);
      scene.add(frame2);

      const frame3 = frame1.clone();
      frame3.position.set(-40, 40, 40);
      scene.add(frame3);

      const frame4 = frame1.clone();
      frame4.position.set(40, 40, 40);
      scene.add(frame4);

      // 상단 빔
      const beamMaterial = new THREE.MeshPhongMaterial({ color: 0x33cc33 });
      const beam1 = new THREE.Mesh(new THREE.BoxGeometry(90, 10, 10), beamMaterial);
      beam1.position.set(0, 80, -40);
      scene.add(beam1);

      const beam2 = beam1.clone();
      beam2.position.set(0, 80, 40);
      scene.add(beam2);

      // 2. 오렌지색 부품
      const orangeMaterial = new THREE.MeshPhongMaterial({ color: 0xff6600 });
      const orangeBox = new THREE.Mesh(new THREE.BoxGeometry(60, 5, 10), orangeMaterial);
      orangeBox.position.set(0, 60, 0);
      scene.add(orangeBox);

      // 3. 작업대(그리드)
      const gridMaterial = new THREE.MeshPhongMaterial({ color: 0xcccccc });
      for (let i = -20; i <= 20; i += 10) {
        for (let j = -20; j <= 20; j += 10) {
          const gridBox = new THREE.Mesh(new THREE.BoxGeometry(8, 2, 8), gridMaterial);
          gridBox.position.set(i, 2, j);
          scene.add(gridBox);
        }
      }

      // 4. 모터(파란색)
      const motorMaterial = new THREE.MeshPhongMaterial({ color: 0x0066ff });
      const motor = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 10, 32), motorMaterial);
      motor.position.set(-40, 85, -40);
      motor.rotation.x = Math.PI / 2;
      scene.add(motor);

      // 렌더링 루프
      function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
      }
      animate();
    }
  }
}
</script>

<style scoped>
.scene-container {
  width: 100%;
  height: 80vh;
  background: #f0f0f0;
}
</style>

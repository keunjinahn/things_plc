<template>
    <div class="row layout-top-spacing">
        <div class="col-xl-4 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing map-h">
            <div style="display: flex; flex-wrap: wrap;">
                <div
                  v-for="cam in cameras"
                  :key="cam"
                  style="flex: 1; padding: 10px; max-width: 400px;"
                >
                  <h3>Camera {{ cam }}</h3>
                  <!-- 클릭 시 togglePlay 호출 -->
                  <div @click="togglePlay(cam)" style="cursor: pointer;">
                    <!-- 비디오 모드이면 video 태그, 아니면 스냅샷 이미지 -->
                    <video
                      v-if="playing[cam]"
                      controls
                      autoplay
                      style="width: 100%; border: 1px solid #ccc;"
                    >
                      <source :src="videoUrls[cam]" type="multipart/x-mixed-replace; boundary=ffserver" />
                      Your browser does not support the video tag.
                    </video>
                    <img
                      v-else
                      :src="snapshotUrls[cam]"
                      alt="Snapshot for camera"
                      style="width: 100%; border: 1px solid #ccc;"
                    />
                  </div>
                </div>
              </div>
        </div>
    </div>
 
</template>

<script>
    import '@/assets/sass/widgets/widgets.scss';
    export default {
        metaInfo: { title: 'Widgets' },
         components: {
        },
        data() {
            return {
                cameras: [1],
                snapshotUrls: {},
                videoUrls: {},    // 카메라별 비디오 스트림 URL
                playing: {},      // 카메라별 재생 여부 (false: 스냅샷, true: 비디오)                
                refreshInterval: null,                   
            };
        },
        computed: {
             
        },
        mounted() {
            this.refreshSnapshots();
            this.refreshInterval = setInterval(this.refreshSnapshots, 5000);   
        },
        methods: {
            async getSnapshotUrl(cam) {
                try {
                    // 요청 시 캐시 방지를 위해 현재 시간을 쿼리 스트링에 추가합니다.
                    let { data } = await this.$http.get(
                        `/snapshot/${cam}?t=${new Date().getTime()}`,
                        { responseType: 'blob' }
                    );
                    // Blob 데이터를 URL 객체로 변환하여 반환합니다.
                    return URL.createObjectURL(data);
                } catch (error) {
                    console.error(`Error fetching snapshot for camera ${cam}:`, error);
                    return '';
                }
            },
            async refreshSnapshots() {
                for (let cam of this.cameras) {
                    const url = await this.getSnapshotUrl(cam);
                    this.$set(this.snapshotUrls, cam, url);
                    //this.$set(this.videoUrls, cam, `/api/v1/video/${cam}`);
                }
            },
            togglePlay(cam) {
            // 현재 재생중이면 스냅샷 모드로 전환, 아니면 비디오 모드로 전환
                this.$set(this.playing, cam, !this.playing[cam]);
            }           
        },
        beforeDestroy() {
            // 컴포넌트 종료 시 주기적 갱신 해제
            clearInterval(this.refreshInterval);
        }
    };
</script>
<style lang="scss" scoped>
.test {
    height: 95%; /* 또는 100vh 등으로 조정 */
}
.map-h {
    height:600px;
}
.widget-content {
    padding: 0 20px 20px;

    .chart-title {
        font-size: 18px;
    }
}
</style>
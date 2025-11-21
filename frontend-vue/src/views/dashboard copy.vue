<template>
    <div class="row layout-top-spacing">
        <div class="col-xl-4 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing map-h">
            <vue-daum-map
                :appKey="kakaomap.appKey"
                :center.sync="kakaomap.center"
                :level.sync="kakaomap.level"
                :mapTypeId="kakaomap.mapTypeId"
                :libraries="kakaomap.libraries"
                :style="kakaomap.style"
                @load="loadedMap"
                @zoom_changed="zoomUpdate"
                @center_changed="centerChanged"
            />
        </div>

        <div class="col-xl-8 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing map-h">
            <div class="widget h-100">
                <div class="widget-content h-100">
                    <V3DItem class="h-100" :resultXYZ="lastResultXYZ" />
                </div>
            </div>
        </div>

        <div class="col-xl-12 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing">
            <div class="widget widget-table-two">
                <div class="widget-heading">
                    <h5>실시간 수집 데이터</h5>
                    <div class="button-group">
                        <button class="btn btn-primary" @click="generateAndSendData">위치 데이터 생성</button>
                        <button class="btn btn-primary" @click="getLastSendData">위치 데이터 조회</button>
                        <button class="btn btn-primary" @click="getWaveImage">파형조회</button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="table-responsive">
                        <table class="table table-hover data-table">
                            <thead>
                                <tr>
                                    <th>NO</th>
                                    <th>시간</th>
                                    <th>장비명</th>
                                    <th>위도</th>
                                    <th>경도</th>
                                    <th>수심</th>
                                    <th>온도</th>
                                    <th>상태</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="item in paginatedData" :key="item.deviceName" 
                                    :class="{ 'warning-row': item.status === '이상' }">
                                    <td>{{ deviceData.indexOf(item) + 1 }}</td>
                                    <td>{{ item.time }}</td>
                                    <td>{{ item.deviceName }}</td>
                                    <td>{{ item.latitude }}</td>
                                    <td>{{ item.longitude }}</td>
                                    <td>{{ item.depth }}M</td>
                                    <td>{{ item.temperature }}°C</td>
                                    <td :class="{ 'status-normal': item.status === '정상', 'status-abnormal': item.status === '이상' }">
                                        {{ item.status }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div class="pagination-controls">
                            <button @click="prevPage" :disabled="currentPage === 1">이전</button>
                            <span>페이지 {{ currentPage }} / {{ totalPages }}</span>
                            <button @click="nextPage" :disabled="currentPage === totalPages">다음</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
 
</template>

<script>
    import '@/assets/sass/widgets/widgets.scss';
    import VueDaumMap from 'vue-daum-map'
    import VItem from '@/components/VItem'
    import Vue from 'vue'
    import VueApexCharts from 'vue-apexcharts';
    import V3DItem from '@/components/V3DItem.vue';
    Vue.use(VueApexCharts);
    Vue.component('apexchart', VueApexCharts);
    const VItemComponent = Vue.extend(VItem)   
    export default {
        metaInfo: { title: '충남지역지능화센터 해양지능화 솔루션' },
         components: {
            VueDaumMap,V3DItem
        },
        data() {
            return {
                mapView: true,
                kakaomap: {
                    appKey: 'faea7c1211312bb306dc708fa0977848',
                    center: {lat: 33.9547, lng: 126.3250},  // 추자도 중심 좌표
                    level: 9,  // 줌 레벨 조정
                    mapTypeId: VueDaumMap.MapTypeId.NORMAL,
                    libraries: ['clusterer'],
                    map: null,
                    clusterer: null,
                    style: {
                        width: '100%',
                        height: '100%'
                    }
                },  
                // 미리 정의된 VItem 위치들
                vitemPositions: [
                    { latitude: 33.9547 + 0.135, longitude: 126.3250 + 0.225 },  // 북동쪽 20km
                    { latitude: 33.9547 - 0.090, longitude: 126.3250 + 0.180 },  // 남동쪽 15km
                    { latitude: 33.9547 + 0.225, longitude: 126.3250 - 0.180 },  // 북서쪽 25km
                    { latitude: 33.9547 - 0.180, longitude: 126.3250 - 0.135 },  // 남서쪽 22km
                    { latitude: 33.9547 + 0.360, longitude: 126.3250 + 0.045 },  // 북쪽 40km
                    { latitude: 33.9547 - 0.270, longitude: 126.3250 + 0.090 },  // 남쪽 30km
                    { latitude: 33.9547 + 0.045, longitude: 126.3250 + 0.315 },  // 동쪽 35km
                    { latitude: 33.9547 - 0.135, longitude: 126.3250 - 0.270 },  // 서쪽 32km
                    { latitude: 33.9547 + 0.180, longitude: 126.3250 + 0.135 },  // 북동쪽 28km
                    { latitude: 33.9547 - 0.225, longitude: 126.3250 - 0.090 }   // 남서쪽 26km
                ],
                activeVitemInstance: null,
                colors: [
                    '#4572A7', '#AA4643', '#89A54E', '#80699B', '#3D96AE',
                    '#DB843D', '#92A8CD', '#A47D7C', '#B5CA92'
                ],
                current: {
                    show: false,
                    vItemInfo: null,
                    selectedPath: 0,
                    listIndex:0,
                },   
                daily_sales_series: [
                    { name: 'Sales', data: [44, 55, 41, 67, 22, 43, 21] },
                    { name: 'Last Week', data: [13, 23, 20, 8, 13, 27, 33] }
                ],                          
                vitemInstances: [], // VItem 인스턴스 배열
                deviceData: [],  // 초기 빈 배열
                currentPage: 1,
                itemsPerPage: 5,
                updateInterval: null,
                lastResultXYZ: null,
                showWaveImage: false,
                waveImageUrl: null,
            };
        },
        computed: {
            daily_sales_options() {
                return {
                    chart: { toolbar: { show: false }, stacked: true, stackType: '100%' },
                    dataLabels: { enabled: false },
                    stroke: { show: true, width: 1 },
                    colors: ['#e2a03f', '#e0e6ed'],
                    responsive: [{ breakpoint: 480, options: { legend: { position: 'bottom', offsetX: -10, offsetY: 0 } } }],
                    xaxis: { labels: { show: false }, categories: ['Sun', 'Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat'] },
                    yaxis: { show: false },
                    fill: { opacity: 1 },
                    plotOptions: { bar: { horizontal: false, columnWidth: '25%' } },
                    legend: { show: false },
                    grid: {
                        show: false,
                        xaxis: { lines: { show: false } },
                        padding: { top: 10, right: -20, bottom: -20, left: -20 }
                    }
                };
            },
            totalPages() {
                return Math.ceil(this.deviceData.length / this.itemsPerPage);
            },
            paginatedData() {
                const start = (this.currentPage - 1) * this.itemsPerPage;
                const end = start + this.itemsPerPage;
                return this.deviceData.slice(start, end);
            }
        },
        mounted() {
            this.initDeviceData()
            this.init_map()
            // 3초마다 데이터 업데이트
            this.updateInterval = setInterval(() => {
                this.updateDeviceData()
             
            }, 3000)

            this.updateInterval_sensor = setInterval(() => {
                //this.generateAndSendData();
                this.getLastSendData();    
                this.getWaveImage();           
            }, 3000)
        },
        beforeDestroy() {
            if (this.vitemInstances) {
                this.vitemInstances.forEach(instance => {
                    instance.$destroy()
                })
            }
            if (this.updateInterval) {
                clearInterval(this.updateInterval)
            }
            if (this.updateInterval_sensor) {
                clearInterval(this.updateInterval_sensor)
            }
        },
        methods: {
            loadedMap (map) {
                map.setMinLevel(2)
                this.kakaomap.map = map
                this.init_map()
            },

            zoomUpdate() {
                //console.log(`ZOOM: ${this.kakaomap.level}`)
            },
            centerChanged() {
                const center = this.kakaomap.map.getCenter();
                console.log('현재 중심 좌표:', center.getLat(), center.getLng());
            },
            init_map(){
                let kakao = window.kakao
                
                // 미리 정의된 위치에 VItem 생성
                this.vitemPositions.forEach((position, index) => {
                    const newPosition = {
                        path: [{
                            latitude: position.latitude,
                            longitude: position.longitude
                        }]
                    }

                    // VItem 인스턴스 생성
                    const instance = new VItemComponent({
                        propsData: {
                            info: newPosition,
                            color: this.colors[index % this.colors.length],
                            kakao: kakao,
                            map: this.kakaomap.map,
                            root: this,
                            isBlinking: this.deviceData[index]?.status === '이상',
                            warningColor: '#ff0000'
                        }
                    })
                    
                    instance.$mount()
                    this.vitemInstances.push(instance)
                })
            },
            
            initDeviceData() {
                // 초기 데이터 설정
                this.deviceData = this.vitemPositions.map((pos, index) => ({
                    deviceName: `장비 ${index + 1}`,
                    time: this.getCurrentTime(),
                    latitude: pos.latitude.toFixed(4),
                    longitude: pos.longitude.toFixed(4),
                    depth: Math.floor(80 + Math.random() * 20),
                    temperature: (10 + Math.random() * 10).toFixed(1),
                    status: Math.random() > 0.2 ? '정상' : '이상'
                }))
            },
            updateDeviceData() {
                this.deviceData = this.deviceData.map((item) => {
                    const newStatus = Math.random() > 0.2 ? '정상' : '이상'
                    return {
                        ...item,
                        time: this.getCurrentTime(),
                        depth: Math.floor(80 + Math.random() * 20),
                        temperature: (10 + Math.random() * 10).toFixed(1),
                        status: newStatus
                    }
                })

                this.vitemInstances.forEach((instance, index) => {
                    if (instance) {
                        instance.$children[0].isBlinking = this.deviceData[index]?.status === '이상'
                        instance.$forceUpdate()
                    }
                })
            },
            getCurrentTime() {
                const now = new Date()
                const year = now.getFullYear()
                const month = String(now.getMonth() + 1).padStart(2, '0')
                const day = String(now.getDate()).padStart(2, '0')
                const hours = String(now.getHours()).padStart(2, '0')
                const minutes = String(now.getMinutes()).padStart(2, '0')
                const seconds = String(now.getSeconds()).padStart(2, '0')
                return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
            },
            prevPage() {
                if (this.currentPage > 1) {
                    this.currentPage--;
                }
            },
            nextPage() {
                if (this.currentPage < this.totalPages) {
                    this.currentPage++;
                }
            },
            generateRandomCoordinate() {
                return parseFloat((Math.random() * 10).toFixed(2));
            },

            generateXYZPoint() {
                return {
                    x: this.generateRandomCoordinate(),
                    y: this.generateRandomCoordinate(),
                    z: this.generateRandomCoordinate()
                };
            },

            async generateAndSendData() {
                // Generate 8 xyz points for axis_xyz
                const axis_xyz = Array.from({ length: 8 }, () => this.generateXYZPoint());
                
                // Generate result_xyz
                const result_xyz = this.generateXYZPoint();

                // Create the data object
                const sensorData = {
                    axis_xyz,
                    result_xyz
                };
                await this.$http.post('sensor-sea-data', sensorData).then(response => {
                    console.log('Data sent successfully:', response.data);
                })
                .catch(error => {
                    console.error('Error sending data:', error);
                });
            },
            async getLastSendData() {
                try {
                    const params = {
                        q: JSON.stringify({
                            filters: [],
                            order_by: [{
                                field: 'id',
                                direction: 'desc'
                            }]
                        }),
                        results_per_page: 1,
                        page: 1
                    };
                    
                    const response = await this.$http.get('sea-data', { params });
                    console.log('Last data fetched successfully:', response.data);
                    
                    if (response.data && response.data.objects && response.data.objects.length > 0) {
                        const lastData = JSON.parse(response.data.objects[0].sensor_data);
                        this.lastResultXYZ = lastData.result_xyz;
                        console.log('Parsed result_xyz:', this.lastResultXYZ);
                    } else {
                        console.log('No data available');
                        this.lastResultXYZ = { x: 0, y: 0, z: 0 };
                    }
                } catch (error) {
                    console.error('Error fetching last data:', error);
                    this.lastResultXYZ = { x: 0, y: 0, z: 0 };
                }
            },
            async getWaveImage() {
                try {
                    const response = await this.$http.get('get_wave_image', { responseType: 'blob' });
                    const imageUrl = URL.createObjectURL(response.data);
                    this.waveImageUrl = imageUrl;
                    this.showWaveImage = true;
                } catch (error) {
                    console.error('Error fetching wave image:', error);
                }
            }
        }
    };
</script>
<style lang="scss" scoped>
.test {
    height: 95%; /* 또는 100vh 등으로 조정 */
}
.map-h {
    height:800px;
}
.widget-content {
    padding: 0 20px 20px;

    .chart-title {
        font-size: 18px;
    }
}
.h-100 {
    height: 100%;
}

.widget-table-data {
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(8px);
    border-radius: 6px;
    margin-bottom: 20px;
}

.widget-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;

    h5 {
        margin: 0;
        flex: 1;
    }

    .button-group {
        display: flex;
        gap: 10px;  // 버튼 사이 간격
        margin-left: auto;  // 오른쪽 정렬
    }
}

.table-responsive {
    overflow-x: auto;
    min-height: 200px;
    max-height: 400px;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    color: white;
    font-size: 14px;
    
    th, td {
        padding: 12px;
        text-align: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    th {
        background-color: rgba(0, 0, 0, 0.3);
        font-weight: bold;
        position: sticky;
        top: 0;
        z-index: 1;
    }
    
    tbody tr {
        &:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
    }
}

.status-normal {
    color: #00ff00;
}

.status-abnormal {
    color: #ff0000;
}

/* 스크롤바 스타일 */
.table-responsive::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

.table-responsive::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
}

.table-responsive::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
    
    &:hover {
        background: rgba(255, 255, 255, 0.3);
    }
}

.warning-row {
    animation: warningBackground 1.5s infinite;
}

@keyframes warningBackground {
    0% {
        background-color: rgba(255, 0, 0, 0.1);
    }
    50% {
        background-color: rgba(255, 0, 0, 0.3);
    }
    100% {
        background-color: rgba(255, 0, 0, 0.1);
    }
}

.status-abnormal {
    color: #ff0000;
    font-weight: bold;
}

.pagination-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 15px;
    gap: 10px;
    
    button {
        padding: 5px 15px;
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        border-radius: 4px;
        cursor: pointer;
        
        &:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        &:hover:not(:disabled) {
            background-color: rgba(255, 255, 255, 0.2);
        }
    }
    
    span {
        color: white;
        font-size: 14px;
    }
}

.vitem-container {
    position: relative;
    width: 100%;
    height: 100%;
}

.btn-primary {
    background-color: #4361ee;
    border-color: #4361ee;
    padding: 8px 16px;
    border-radius: 6px;
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 0 #2c3ebd, 0 5px 10px rgba(67, 97, 238, 0.3);
    font-weight: bold;
    
    &:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            120deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
        );
        transition: all 0.6s ease;
    }

    &:hover {
        background-color: #3651d4;
        border-color: #3651d4;
        transform: translateY(-2px);
        box-shadow: 0 6px 0 #2c3ebd, 0 8px 15px rgba(67, 97, 238, 0.4);

        &:before {
            left: 100%;
        }
    }

    &:active {
        transform: translateY(4px);
        box-shadow: 0 0 0 #2c3ebd, 0 0 5px rgba(67, 97, 238, 0.3);
        background-color: #2c3ebd;
        border-color: #2c3ebd;
        transition: all 0.1s ease;
    }

    &:after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: transparent;
        border-radius: 6px;
        transition: all 0.2s ease;
    }

    &:active:after {
        background: rgba(255, 255, 255, 0.1);
    }
}

.wave-image-overlay {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    background: transparent;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.wave-image {
    width: 200%;
    max-height: 200px;
    object-fit: contain;
    opacity: 0.7;
    transform: scaleX(2);
    transform-origin: center center;
}
</style>
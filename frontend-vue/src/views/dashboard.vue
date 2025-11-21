<template>
    <div class="row layout-top-spacing">
        <!-- PLC 실시간 데이터 대시보드 헤더 -->
        <div class="col-xl-12 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing">
            <div class="widget widget-header">
                <div class="widget-heading">
                    <h3><i class="fas fa-tachometer-alt"></i> PLC 실시간 데이터 모니터링</h3>
                    <div class="status-indicator">
                        <span class="status-dot" :class="{ 'active': isConnected }"></span>
                        <span class="status-text">{{ isConnected ? '연결됨' : '연결 끊김' }}</span>
        </div>
                </div>
                <div class="widget-content">
                    <div class="stats-overview">
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-database"></i>
                            </div>
                            <div class="stat-info">
                                <div class="stat-value">{{ totalDataItems }}</div>
                                <div class="stat-label">총 데이터 항목</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-clock"></i>
                            </div>
                            <div class="stat-info">
                                <div class="stat-value">{{ lastUpdateTime }}</div>
                                <div class="stat-label">마지막 업데이트</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-sync-alt"></i>
                            </div>
                            <div class="stat-info">
                                <div class="stat-value">{{ refreshRate }}초</div>
                                <div class="stat-label">새로고침 주기</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-server"></i>
                            </div>
                            <div class="stat-info">
                                <div class="stat-value">{{ activeDevices }}</div>
                                <div class="stat-label">활성 디바이스</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- PLC 데이터 그리드 -->
        <div class="col-xl-12 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing">
            <div class="widget widget-table">
                <div class="widget-heading">
                    <h5><i class="fas fa-table"></i> PLC 실시간 데이터 테이블 (plc_real_time_data)</h5>
                    <div class="controls">
                        <div class="refresh-control">
                            <label class="switch">
                                <input type="checkbox" v-model="autoRefresh" @change="toggleAutoRefresh">
                                <span class="slider round"></span>
                            </label>
                            <span class="control-label">자동 새로고침</span>
                        </div>
                        <div class="filter-controls">
                            <select v-model="qualityFilter" class="form-control" @change="applyFilters">
                                <option value="">모든 품질</option>
                                <option value="good">Good</option>
                                <option value="bad">Bad</option>
                                <option value="uncertain">Uncertain</option>
                            </select>
                            <button class="btn btn-secondary" @click="refreshData">
                                <i class="fas fa-sync-alt"></i> 새로고침
                            </button>
                        </div>
                    </div>
                </div>
                <div class="widget-content">
                    <!-- 로딩 상태 표시 -->
                    <div v-if="isLoading" class="loading-state">
                        <div class="spinner-border text-primary" role="status">
                            <span class="sr-only">데이터 로딩 중...</span>
                        </div>
                        <p>PLC 데이터를 불러오는 중...</p>
                    </div>
                    
                    <!-- 연결 상태 표시 -->
                    <div v-else-if="!isConnected" class="connection-error">
                        <i class="fas fa-exclamation-triangle text-warning"></i>
                        <p>PLC 연결이 끊어졌습니다. 더미 데이터를 표시합니다.</p>
                    </div>
                    
                    <!-- PLC 실시간 데이터 테이블 -->
                    <div v-else class="table-responsive">
                        <table class="table table-bordered plc-real-time-table">
                            <tbody>
                                <!-- 첫 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in firstRowData" :key="`name-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 1}` }}
                                    </th>
                                </tr>
                                
                                <!-- 두 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in firstRowData" :key="`value-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 세 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in secondRowData" :key="`name2-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 11}` }}
                                    </th>
                                </tr>
                                
                                <!-- 네 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in secondRowData" :key="`value2-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 다섯 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in thirdRowData" :key="`name3-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 21}` }}
                                    </th>
                                </tr>
                                
                                <!-- 여섯 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in thirdRowData" :key="`value3-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 일곱 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in fourthRowData" :key="`name4-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 31}` }}
                                    </th>
                                </tr>
                                
                                <!-- 여덟 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in fourthRowData" :key="`value4-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 아홉 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in fifthRowData" :key="`name5-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 41}` }}
                                    </th>
                                </tr>
                                
                                <!-- 열 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in fifthRowData" :key="`value5-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 열한 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in sixthRowData" :key="`name6-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 51}` }}
                                    </th>
                                </tr>
                                
                                <!-- 열두 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in sixthRowData" :key="`value6-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 열세 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in seventhRowData" :key="`name7-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 61}` }}
                                    </th>
                                </tr>
                                
                                <!-- 열네 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in seventhRowData" :key="`value7-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 열다섯 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in eighthRowData" :key="`name8-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 71}` }}
                                    </th>
                                </tr>
                                
                                <!-- 열여섯 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in eighthRowData" :key="`value8-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 열일곱 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in ninthRowData" :key="`name9-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 81}` }}
                                    </th>
                                </tr>
                                
                                <!-- 열여덟 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in ninthRowData" :key="`value9-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 열아홉 번째 줄: 컬럼 이름 10개 -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in tenthRowData" :key="`name10-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 91}` }}
                                    </th>
                                </tr>
                                
                                <!-- 스무 번째 줄: 컬럼 값 10개 -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in tenthRowData" :key="`value10-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                </tr>
                                
                                <!-- 스물한 번째 줄: 컬럼 이름 4개 (마지막 줄) -->
                                <tr class="column-names-row">
                                    <th v-for="(item, index) in eleventhRowData" :key="`name11-${index}`" 
                                        class="column-name-header" :class="getColumnHeaderClass(item)">
                                        {{ item.item_name || `항목${index + 101}` }}
                                    </th>
                                    <!-- 빈 셀 6개 추가 (10개 컬럼 맞추기) -->
                                    <th v-for="i in 6" :key="`empty-${i}`" class="column-name-header empty-header">
                                        -
                                    </th>
                                </tr>
                                
                                <!-- 스물두 번째 줄: 컬럼 값 4개 (마지막 줄) -->
                                <tr class="column-values-row">
                                    <td v-for="(item, index) in eleventhRowData" :key="`value11-${index}`" 
                                        class="column-value-cell" :class="getValueClass(item)"
                                        :title="`10진수: ${item.value}`">
                                        {{ formatValue(item.value) }}
                                    </td>
                                    <!-- 빈 셀 6개 추가 (10개 컬럼 맞추기) -->
                                    <td v-for="i in 6" :key="`empty-value-${i}`" class="column-value-cell empty-cell">
                                        -
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <!-- 데이터가 없을 때 표시 -->
                        <div v-if="realTimeData.length === 0" class="no-data">
                            <i class="fas fa-database"></i>
                            <p>표시할 실시간 데이터가 없습니다.</p>
                            <p>데이터 개수: {{ realTimeData.length }}</p>
                        </div>
                        
                        <!-- 디버그 정보 (개발용) -->
                        <div v-if="realTimeData.length > 0" class="debug-info">
                            <details>
                                <summary>디버그 정보 ({{ realTimeData.length }}개 항목)</summary>
                                <div class="debug-content">
                                    <p><strong>실시간 데이터:</strong> {{ realTimeData.length }}개</p>
                                    <p><strong>품질 필터:</strong> {{ qualityFilter || '없음' }}</p>
                                    <p><strong>연결 상태:</strong> {{ isConnected ? '연결됨' : '연결 끊김' }}</p>
                                    <p><strong>로딩 상태:</strong> {{ isLoading ? '로딩 중' : '완료' }}</p>
                                    <div v-if="realTimeData.length > 0" class="sample-data">
                                        <p><strong>샘플 데이터 (첫 5개):</strong></p>
                                        <pre>{{ JSON.stringify(realTimeData.slice(0, 5), null, 2) }}</pre>
                                    </div>
                                </div>
                            </details>
                    </div>
                </div>
            </div>
        </div>
    </div>
 
        <!-- 데이터 품질 분포 -->
        <div class="col-xl-6 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing">
            <div class="widget widget-chart">
                <div class="widget-heading">
                    <h5><i class="fas fa-chart-pie"></i> 데이터 품질 분포</h5>
                </div>
                <div class="widget-content">
                    <div class="quality-distribution">
                        <div class="quality-item">
                            <div class="quality-color good"></div>
                            <span class="quality-label">Good</span>
                            <span class="quality-count">{{ qualityCounts.good }}</span>
                        </div>
                        <div class="quality-item">
                            <div class="quality-color bad"></div>
                            <span class="quality-label">Bad</span>
                            <span class="quality-count">{{ qualityCounts.bad }}</span>
                        </div>
                        <div class="quality-item">
                            <div class="quality-color uncertain"></div>
                            <span class="quality-label">Uncertain</span>
                            <span class="quality-count">{{ qualityCounts.uncertain }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 데이터 타입 분포 -->
        <div class="col-xl-6 col-lg-12 col-md-12 col-sm-12 col-12 layout-spacing">
            <div class="widget widget-chart">
                <div class="widget-heading">
                    <h5><i class="fas fa-chart-bar"></i> 데이터 타입 분포</h5>
                </div>
                <div class="widget-content">
                    <div class="type-distribution">
                        <div v-for="(count, type) in typeCounts" :key="type" class="type-item">
                            <div class="type-color" :class="getTypeClass(type)"></div>
                            <span class="type-label">{{ getTypeLabel(type) }}</span>
                            <span class="type-count">{{ count }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import '@/assets/sass/widgets/widgets.scss';

    export default {
    metaInfo: { 
        title: 'PLC 실시간 데이터 모니터링 - Things PLC' 
        },
        data() {
            return {
            // PLC 실시간 데이터
            realTimeData: [],
            
            // 필터링
            qualityFilter: '',
            
            // 자동 새로고침
            autoRefresh: true,
            refreshInterval: null,
            refreshRate: 1,
            
            // 연결 상태
            isConnected: true,
            lastUpdateTime: '--',
            
            // 품질 카운트
            qualityCounts: {
                good: 0,
                bad: 0,
                uncertain: 0
            },
            
            // 타입 카운트
            typeCounts: {},
            
            // 로딩 상태
            isLoading: false
            };
        },
        computed: {
        totalDataItems() {
            return this.realTimeData.length;
        },
        activeDevices() {
            const devices = new Set(this.realTimeData.map(item => item.plc_device_id).filter(Boolean));
            return devices.size;
        },
        // 첫 번째 줄과 두 번째 줄용 데이터 (20개씩)
        firstRowData() {
            return this.realTimeData.slice(0, 10);
        },
        // 세 번째 줄과 네 번째 줄용 데이터 (20개씩)
        secondRowData() {
            return this.realTimeData.slice(10, 20);
        },
        // 다섯 번째 줄과 여섯 번째 줄용 데이터 (20개씩)
        thirdRowData() {
            return this.realTimeData.slice(20, 30);
        },
        // 일곱 번째 줄과 여덟 번째 줄용 데이터 (20개씩)
        fourthRowData() {
            return this.realTimeData.slice(30, 40);
        },
        // 아홉 번째 줄과 열 번째 줄용 데이터 (20개씩)
        fifthRowData() {
            return this.realTimeData.slice(40, 50);
        },
        // 열한 번째 줄과 열두 번째 줄용 데이터 (20개씩)
        sixthRowData() {
            return this.realTimeData.slice(50, 60);
        },
        // 열세 번째 줄과 열네 번째 줄용 데이터 (20개씩)
        seventhRowData() {
            return this.realTimeData.slice(60, 70);
        },
        // 열다섯 번째 줄과 열여덟 번째 줄용 데이터 (20개씩)
        eighthRowData() {
            return this.realTimeData.slice(70, 80);
        },
        // 열일곱 번째 줄과 열여덟 번째 줄용 데이터 (20개씩)
        ninthRowData() {
            return this.realTimeData.slice(80, 90);
        },
        // 열아홉 번째 줄과 스무 번째 줄용 데이터 (20개씩)
        tenthRowData() {
            return this.realTimeData.slice(90, 100);
        },
        // 스물한 번째 줄과 스물두 번째 줄용 데이터 (4개씩)
        eleventhRowData() {
            return this.realTimeData.slice(100, 104);
            }
        },
        mounted() {
        this.initializeDashboard();
        this.startAutoRefresh();
        },
        beforeDestroy() {
        this.stopAutoRefresh();
    },
    methods: {
        async initializeDashboard() {
            await this.fetchPLCRealTimeData();
            this.updateStatistics();
            this.updateLastUpdateTime();
        },

        async fetchPLCRealTimeData() {
            try {
                this.isLoading = true;
                console.log('PLC 실시간 데이터 조회 시작...');
                
                // plc_real_time_data 테이블에서 데이터 조회
                const response = await this.$http.get('/plc/real-time-data');
                console.log('API 응답:', response);
                
                if (response.data.success) {
                    console.log('PLC 실시간 데이터 조회 성공:', response.data.data);
                    
                    // 데이터 업데이트
                    this.updateRealTimeData(response.data.data);
                    
                    // 필터링 적용
                    if (this.qualityFilter) {
                        this.applyFilters();
                    }
                    
                    this.isConnected = true;
                } else {
                    console.error('PLC 실시간 데이터 조회 실패:', response.data.message);
                    this.isConnected = false;
                    // 실패 시 더미 데이터 생성
                    this.generateDummyRealTimeData();
                }
            } catch (error) {
                console.error('PLC 실시간 데이터 조회 오류:', error);
                this.isConnected = false;
                // 에러 시 더미 데이터 생성
                this.generateDummyRealTimeData();
            } finally {
                this.isLoading = false;
            }
        },
        
        // 실시간 데이터 업데이트
        updateRealTimeData(newData) {
            this.realTimeData = newData;
        },

        generateDummyRealTimeData() {
            const dummyData = [];
            const itemTypes = ['M', 'D', 'Y', 'X'];
            const qualities = ['good', 'bad', 'uncertain'];
            
            // 104개의 더미 데이터 생성 (11줄 x 10개 컬럼, 마지막 줄은 4개)
            for (let i = 1; i <= 104; i++) {
                const itemType = itemTypes[Math.floor(Math.random() * itemTypes.length)];
                const quality = qualities[Math.floor(Math.random() * qualities.length)];
                
                // D4010 항목은 특별하게 처리
                let itemName, description;
                if (i === 10) { // 10번째 항목을 D4010으로 설정
                    itemName = 'D4010';
                    description = 'D4010 특별 데이터 항목 (중요)';
                } else {
                    itemName = `${itemType}${String(i).padStart(3, '0')}`;
                    description = `${itemType} 타입 데이터 항목 ${i}`;
                }
                
                // 16진수 표시에 적합한 값 생성 (0-65535 범위)
                const value = Math.floor(Math.random() * 65536);
                
                dummyData.push({
                    id: i,
                    data_item_id: i,
                    plc_device_id: Math.floor(i / 10) + 1,
                    item_name: itemName,
                    item_type: itemType,
                    description: description,
                    value: value,
                    quality: quality,
                    timestamp: new Date().toISOString()
                });
            }
            
            this.realTimeData = dummyData;
            this.applyFilters();
        },

        applyFilters() {
            console.log('필터 적용 시작. 원본 데이터:', this.realTimeData);
            
            if (!this.qualityFilter) {
                // 필터가 없으면 원본 데이터를 그대로 사용
                this.updateStatistics();
            } else {
                // 품질 필터 적용
                const filteredData = this.realTimeData.filter(item => item.quality === this.qualityFilter);
                console.log('필터된 데이터:', filteredData);
                this.updateStatistics();
            }
        },

        updateStatistics() {
            // 품질별 카운트
            this.qualityCounts = {
                good: this.realTimeData.filter(item => item.quality === 'good').length,
                bad: this.realTimeData.filter(item => item.quality === 'bad').length,
                uncertain: this.realTimeData.filter(item => item.quality === 'uncertain').length
            };
            
            // 타입별 카운트
            this.typeCounts = this.realTimeData.reduce((acc, item) => {
                acc[item.item_type] = (acc[item.item_type] || 0) + 1;
                return acc;
            }, {});
        },

        updateLastUpdateTime() {
            const now = new Date();
            this.lastUpdateTime = now.toLocaleTimeString('ko-KR');
        },

        startAutoRefresh() {
            if (this.autoRefresh) {
                this.refreshInterval = setInterval(() => {
                    this.refreshData();
                }, this.refreshRate * 1000);
            }
        },

        stopAutoRefresh() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        },

        toggleAutoRefresh() {
            if (this.autoRefresh) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        },

        async refreshData() {
            // 자동 새로고침 시에는 로딩 상태를 표시하지 않음
            const wasAutoRefresh = this.autoRefresh;
            if (!wasAutoRefresh) {
                this.isLoading = true;
            }
            
            try {
                // 자동 새로고침 시에는 수동 DOM 업데이트만 수행
                if (wasAutoRefresh) {
                    await this.updateDataOnly();
                } else {
                    await this.fetchPLCRealTimeData();
                }
                this.updateLastUpdateTime();
            } finally {
                if (!wasAutoRefresh) {
                    this.isLoading = false;
                }
            }
        },
        
        // 데이터만 업데이트 (DOM 재렌더링 없음)
        async updateDataOnly() {
            try {
                const response = await this.$http.get('/plc/real-time-data');
                if (response.data.success) {
                    // 기존 데이터 구조 유지하면서 값만 업데이트
                    const newData = response.data.data;
                    this.updateRealTimeDataSilently(newData);
                }
            } catch (error) {
                console.error('데이터 업데이트 오류:', error);
            }
        },
        
        // 조용한 데이터 업데이트 (Vue 반응성 완전 우회)
        updateRealTimeDataSilently(newData) {
            newData.forEach(newItem => {
                const existingItem = this.realTimeData.find(item => item.id === newItem.id);
                if (existingItem) {
                    // 기존 객체의 값만 업데이트
                    existingItem.value = newItem.value;
                    existingItem.quality = newItem.quality;
                    existingItem.timestamp = newItem.timestamp;
                }
            });
            
            // 통계 업데이트
            this.updateStatistics();
        },

        getValueClass(item) {
            if (!item || !item.quality) return '';
            
            // D4010 항목은 특별한 색상으로 표시
            if (item.item_name === 'D4010') {
                return 'value-d4010';
            }
            
            switch (item.quality.toLowerCase()) {
                case 'good':
                    return 'value-good';
                case 'bad':
                    return 'value-bad';
                case 'uncertain':
                    return 'value-uncertain';
                default:
                    return '';
            }
        },

        // D4010 컬럼 헤더용 클래스
        getColumnHeaderClass(item) {
            if (!item) return '';
            
            // D4010 항목은 특별한 색상으로 표시
            if (item.item_name === 'D4010') {
                return 'column-header-d4010';
            }
            
            return '';
        },

        formatValue(value) {
            if (value === null || value === undefined) return '--';
            
            try {
                // 숫자로 변환
                let numValue;
                if (typeof value === 'number') {
                    numValue = value;
                } else if (typeof value === 'string') {
                    numValue = parseFloat(value);
                    } else {
                    numValue = Number(value);
                }
                
                // NaN 체크
                if (isNaN(numValue)) {
                    return '--';
                }
                
                // 16진수로 변환 (대문자)
                const hexValue = Math.round(numValue).toString(16).toUpperCase();
                
                // 4자리로 패딩 (예: 000A, 00FF, 01A3)
                return `0x${hexValue.padStart(4, '0')}`;
                
                } catch (error) {
                console.error('값 변환 오류:', error);
                return '--';
            }
        },

        getTypeClass(type) {
            if (!type) return '';
            
            switch (type.toUpperCase()) {
                case 'M':
                    return 'type-m';
                case 'D':
                    return 'type-d';
                case 'Y':
                    return 'type-y';
                case 'X':
                    return 'type-x';
                default:
                    return 'type-default';
            }
        },

        getTypeLabel(type) {
            if (!type) return 'Unknown';
            
            switch (type.toUpperCase()) {
                case 'M':
                    return '내부 릴레이';
                case 'D':
                    return '데이터 레지스터';
                case 'Y':
                    return '출력';
                case 'X':
                    return '입력';
                default:
                    return type;
                }
            }
        }
    };
</script>

<style lang="scss" scoped>
.layout-top-spacing {
    padding-top: 20px;
}

.widget {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.widget-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    
    .widget-heading {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        
        h3 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            
            i {
                margin-right: 10px;
                color: #ffd700;
            }
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .status-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #ccc;
                transition: all 0.3s ease;
                
                &.active {
                    background: #4caf50;
                    box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
                }
            }
            
            .status-text {
                font-size: 14px;
                font-weight: 500;
            }
        }
    }
    
.widget-content {
    padding: 0 20px 20px;
    }
}

.stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    
    .stat-card {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 20px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        backdrop-filter: blur(10px);
        
        .stat-icon {
            width: 50px;
            height: 50px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: #ffd700;
        }
        
        .stat-info {
            .stat-value {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 4px;
            }
            
            .stat-label {
                font-size: 14px;
                opacity: 0.8;
            }
        }
    }
}

.widget-table {
.widget-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
        border-bottom: 1px solid #e9ecef;

    h5 {
        margin: 0;
            font-size: 18px;
            font-weight: 600;
            color: #333;
            
            i {
                margin-right: 8px;
                color: #667eea;
            }
        }
        
        .controls {
        display: flex;
            align-items: center;
            gap: 20px;
            
            .refresh-control {
                display: flex;
                align-items: center;
                gap: 10px;
                
                .switch {
                    position: relative;
                    display: inline-block;
                    width: 50px;
                    height: 24px;
                    
                    input {
                        opacity: 0;
                        width: 0;
                        height: 0;
                        
                        &:checked + .slider {
                            background-color: #667eea;
                        }
                        
                        &:checked + .slider:before {
                            transform: translateX(26px);
                        }
                    }
                    
                    .slider {
                        position: absolute;
                        cursor: pointer;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-color: #ccc;
                        transition: 0.4s;
                        border-radius: 24px;
                        
                        &:before {
                            position: absolute;
                            content: "";
                            height: 18px;
                            width: 18px;
                            left: 3px;
                            bottom: 3px;
                            background-color: white;
                            transition: 0.4s;
                            border-radius: 50%;
                        }
                    }
                }
                
                .control-label {
                    font-size: 14px;
                    color: #666;
                }
            }
            
            .filter-controls {
                display: flex;
                align-items: center;
                gap: 10px;
                
                .form-control {
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                }
                
                .btn-secondary {
                    background: #6c757d;
                    border: none;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    
                    &:hover {
                        background: #5a6268;
                    }
                    
                    i {
                        margin-right: 5px;
                    }
                }
            }
        }
    }
    
    .widget-content {
        padding: 20px;
    }
}

.table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.plc-data-grid {
    width: 100%;
    margin: 0;
    
    th, td {
        padding: 12px 16px;
        text-align: center;
        border: 1px solid #e9ecef;
        vertical-align: middle;
        white-space: nowrap;
    }
    
    th {
        background: #f8f9fa;
        font-weight: 600;
        color: #495057;
        position: sticky;
        top: 0;
        z-index: 10;
        min-width: 120px;
        
        &.grid-header {
            background: #e3f2fd;
            border: 2px solid #1976d2;
            
            .item-name {
                font-weight: 700;
                font-size: 14px;
                color: #1976d2;
            }
            
            .item-type {
                .type-badge {
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 600;
                    text-transform: uppercase;
                    
                    &.type-m {
                        background: #1976d2;
                        color: white;
                    }
                    
                    &.type-d {
                        background: #7b1fa2;
                        color: white;
                    }
                    
                    &.type-y {
                        background: #388e3c;
                        color: white;
                    }
                    
                    &.type-x {
                        background: #f57c00;
                        color: white;
                    }
                    
                    &.type-c {
                        background: #9c27b0;
                        color: white;
                    }
                    
                    &.type-default {
                        background: #f5f5f5;
                        color: #616161;
                    }
                }
            }
            
            .item-address {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                color: #666;
                background: #f8f9fa;
                padding: 2px 4px;
    border-radius: 3px;
            }
            
            .item-unit {
                font-size: 11px;
                color: #666;
                font-weight: 500;
            }
        }
    }
    
    tbody {
        .data-row {
            transition: none;
    
    &:hover {
                background: #e3f2fd;
            }
            
            td {
                transition: none;
                
                &.item-value {
                    transition: none;
                }
                
                &.item-name,
                &.item-type,
                &.item-address,
                &.item-unit {
                    transition: none;
                }
            }
        }
        
        .item-name {
            background: #f1f3f4;
            font-weight: 600;
            color: #495057;
            text-align: left;
            border-right: 2px solid #dee2e6;
            min-width: 150px;
        }
        
        .item-type {
            text-align: center;
            border: 1px solid #e9ecef;
            
            .type-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                display: inline-block;
                min-width: 60px;
                
                &.type-m {
                    background: #1976d2;
                    color: white;
                }
                
                &.type-d {
                    background: #7b1fa2;
                    color: white;
                }
                
                &.type-y {
                    background: #388e3c;
                    color: white;
                }
                
                &.type-x {
                    background: #f57c00;
                    color: white;
                }
            }
        }
        
        .item-address {
            text-align: center;
            border: 1px solid #e9ecef;
            
            code {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                color: #666;
                background: #f8f9fa;
                padding: 4px 6px;
                border-radius: 4px;
                border: 1px solid #dee2e6;
                display: inline-block;
                min-width: 80px;
                font-weight: 500;
            }
        }
        
        .item-unit {
            text-align: center;
            border: 1px solid #e9ecef;
            
            font-size: 11px;
            color: #666;
            font-weight: 500;
        }
        
        .item-value {
            text-align: center;
            border: 1px solid #e9ecef;
            
            .value-display {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: 600;
                min-width: 60px;
                text-align: center;
                transition: none;
                
                &.value-good {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                &.value-bad {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                
                &.value-uncertain {
                    background: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }
                
                &.value-null {
                    background: #f8f9fa;
                    color: #9e9e9e;
                    font-style: italic;
                    border: 1px solid #dee2e6;
                    font-weight: 400;
                }
            }
        }
    }
}

.loading-state, .connection-error, .no-data {
    text-align: center;
    padding: 40px 20px;
    color: #666;
    
    .spinner-border {
        width: 3rem;
        height: 3rem;
        margin-bottom: 20px;
    }
    
    i {
        font-size: 48px;
        margin-bottom: 20px;
        display: block;
    }
    
    p {
        margin: 10px 0;
        font-size: 16px;
        
        &:first-of-type {
            font-size: 18px;
            font-weight: 600;
        }
    }
}

.connection-error {
    color: #856404;
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 8px;
    
    i {
        color: #f39c12;
    }
}

.no-data {
    color: #6c757d;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    
    i {
        color: #6c757d;
    }
}

.widget-chart {
    .widget-heading {
        padding: 20px;
        border-bottom: 1px solid #e9ecef;
        
        h5 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
            color: #333;
            
            i {
                margin-right: 8px;
                color: #667eea;
            }
        }
    }
    
    .widget-content {
        padding: 20px;
    }
}

.quality-distribution, .type-distribution {
    display: flex;
    flex-direction: column;
    gap: 16px;
    
    .quality-item, .type-item {
        display: flex;
    align-items: center;
        gap: 12px;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 6px;
        
        .quality-color, .type-color {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            
            &.good {
                background: #28a745;
            }
            
            &.bad {
                background: #dc3545;
            }
            
            &.uncertain {
                background: #ffc107;
            }
            
            &.type-m {
                background: #1976d2;
            }
            
            &.type-d {
                background: #7b1fa2;
            }
            
            &.type-y {
                background: #388e3c;
            }
            
            &.type-x {
                background: #f57c00;
            }
        }
        
        .quality-label, .type-label {
            flex: 1;
            font-weight: 500;
            color: #495057;
        }
        
        .quality-count, .type-count {
            font-weight: 700;
            color: #667eea;
            font-size: 18px;
        }
    }
}

.debug-info {
    margin-top: 20px;
    padding: 15px;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    
    summary {
        cursor: pointer;
        font-weight: 600;
        color: #495057;
        margin-bottom: 10px;
        
        &:hover {
            color: #007bff;
        }
    }
    
    .debug-content {
        p {
            margin: 5px 0;
        font-size: 14px;
        }
        
        .sample-data {
            margin-top: 15px;
            
            pre {
                background: #fff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
                overflow-x: auto;
                max-height: 200px;
                overflow-y: auto;
            }
        }
    }
}

// PLC 실시간 데이터 테이블 스타일
.plc-real-time-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    
    tbody {
        tr {
            &:nth-child(odd) {
                background-color: #f8f9fa;
            }
            
            &:nth-child(even) {
                background-color: #ffffff;
            }
        }
    }
    
    .column-names-row {
        th.column-name-header {
            background-color: #007bff;
    color: white;
            text-align: center;
            padding: 12px 6px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid #dee2e6;
            min-width: 90px;
            max-width: 120px;
            white-space: nowrap;
    overflow: hidden;
            text-overflow: ellipsis;
            
            &:hover {
                background-color: #0056b3;
                cursor: pointer;
            }
            
            /* D4010 컬럼 헤더 특별 스타일 */
            &.column-header-d4010 {
                background: linear-gradient(135deg, #ff6b35, #f7931e);
                color: white;
                border-color: #e55a2b;
    font-weight: bold;
                font-size: 12px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                position: relative;
    
                /* D4010 컬럼 헤더에 특별한 표시 추가 */
                &::before {
                    content: '⚡';
        position: absolute;
                    top: 2px;
                    left: 4px;
                    color: #ffff00;
                    font-size: 12px;
                    animation: pulse 2s infinite;
                }
                
                &::after {
                    content: 'D4010';
                    position: absolute;
                    bottom: 2px;
                    right: 4px;
                    font-size: 8px;
                    color: #ffff00;
                    font-weight: normal;
    }

    &:hover {
                    background: linear-gradient(135deg, #ff5722, #ff9800);
                    transform: scale(1.05);
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 8px rgba(255, 107, 53, 0.4);
                }
            }
        }
    }
    
    .column-values-row {
        td.column-value-cell {
            text-align: center;
            padding: 10px 6px;
            font-size: 13px;
            font-weight: 500;
            border: 1px solid #dee2e6;
            min-width: 90px;
            max-width: 120px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-family: 'Courier New', monospace; /* 16진수 값 정렬을 위한 모노스페이스 폰트 */
            
            /* 16진수 값 스타일 */
            &:not(.empty-cell) {
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            
            &.value-good {
                background-color: #d4edda;
                color: #155724;
                border-color: #c3e6cb;
            }
            
            &.value-bad {
                background-color: #f8d7da;
                color: #721c24;
                border-color: #f5c6cb;
            }
            
            &.value-uncertain {
                background-color: #fff3cd;
                color: #856404;
                border-color: #ffeaa7;
            }
            
            /* 빈 셀 스타일 */
            &.empty-cell {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
                font-style: italic;
                opacity: 0.6;
                font-family: inherit; /* 빈 셀은 기본 폰트 사용 */
            }
            
            &.value-d4010 {
                background: linear-gradient(135deg, #4caf50, #8bc34a);
                color: white;
                border-color: #45a049;
                font-weight: bold;
                position: relative;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                
                /* D4010 항목에 특별한 표시 추가 */
                &::before {
                    content: '★';
                    position: absolute;
                    top: 2px;
                    right: 4px;
                    color: #ff6b35;
                    font-size: 12px;
                    animation: rotate 3s linear infinite;
                }
                
                &::after {
                    content: '중요';
    position: absolute;
                    bottom: 2px;
                    left: 4px;
                    font-size: 8px;
                    color: #ff6b35;
                    font-weight: normal;
                }
                
                &:hover {
                    background: linear-gradient(135deg, #45a049, #7cb342);
                    transform: scale(1.05);
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
                }
            }
            
            &:hover {
                background-color: #e9ecef;
                cursor: pointer;
            }
        }
    }
}

// 반응형 디자인
@media (max-width: 768px) {
    .widget-heading {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
        
        .controls {
            width: 100%;
            justify-content: space-between;
        }
    }
    
    .stats-overview {
        grid-template-columns: 1fr;
    }
    
    .plc-real-time-table {
        .column-names-row {
            th.column-name-header {
                padding: 8px 3px;
                font-size: 9px;
                min-width: 70px;
                max-width: 90px;
            }
        }
        
        .column-values-row {
            td.column-value-cell {
                padding: 6px 3px;
                font-size: 10px;
                min-width: 70px;
                max-width: 90px;
            }
        }
    }
}
</style>
<template>
    <div class="plc-data">
        <!-- PLC 데이터 헤더 -->
        <div class="data-header">
            <div class="header-content">
                <h1 class="page-title">
                    <i class="las la-database"></i>
                    PLC 데이터 관리
                </h1>
                <p class="page-subtitle">PLC 데이터 수집, 저장 및 분석</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary">
                    <i class="las la-download"></i>
                    데이터 내보내기
                </button>
                <button class="btn btn-success">
                    <i class="las la-plus"></i>
                    새 데이터 항목
                </button>
            </div>
        </div>

        <!-- 데이터 통계 카드 -->
        <div class="data-stats">
            <div class="card">
                <div class="card-body">
                    <div class="stat-item">
                        <i class="las la-chart-bar"></i>
                        <div class="stat-content">
                            <h3>1,250</h3>
                            <p>총 데이터 레코드</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="stat-item">
                        <i class="las la-clock"></i>
                        <div class="stat-content">
                            <h3>1초</h3>
                            <p>수집 주기</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="stat-item">
                        <i class="las la-hdd"></i>
                        <div class="stat-content">
                            <h3>2.5MB</h3>
                            <p>저장 용량</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="stat-item">
                        <i class="las la-check-circle"></i>
                        <div class="stat-content">
                            <h3>98.5%</h3>
                            <p>데이터 품질</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 데이터 테이블 -->
        <div class="data-table-container">
            <div class="table-header">
                <h5>실시간 데이터 테이블</h5>
                <div class="table-controls">
                    <input type="text" class="form-control" placeholder="검색..." v-model="searchQuery">
                    <select class="form-select" v-model="selectedType">
                        <option value="">모든 타입</option>
                        <option value="D">D (데이터)</option>
                        <option value="M">M (메모리)</option>
                        <option value="X">X (입력)</option>
                        <option value="Y">Y (출력)</option>
                    </select>
                </div>
            </div>
            <div class="table-content">
                <div class="table-placeholder">
                    <i class="las la-table"></i>
                    <p>데이터 테이블</p>
                    <small>PLC 데이터가 여기에 표시됩니다</small>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'PLCData',
    data() {
        return {
            searchQuery: '',
            selectedType: '',
            dataStats: {
                totalRecords: 1250,
                collectionInterval: 1000,
                storageSize: '2.5MB',
                dataQuality: 98.5
            }
        };
    },
    mounted() {
        this.initializeData();
    },
    methods: {
        initializeData() {
            console.log('PLC 데이터 관리 초기화');
        },
        exportData() {
            console.log('데이터 내보내기');
        },
        addDataItem() {
            console.log('새 데이터 항목 추가');
        }
    }
};
</script>

<style scoped>
.plc-data {
    padding: 20px;
    background-color: #f8f9fa;
    min-height: 100vh;
}

/* 헤더 스타일 */
.data-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    border-radius: 10px;
    color: white;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.header-content h1 {
    margin: 0;
    font-size: 28px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
}

.header-content p {
    margin: 5px 0 0 0;
    opacity: 0.9;
    font-size: 14px;
}

.header-actions {
    display: flex;
    gap: 10px;
}

.header-actions .btn {
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 5px;
}

/* 통계 카드 */
.data-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.card {
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: transform 0.3s ease;
}

.card:hover {
    transform: translateY(-2px);
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 20px;
}

.stat-item i {
    font-size: 32px;
    color: #28a745;
}

.stat-content h3 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    color: #495057;
}

.stat-content p {
    margin: 5px 0 0 0;
    color: #6c757d;
    font-size: 14px;
}

/* 테이블 컨테이너 */
.data-table-container {
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
}

.table-header h5 {
    margin: 0;
    color: #495057;
}

.table-controls {
    display: flex;
    gap: 10px;
}

.table-controls .form-control,
.table-controls .form-select {
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 14px;
}

.table-content {
    padding: 40px;
    text-align: center;
}

.table-placeholder {
    color: #6c757d;
}

.table-placeholder i {
    font-size: 48px;
    margin-bottom: 15px;
    opacity: 0.5;
}

.table-placeholder p {
    margin: 10px 0;
    font-size: 18px;
    font-weight: 500;
}

.table-placeholder small {
    color: #adb5bd;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .data-header {
        flex-direction: column;
        gap: 20px;
        text-align: center;
    }
    
    .header-actions {
        flex-wrap: wrap;
        justify-content: center;
    }
    
    .data-stats {
        grid-template-columns: 1fr;
    }
    
    .table-header {
        flex-direction: column;
        gap: 15px;
    }
    
    .table-controls {
        width: 100%;
        flex-direction: column;
    }
}
</style>


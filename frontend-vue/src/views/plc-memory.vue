<template>
    <div class="layout-px-spacing">
        <portal to="breadcrumb">
            <ul class="navbar-nav flex-row">
                <li>
                    <div class="page-header">
                        <nav class="breadcrumb-one" aria-label="breadcrumb">
                            <ol class="breadcrumb">
                                <li class="breadcrumb-item"><a href="javascript:;">PLC</a></li>
                                <li class="breadcrumb-item active" aria-current="page"><span>PLC 메모리</span></li>
                            </ol>
                        </nav>
                    </div>
                </li>
            </ul>
        </portal>

        <div class="row layout-top-spacing">
            <div class="col-xl-12 col-lg-12 col-sm-12 layout-spacing">
                <div class="panel br-6 p-0">
                    <div class="custom-table">
                        <!-- 테이블 헤더 -->
                        <div class="table-header">
                            <div class="d-flex align-items-center">
                                <h5 class="mb-0">
                                    <i class="las la-memory"></i>
                                    PLC 메모리 항목 관리
                                </h5>
                            </div>
                            <div class="header-actions">
                                <div class="header-search">
                                    <b-input 
                                        v-model="table_option.search_text" 
                                        size="sm" 
                                        placeholder="검색..." 
                                        @input="on_search"
                                    />
                                    <div class="search-image">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-search">
                                            <circle cx="11" cy="11" r="8"></circle>
                                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                                        </svg>
                                    </div>
                                </div>
                                <button class="btn btn-primary btn-sm" @click="refreshData">
                                    <i class="las la-sync-alt"></i>
                                    새로고침
                                </button>
                            </div>
                        </div>

                        <!-- 로딩 상태 -->
                        <div v-if="isLoading" class="text-center p-5">
                            <div class="spinner-border text-primary" role="status">
                                <span class="sr-only">로딩 중...</span>
                            </div>
                            <p class="mt-2">데이터를 불러오는 중...</p>
                        </div>

                        <!-- 테이블 -->
                        <div v-else class="table-responsive">
                            <b-table 
                                ref="memory_table" 
                                responsive 
                                hover 
                                :items="filtered_items" 
                                :fields="columns" 
                                :per-page="table_option.page_size" 
                                :current-page="table_option.current_page"
                                :show-empty="true"
                                @filtered="on_filtered"
                                class="plc-memory-table"
                            >
                                <!-- 체크박스 컬럼 (is_active) -->
                                <template #cell(is_active)="row">
                                    <div class="form-check form-check-primary d-flex justify-content-center align-items-center">
                                        <input 
                                            type="checkbox" 
                                            class="form-check-input" 
                                            :checked="row.item.is_active"
                                            @change="toggleActive(row.item)"
                                            :disabled="isUpdating === row.item.id"
                                        />
                                        <span v-if="isUpdating === row.item.id" class="spinner-border spinner-border-sm text-primary ml-2"></span>
                                    </div>
                                </template>

                                <!-- 항목 타입 컬럼 -->
                                <template #cell(item_type)="row">
                                    <span class="badge badge-type" :class="getTypeBadgeClass(row.item.item_type)">
                                        {{ row.item.item_type }}
                                    </span>
                                </template>

                                <!-- 주소 컬럼 -->
                                <template #cell(address)="row">
                                    <code class="address-code">{{ row.item.address }}</code>
                                </template>

                                <!-- Modbus 주소 컬럼 -->
                                <template #cell(modbus_address)="row">
                                    <span v-if="row.item.modbus_address !== null && row.item.modbus_address !== undefined">
                                        {{ row.item.modbus_address }}
                                    </span>
                                    <span v-else class="text-muted">-</span>
                                </template>

                                <!-- 단위 컬럼 -->
                                <template #cell(unit)="row">
                                    <span v-if="row.item.unit">{{ row.item.unit }}</span>
                                    <span v-else class="text-muted">-</span>
                                </template>

                                <!-- 설명 컬럼 -->
                                <template #cell(description)="row">
                                    <span v-if="row.item.description" :title="row.item.description">
                                        {{ truncateText(row.item.description, 50) }}
                                    </span>
                                    <span v-else class="text-muted">-</span>
                                </template>

                                <!-- 디바이스 이름 컬럼 -->
                                <template #cell(device_name)="row">
                                    <span v-if="row.item.device_name">{{ row.item.device_name }}</span>
                                    <span v-else class="text-muted">-</span>
                                </template>
                            </b-table>
                        </div>

                        <!-- 테이블 푸터 (페이지네이션) -->
                        <div class="table-footer">
                            <div class="dataTables_info">
                                Showing {{ meta.total_items ? meta.start_index + 1 : 0 }} to {{ meta.end_index }} of {{ meta.total_items }}
                            </div>
                            <div class="paginating-container pagination-solid flex-column align-items-right">
                                <b-pagination 
                                    v-model="table_option.current_page" 
                                    :total-rows="table_option.total_rows" 
                                    :per-page="table_option.page_size" 
                                    prev-text="Prev" 
                                    next-text="Next" 
                                    first-text="First" 
                                    last-text="Last" 
                                    first-class="first" 
                                    prev-class="prev" 
                                    next-class="next" 
                                    last-class="last" 
                                    class="rounded"
                                >
                                    <template #first-text>
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                                        </svg>
                                    </template>
                                    <template #prev-text>
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                                        </svg>
                                    </template>
                                    <template #next-text>
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                                        </svg>
                                    </template>
                                    <template #last-text>
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                                        </svg>
                                    </template>
                                </b-pagination>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    metaInfo: { title: 'PLC 메모리 관리' },
    data() {
        return {
            items: [],
            filtered_items: [],
            columns: [
                { key: 'is_active', label: '조회 대상', sortable: true, thClass: 'text-center', tdClass: 'text-center' },
                { key: 'id', label: 'ID', sortable: true, thClass: 'text-center', tdClass: 'text-center' },
                { key: 'item_name', label: '항목 이름', sortable: true },
                { key: 'item_type', label: '타입', sortable: true, thClass: 'text-center', tdClass: 'text-center' },
                { key: 'address', label: '주소', sortable: true },
                { key: 'modbus_address', label: 'Modbus 주소', sortable: true, thClass: 'text-center', tdClass: 'text-center' },
                { key: 'modbus_function', label: 'Modbus 함수', sortable: true, thClass: 'text-center', tdClass: 'text-center' },
                { key: 'unit', label: '단위', sortable: true, thClass: 'text-center', tdClass: 'text-center' },
                { key: 'description', label: '설명', sortable: false },
                { key: 'device_name', label: '디바이스', sortable: true },
                { key: 'created_at', label: '생성일', sortable: true, formatter: (value) => value ? new Date(value).toLocaleDateString('ko-KR') : '-' }
            ],
            table_option: { 
                total_rows: 0, 
                current_page: 1, 
                page_size: 20, 
                search_text: '' 
            },
            meta: {},
            isLoading: false,
            isUpdating: null // 현재 업데이트 중인 항목 ID
        }
    },
    watch: {
        table_option: {
            handler: function () { 
                this.get_meta(); 
            },
            deep: true
        },
    },
    mounted() {
        this.fetchMemoryItems();
    },
    methods: {
        async fetchMemoryItems() {
            try {
                this.isLoading = true;
                const response = await this.$http.get('/plc/memory-items');
                
                if (response.data.success) {
                    this.items = response.data.data;
                    this.filtered_items = [...this.items];
                    this.table_option.total_rows = this.items.length;
                    this.get_meta();
                } else {
                    console.error('PLC 메모리 항목 조회 실패:', response.data.message);
                    this.$bvToast.toast('데이터 조회에 실패했습니다.', {
                        title: '오류',
                        variant: 'danger',
                        solid: true
                    });
                }
            } catch (error) {
                console.error('PLC 메모리 항목 조회 오류:', error);
                this.$bvToast.toast('데이터 조회 중 오류가 발생했습니다.', {
                    title: '오류',
                    variant: 'danger',
                    solid: true
                });
            } finally {
                this.isLoading = false;
            }
        },

        async toggleActive(item) {
            try {
                this.isUpdating = item.id;
                const response = await this.$http.patch(`/plc/memory-items/${item.id}/toggle-active`);
                
                if (response.data.success) {
                    // 로컬 데이터 업데이트
                    const index = this.items.findIndex(i => i.id === item.id);
                    if (index !== -1) {
                        this.items[index].is_active = response.data.data.is_active;
                        this.filtered_items = [...this.items];
                    }
                    
                    this.$bvToast.toast(
                        `항목이 ${response.data.data.is_active ? '활성화' : '비활성화'}되었습니다.`,
                        {
                            title: '성공',
                            variant: 'success',
                            solid: true
                        }
                    );
                } else {
                    this.$bvToast.toast('상태 업데이트에 실패했습니다.', {
                        title: '오류',
                        variant: 'danger',
                        solid: true
                    });
                    // 원래 상태로 복구
                    this.fetchMemoryItems();
                }
            } catch (error) {
                console.error('상태 업데이트 오류:', error);
                this.$bvToast.toast('상태 업데이트 중 오류가 발생했습니다.', {
                    title: '오류',
                    variant: 'danger',
                    solid: true
                });
                // 원래 상태로 복구
                this.fetchMemoryItems();
            } finally {
                this.isUpdating = null;
            }
        },

        refreshData() {
            this.fetchMemoryItems();
        },

        on_search() {
            this.table_option.current_page = 1;
            this.filter_items();
        },

        filter_items() {
            const searchText = this.table_option.search_text.toLowerCase();
            if (!searchText) {
                this.filtered_items = [...this.items];
            } else {
                this.filtered_items = this.items.filter(item => {
                    return (
                        (item.item_name && item.item_name.toLowerCase().includes(searchText)) ||
                        (item.address && item.address.toLowerCase().includes(searchText)) ||
                        (item.item_type && item.item_type.toLowerCase().includes(searchText)) ||
                        (item.description && item.description.toLowerCase().includes(searchText)) ||
                        (item.device_name && item.device_name.toLowerCase().includes(searchText)) ||
                        (item.modbus_address !== null && String(item.modbus_address).includes(searchText))
                    );
                });
            }
            this.table_option.total_rows = this.filtered_items.length;
            this.get_meta();
        },

        on_filtered(filtered_items) {
            this.filtered_items = filtered_items;
            this.get_meta();
        },

        get_meta() {
            const start_index = (this.table_option.current_page - 1) * this.table_option.page_size;
            const end_index = Math.min(start_index + this.table_option.page_size, this.table_option.total_rows);
            this.meta = {
                start_index: start_index,
                end_index: end_index,
                total_items: this.table_option.total_rows
            };
        },

        getTypeBadgeClass(type) {
            const typeMap = {
                'M': 'badge-primary',
                'D': 'badge-success',
                'X': 'badge-warning',
                'Y': 'badge-info',
                'T': 'badge-secondary',
                'C': 'badge-danger'
            };
            return typeMap[type] || 'badge-secondary';
        },

        truncateText(text, maxLength) {
            if (!text) return '';
            return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
        }
    }
};
</script>

<style scoped>
.plc-memory-table {
    margin-bottom: 0;
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
    display: flex;
    align-items: center;
    gap: 10px;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 15px;
}

.header-search {
    position: relative;
}

.header-search .form-control {
    padding-right: 40px;
    min-width: 250px;
}

.search-image {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: #6c757d;
    pointer-events: none;
}

.badge-type {
    font-size: 0.85em;
    padding: 0.35em 0.65em;
    font-weight: 600;
}

.address-code {
    background-color: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
    color: #495057;
}

.form-check {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.form-check-input {
    cursor: pointer;
    width: 18px;
    height: 18px;
}

.form-check-input:disabled {
    cursor: not-allowed;
    opacity: 0.6;
}

.form-check-label {
    margin: 0;
    cursor: pointer;
    font-size: 0.9em;
}

.table-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    background: #f8f9fa;
    border-top: 1px solid #e9ecef;
}

.dataTables_info {
    color: #6c757d;
    font-size: 0.9em;
}

.spinner-border-sm {
    width: 1rem;
    height: 1rem;
    border-width: 0.15em;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .table-header {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
    }

    .header-actions {
        width: 100%;
        flex-direction: column;
        align-items: stretch;
    }

    .header-search {
        width: 100%;
    }

    .header-search .form-control {
        min-width: 100%;
    }

    .table-footer {
        flex-direction: column;
        gap: 15px;
        align-items: center;
    }
}
</style>


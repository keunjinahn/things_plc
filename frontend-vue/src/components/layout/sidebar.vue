<template>
    <!--  BEGIN SIDEBAR  -->
    <div :class="['sidebar-wrapper', {'sidebar-collapsed': !isExpanded}]">
        <nav id="sidebar" class="sidebar-nav" :class="{'collapsed': !isExpanded}">
            <div class="shadow-bottom"></div>
            
            <!-- 사이드바 헤더 -->
            <div class="sidebar-header">
                <div class="sidebar-logo">
                    <i class="las la-microchip"></i>
                    <span v-if="isExpanded">용접철망 드지털트윈</span>
                </div>
            </div>

            <perfect-scrollbar class="list-unstyled menu-categories" tag="ul" :options="perfectScrollbarSettings">
                <li class="menu">
                    <router-link to="/dashboard" class="dropdown-toggle" @click="toggleMenu">
                        <div class="">
                            <i class="las la-home"></i>
                            <span>PLC 데이터 대시보드</span>
                        </div>
                    </router-link>
                </li>
                
                <!-- <li class="menu">
                    <router-link to="/dashboard2" class="dropdown-toggle" @click="toggleMenu">
                        <div class="">
                            <i class="las la-tachometer-alt"></i>
                            <span>PLC Dashboard</span>
                        </div>
                    </router-link>
                </li> -->
                
                <li class="menu">
                    <router-link to="/plc-monitor" class="dropdown-toggle" @click="toggleMenu">
                        <div class="">
                            <i class="las la-microchip"></i>
                            <span>용접철망 디지털트윈</span>
                        </div>
                    </router-link>
                </li>
                
                <li class="menu">
                    <router-link to="/plc-memory" class="dropdown-toggle" @click="toggleMenu">
                        <div class="">
                            <i class="las la-memory"></i>
                            <span>PLC 메모리</span>
                        </div>
                    </router-link>
                </li>

                <li class="menu">
                    <router-link to="/memory-query-manage" class="dropdown-toggle" @click="toggleMenu">
                        <div class="">
                            <i class="las la-database"></i>
                            <span>조회 메모리 관리</span>
                        </div>
                    </router-link>
                </li>

                <!-- <li class="menu">
                    <router-link to="/plc-data" class="dropdown-toggle" @click="toggleMenu">
                        <div class="">
                            <i class="las la-database"></i>
                            <span>PLC 데이터</span>
                        </div>
                    </router-link>
                </li> -->
                
            </perfect-scrollbar>
        </nav>
    </div>
    <!--  END SIDEBAR  -->
</template>
<script>
    export default {
        name: 'Sidebar',
        data() {
            return {
                isExpanded: true, // 사이드바를 기본적으로 보이게 설정
                perfectScrollbarSettings: {
                    handlers: ['click-rail', 'drag-thumb', 'keyboard', 'wheel', 'touch'],
                    wheelSpeed: 0.5,
                    wheelPropagation: false,
                    suppressScrollX: true
                }
            };
        },

        watch: {
            $route(to) {
                const selector = document.querySelector('#sidebar a[href="' + to.path + '"]');
                const ul = selector.closest('ul.collapse');
                if (!ul) {
                    const ele = document.querySelector('.dropdown-toggle.not-collapsed');
                    if (ele) {
                        ele.click();
                    }
                }
            }
        },

        mounted() {
            // 사이드바를 기본적으로 보이게 설정
            this.isExpanded = true;
            this.$nextTick(() => {
                const sidebarWrapper = document.querySelector('.sidebar-wrapper');
                if (sidebarWrapper) {
                    sidebarWrapper.classList.add('active');
                    sidebarWrapper.classList.remove('sidebar-collapsed');
                }
            });
        },

        methods: {
            toggleMenu() {
                this.isExpanded = !this.isExpanded;
                const sidebarWrapper = document.querySelector('.sidebar-wrapper');
                if (this.isExpanded) {
                    sidebarWrapper.classList.add('active');
                } else {
                    sidebarWrapper.classList.remove('active');
                }
            },
            toggleMobileMenu() {
                if (window.innerWidth < 991) {
                    this.$store.commit('toggleSideBar', !this.$store.state.is_show_sidebar);
                }
            }
        }
    };
</script>

<style scoped>
.sidebar-wrapper {
    width: 255px;
    position: fixed;
    z-index: 1030;
    transition: all .3s ease-in-out;
    height: 100vh;
    touch-action: none;
    user-select: none;
    -webkit-user-drag: none;
    -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
    transform: translateX(0);
    left: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.sidebar-wrapper.active {
    width: 255px;
    left: 0;
    transform: translateX(0);
}

/* 기본적으로 사이드바가 보이도록 설정 */
.sidebar-wrapper:not(.sidebar-collapsed) {
    width: 255px;
    left: 0;
    transform: translateX(0);
}

/* 사이드바 전체 스타일 개선 */
.sidebar-wrapper {
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.sidebar-wrapper::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%);
    z-index: -1;
}

.sidebar-collapsed {
    width: 0 !important;
    transform: translateX(-100%);
    left: -80px;
}

/* 접힌 상태에서의 헤더 스타일 */
.sidebar-collapsed .sidebar-header {
    padding: 15px 10px;
    text-align: center;
}

.sidebar-collapsed .sidebar-logo span {
    display: none;
}

.sidebar-collapsed .sidebar-logo i {
    font-size: 28px;
    margin-right: 0;
}

.sidebar-nav {
    background: transparent;
    width: 255px;
    height: 100%;
    transition: all .3s ease-in-out;
    overflow: hidden;
}

.sidebar-wrapper.active .sidebar-nav {
    width: 255px;
}

.sidebar-nav.collapsed {
    width: 80px;
}

/* 사이드바 헤더 스타일 */
.sidebar-header {
    padding: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 10px;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.sidebar-logo i {
    font-size: 24px;
    margin-right: 10px;
    color: #ffffff;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.sidebar-logo span {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.menu-categories {
    padding: 10px 0;
}

.menu {
    margin: 0;
}

.dropdown-toggle {
    display: flex;
    align-items: center;
    padding: 12px 20px;
    color: #ffffff;
    text-decoration: none;
    transition: all .3s ease;
    border-radius: 8px;
    margin: 4px 12px;
    font-weight: 500;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.dropdown-toggle:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.2);
    transform: translateX(4px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.dropdown-toggle i {
    font-size: 18px;
    margin-right: 12px;
    min-width: 20px;
    color: #ffffff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.dropdown-toggle span {
    font-size: 14px;
    font-weight: 500;
    color: #ffffff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.sidebar-collapsed .dropdown-toggle span {
    display: none;
}

/* 활성 메뉴 스타일 */
.dropdown-toggle.router-link-active {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.25);
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    border-left: 4px solid #ffffff;
    transform: translateX(4px);
}

/* 메뉴 항목 애니메이션 */
.menu {
    position: relative;
}

.menu::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(to bottom, #667eea, #764ba2);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.menu:hover::before {
    opacity: 1;
}

/* 스크롤바 스타일 */
.menu-categories::-webkit-scrollbar {
    width: 4px;
}

.menu-categories::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
}

.menu-categories::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
}

.menu-categories::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.5);
}
</style>

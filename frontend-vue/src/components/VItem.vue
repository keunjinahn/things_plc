<template>
   <div class="vitem-component" :class="{ 'warning': isWarning, 'normal': !isWarning }">
    <div class="vitem-image">
        <img :src="get_vitemImage()"/>
    </div>
    <div class="signal-dot" :class="{ 'warning': isWarning, 'normal': !isWarning }"></div>
   </div>
    
</template>


<script>

export default {
    components: { },
    props: {
        info: {
            type: Object,
            required: true
        },
        color: {
            type: String,
            required: true
        },
        size: {
            type: Number,
            default: 80
        },
        kakao: {
            type: Object,
            required: true
        },
        map: {
            type: Object,
            required: true
        },
        root: {
            type: Object,
            required: true
        },
        isBlinking: {
            type: Boolean,
            default: false
        },
        warningColor: {
            type: String,
            default: '#ff6b00'
        }
    },
    watch: {
    },
    methods: {
        set() {
            this.start_path = this.info.path[0]
            this.step.path = this.info.path[0]
            this.step.n = 0        
            //console.log(" this.start_path.latitude : " + this.start_path.latitude + ",longitude :"+ this.start_path.longitude)
            let center = new this.kakao.maps.LatLng(this.start_path.latitude, this.start_path.longitude)
            this.overlay.setPosition(center)
            this.map.setCenter(center)
            this.overlay.setMap(this.map)
        },
        get_vitemImage(){
            return require('@/assets/images/vitem.png')
        },
    },
    computed: {
        isWarning() {
            return this.isBlinking;
        }
    },
    mounted () {
        this.overlay = new this.kakao.maps.CustomOverlay({
            map: null,
            clickable: true,
            content: this.$el,
            yAnchor: 0,
            zIndex: 4
        })
        this.set()
        
        //this.getEvent(this.info.path)
    },
    beforeDestroy() {
        this.overlay.setMap(null)
        this.activeLoadInstance.forEach((v) => {
            v.$destroy()
        })
    },

    data () {
        return {
            activeLoadInstance: [],
            focused: false,
            overlay: null,
            infopanel: null,
            step: {
                n: -1,
                path: {},
                area: null,
                area_hist : []
            },
            route: null,
            estates: {},
        }
    }
}
</script>

<style lang="scss" scoped>
.buoy {
    width: 200px;
    height: auto;
    background: url('~@/assets/images/vitem.png') no-repeat center center;
    background-size: contain;
    display: inline-block;
    position: relative;
  }
  
  .buoy::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    height: 10px;
    background: radial-gradient(circle, rgba(0, 123, 255, 0.5) 0%, transparent 70%);
    z-index: -1;
  }
  .vitem-component {
    width: 30px;
    border: 1px solid #ccc;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 2px 2px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    position: relative;
    transition: all 0.3s ease;
    animation: normalBlink 2s infinite;
}
  .vitem-component:hover {
    background-color: #e2e8f0; 
    transform: scale(1.05); 
  }
  .vitem-image img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    transition: all 0.3s ease;
  }
    
.vitem-component.normal {
    border: 2px solid #007bff;
    background-color: rgba(0, 123, 255, 0.1);
    animation: normalBlink 2s infinite;
}

.vitem-component.warning {
    border: 2px solid #ff0000;
    background-color: rgba(255, 0, 0, 0.1);
    animation: warningBlink 1.5s infinite;
}

.vitem-component.normal .vitem-image img {
    filter: hue-rotate(180deg) brightness(1.1);
}

.vitem-component.warning .vitem-image img {
    filter: hue-rotate(0deg) brightness(1.2);
}

.pulse-effect {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: rgba(0, 123, 255, 0.3);
    animation: pulse 2s infinite;
}

.vitem-component.warning .pulse-effect {
    background: rgba(255, 107, 0, 0.4);
    animation: warningPulse 1.5s infinite;
}

@keyframes warningPulse {
    0% {
        box-shadow: 0 0 0 0 rgba(255, 107, 0, 0.4);
        transform: scale(1);
    }
    50% {
        box-shadow: 0 0 0 10px rgba(255, 107, 0, 0);
        transform: scale(1.2);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(255, 107, 0, 0);
        transform: scale(1);
    }
}

@keyframes pulse {
    0% {
        transform: translate(-50%, -50%) scale(1);
        opacity: 0.8;
    }
    50% {
        transform: translate(-50%, -50%) scale(2);
        opacity: 0.4;
    }
    100% {
        transform: translate(-50%, -50%) scale(1);
        opacity: 0.8;
    }
}

.signal-dot {
    position: absolute;
    top: -5px;
    right: -5px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: normalBlink 2s infinite;
}

.signal-dot.normal {
    background-color: #007bff;
    box-shadow: 0 0 5px #007bff;
}

.signal-dot.warning {
    background-color: #ff0000;
    box-shadow: 0 0 5px #ff0000;
    animation: warningBlink 1.5s infinite;
}

@keyframes normalBlink {
    0% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 5px #007bff;
    }
    50% {
        opacity: 0.7;
        transform: scale(1.05);
        box-shadow: 0 0 10px #007bff;
    }
    100% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 5px #007bff;
    }
}

@keyframes warningBlink {
    0% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 5px #ff0000;
    }
    50% {
        opacity: 0.7;
        transform: scale(1.1);
        box-shadow: 0 0 15px #ff0000;
    }
    100% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 5px #ff0000;
    }
}
</style>

import _ from 'lodash'
import Vue from 'vue'
import moment from 'moment'
import c from './statusCode'
import setting from './setting.json'


export default new Vue({
  methods: {
    timeout(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },
    async loginFromProp(userid) {

      let params = { userid }
      let userResp = await this.$http.post('check_user', params)

      if (!userResp.data.result) {
        throw Error('Not Matched')
      }
      this.$http.defaults.headers.common['token'] = 'envadmin'
      let { data } = await this.$http.get('setting')
      for (let key in data.problem) {
        if (!data.problem[key].method) continue;
        let mt = data.problem[key].method
        data.problem[key].values = []
        if (mt & 1) data.problem[key].values.push(1)
        if (mt & 2) data.problem[key].values.push(2)
        if (mt & 4) data.problem[key].values.push(4)
      }
      this.settings = data
      sessionStorage.setItem('sessionkey', this.sessionkey)
      sessionStorage.setItem('sessionToken', 'envadmin')
      sessionStorage.setItem('settings', JSON.stringify(data))
      return this.authentication = true
    },
    async login(data) {
      sessionStorage.setItem('sessionkey', this.sessionkey)
      this.$http.defaults.headers.common['token'] = data.user.token
      sessionStorage.setItem('user', JSON.stringify(data.user))
      sessionStorage.setItem('sessionToken', data.user.token)
      this.sessionStart = Date.now() + 32400000
      this.user = data.user
      return this.authentication = true
    },
    async logout() {
      try {
        await this.$http.post('logout')
      } catch (error) {
        console.error('로그아웃 API 호출 실패:', error)
        // API 호출 실패해도 로컬 세션은 정리
      }
      // 세션 정보 정리
      sessionStorage.removeItem('user')
      sessionStorage.removeItem('sessionToken')
      sessionStorage.removeItem('sessionkey')
      sessionStorage.removeItem('settings')
      delete this.$http.defaults.headers.common['token']
      this.authentication = false
      this.user = null
      this.authorized = false
    },
    parseStatusCode(code) {
      let codes = []
      if (code & c.ERROR_311_IN_ERROR) codes.push('311')
      if (code & c.ERROR_312_CAM_ERROR) codes.push('312')
      if (code & c.ERROR_313_QR_ERROR) codes.push('313')
      if (code & c.ERROR_314_MEASURE_DATA_ERROR) codes.push('314')
      if (code & c.ERROR_315_DISK_ERROR) codes.push('315')
      if (code & c.ERROR_316_MEASURE_NA_ERROR) codes.push('316')
      if (code & c.ERROR_317_DISCONNECT_ERROR) codes.push('317')
      return codes
    },
    getProblemFromCode(code, fullText) {
      if (!code) return '정상'
      console.log(code)
      //code = parseInt(code, 10)

      let pb = _.find(this.pb, { 'code': String(code) })
      if (pb) return pb[fullText ? 'text' : 'short']
      return '-'
    },
    isAdmin() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined
        && user.user_role == 1)
        return true
      return false
    },
    getUserId() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined)
        return user.user_id
      return null
    },
    getUserName() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined)
        return user.user_name
      return null
    },
    getUserIndex() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined)
        return user.id
      return null
    },
    getUserInfo() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined)
        return user
      return null
    },
    getUserType() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined)
        return user.user_type
      return null
    },
    getLastLogonTime() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined)
        return user.last_logon_time
      return null
    },
    getUserArea() {
      let user = JSON.parse(sessionStorage.getItem('user'))
      if (user != undefined)
        return user.area_code
      return null
    },
    hasPermission(allows) {
      if (!allows) return true
      return allows.includes(this.user.user_type)
    },
    getSessionDuration() {
      if (!this.sessionStart) return '00:00'
      return moment(Date.now() - this.sessionStart).format('HH:mm:ss')
      // 이거 무슨 문제가 있어서 바꾸신건가요? UTC계산이 잘못되서 출력되서 돌려놨습니다.
      // 그리고 매초마다 문자열을 날짜로 바꾸는건 문제가 있어 보입니다. 시간이 9시간 더해지거나 빠져서 보인다면 밑에 created에서 변경해 주세요.
      // return moment(Date.now()-moment(this.$session.getLastLogonTime())).format('HH:mm:ss')
    },
    getWebURL() {
      return (process.env.NODE_ENV === 'development') ? 'http://localhost:8080' : 'http://139.150.69.115'
      //return 'http://localhost:8080'
      // return 'http://118.128.43.7:30443'
      // return 'https://kodis.or.kr:50443'
    },
    async setToken (user) {
      this.$http.defaults.headers.common['token'] = user.token
      sessionStorage.setItem('user', JSON.stringify(user))
      this.authorized = true
      this.user = user
    },
    unsetToken () {
        delete this.$http.defaults.headers.common['token']
        sessionStorage.removeItem('user')
        this.authorized = false
        this.user = null
    },    
  },
  created() {
    let sessionkey = sessionStorage.getItem('sessionkey')
    let sessionToken = sessionStorage.getItem('sessionToken')
    if (sessionkey === this.sessionkey && sessionToken) {
      this.authentication = true
      this.settings = setting // JSON.parse(sessionStorage.getItem('settings'))
      try {
        let user = JSON.parse(sessionStorage.getItem('user'))
        this.sessionStart = moment(user.last_logon_time).valueOf() + 32400000
        if (!this.sessionStart) this.sessionStart = Date.now()
        this.user = user
      }
      catch (ex) {
        console.error(ex.message)
      }
    }
  },
  data() {
    return {
      sessionkey: 'dGNhZG1pbjp0ZXN0MTIz',
      authentication: false,
      settings: setting,
      user: null,
      sessionStart: null,
    }
  }
})

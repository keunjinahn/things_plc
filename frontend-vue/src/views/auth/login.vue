<template>
    <div class="form full-form auth-cover">
        <div class="form-container">
            <div class="form-form">
                <div class="form-form-wrap">
                    <div class="form-container">
                        <div class="form-content">
                            <h1 class="text-center">
                                스마트 용접철망 <br>드지털 트윈 시스템
                            </h1>
                           
                            <b-form class="text-left" @submit.prevent="login">
                                <div class="form">
                                    <div id="username-field" class="field-wrapper input">
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            width="24"
                                            height="24"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            stroke-width="2"
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            class="feather feather-user"
                                        >
                                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                            <circle cx="12" cy="7" r="4"></circle>
                                        </svg>
                                        <b-input v-model="form.username" placeholder="user id" @keypress.enter="login"></b-input>
                                    </div>

                                    <div id="password-field" class="field-wrapper input mb-2">
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            width="24"
                                            height="24"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            stroke-width="2"
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            class="feather feather-lock"
                                        >
                                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                        </svg>
                                        <b-input v-model="form.password" type="password" placeholder="Password" @keypress.enter="login"></b-input>
                                    </div>
                                    <div class="d-sm-flex justify-content-center">
                                        <div class="field-wrapper login-button-wrapper">
                                            <b-button type="button" variant="primary" class="login-button" @click="login" :loading="loading">Log In</b-button>
                                        </div>
                                    </div>

                                    <!-- <div class="field-wrapper toggle-pass d-flex align-items-center">
                                        <p class="d-inline-block">Show Password</p>
                                        <b-checkbox switch class="switch s-primary"></b-checkbox>
                                    </div> -->

                                    <!-- <div class="field-wrapper text-center keep-logged-in">
                                        <b-checkbox class="checkbox-outline-primary">Keep me logged in</b-checkbox>
                                    </div> -->

                                    <!-- <div class="field-wrapper">
                                        <router-link to="/auth/pass-recovery" class="forgot-pass-link">Forgot Password?</router-link>
                                    </div> -->
                                </div>
                            </b-form>
                            <!-- <p class="terms-conditions">
                                © 2020 All Rights Reserved. This system was developed as part of a project affiliated with Hoseo University. Cookie Preferences, Privacy Policy, and Terms of Use.


                            </p> -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import '@/assets/sass/authentication/auth.scss';
    export default {
        metaInfo: { title: '충남지역지능화센터 해양지능화 솔루션' },
        mounted() {
            
        },
        methods: {
            async login() {

                if (!this.form.username || !this.form.password)
                    return (this.error = '아이디와 패스워드를 입력해 주세요.')
                this.loading = true
                try {
                    let {data} = await this.$http.post('login', this.form)
                    if (data.status) {
                        this.$session.login(data)
                        await this.$session.setToken(data.user)
                        this.$router.replace({name:'dashboard'})
                    }else {
                        if (data.reason == 1) {
                            alert('로그인이 실패(아이디를 확인하여주세요!)')
                        } else if (data.reason == 2) {
                            alert('로그인이 실패(패스워드를 확인하여주세요!)')
                        }
                    }
                    return data
                }
                catch (err) {
                    this.error = err.message
                    alert(err.message)
                }
                finally {
                    this.loading = false
                }

                //this.$router.replace({name: 'index2'})
            }
        },
        data(){
            return {
                loading: false,
                form: {
                    username: '',
                    password: ''
                },
                error: null,
                };
            }
    };
</script>

<style scoped>
.login-button-wrapper {
    width: 100%;
}

.login-button {
    width: 100%;
    min-height: 44px;
    height: 110%;
    font-size: 16px;
    font-weight: 600;
    padding: 12px 24px;
}
</style>

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Cookies from 'js-cookie'
import { login, logout, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(Cookies.get('token') || '')
  const userInfo = ref({})

  const isLoggedIn = computed(() => !!token.value)

  // 登录
  const loginAction = async (loginForm) => {
    try {
      const response = await login(loginForm)
      const { access_token, user_info } = response.data
      
      token.value = access_token
      userInfo.value = user_info
      
      // 保存token到cookie
      Cookies.set('token', access_token, { expires: 7 })
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '登录失败' 
      }
    }
  }

  // 登出
  const logoutAction = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      token.value = ''
      userInfo.value = {}
      Cookies.remove('token')
    }
  }

  // 获取用户信息
  const getUserInfoAction = async () => {
    try {
      const response = await getUserInfo()
      userInfo.value = response.data
      return { success: true }
    } catch (error) {
      // token可能已过期，清除登录状态
      token.value = ''
      userInfo.value = {}
      Cookies.remove('token')
      return { success: false }
    }
  }

  // 初始化用户信息
  const initUserInfo = async () => {
    if (token.value) {
      await getUserInfoAction()
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    loginAction,
    logoutAction,
    getUserInfoAction,
    initUserInfo
  }
})

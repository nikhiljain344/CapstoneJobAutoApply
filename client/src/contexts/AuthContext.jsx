import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(() => {
    // Initialize token from localStorage
    const savedToken = localStorage.getItem('token')
    console.log('🔄 Initial token:', savedToken ? 'exists' : 'none')
    if (savedToken) {
      try {
        // Verify token format
        const tokenParts = savedToken.split('.')
        if (tokenParts.length === 3) {
          return savedToken
        }
      } catch (error) {
        console.error('❌ Invalid token format:', error)
        localStorage.removeItem('token')
        return null
      }
    }
    return null
  })

  // Load user on mount or token change
  useEffect(() => {
    const loadUser = async () => {
      console.log('🔄 Loading user, token:', token ? 'exists' : 'none')
      if (token) {
        try {
          const data = await authAPI.getCurrentUser()
          console.log('✅ User loaded:', data.user)
          setUser(data.user)
        } catch (error) {
          console.error('❌ Failed to load user:', error)
          // Clear auth state on error
          localStorage.removeItem('token')
          setToken(null)
          setUser(null)
        }
      }
      setLoading(false)
    }

    loadUser()
  }, [token])

  const login = async (email, password) => {
    try {
      console.log('🔄 Login attempt:', email)
      // Clear any existing auth state
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)

      const data = await authAPI.login(email, password)
      console.log('✅ Login response:', data)
      const { access_token, user: userData } = data

      // Validate token before storing
      if (!access_token || typeof access_token !== 'string') {
        throw new Error('Invalid token received')
      }

      console.log('🔑 Setting token and user')
      // Set token first
      localStorage.setItem('token', access_token)
      setToken(access_token)
      
      // Then set user
      setUser(userData)

      return { success: true, user: userData }
    } catch (error) {
      console.error('❌ Login error:', error)
      return { 
        success: false, 
        error: error.error || error.message || 'Login failed' 
      }
    }
  }

  const register = async (userData) => {
    try {
      console.log('🔄 Register attempt:', userData.email)
      // Clear any existing auth state
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)

      const data = await authAPI.register(userData)
      console.log('✅ Register response:', data)
      const { access_token, user: newUser } = data

      // Validate token before storing
      if (!access_token || typeof access_token !== 'string') {
        throw new Error('Invalid token received')
      }

      console.log('🔑 Setting token and user')
      // Set token first
      localStorage.setItem('token', access_token)
      setToken(access_token)
      
      // Then set user
      setUser(newUser)

      return { success: true, user: newUser }
    } catch (error) {
      console.error('❌ Register error:', error)
      return { 
        success: false, 
        error: error.error || error.message || 'Registration failed' 
      }
    }
  }

  const logout = () => {
    console.log('🔒 Logging out')
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const updateProfile = async (profileData) => {
    try {
      const data = await authAPI.updateProfile(profileData)
      setUser(data.user)
      return { success: true, user: data.user }
    } catch (error) {
      console.error('❌ Update profile error:', error)
      return { 
        success: false, 
        error: error.error || error.message || 'Failed to update profile' 
      }
    }
  }

  const changePassword = async (currentPassword, newPassword) => {
    try {
      await authAPI.changePassword(currentPassword, newPassword)
      return { success: true }
    } catch (error) {
      console.error('❌ Change password error:', error)
      return { 
        success: false, 
        error: error.error || error.message || 'Failed to change password' 
      }
    }
  }

  const value = {
    user,
    loading,
    token,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}


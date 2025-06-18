import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

const API_BASE_URL = 'http://localhost:5002/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(() => {
    // Initialize token from localStorage
    const savedToken = localStorage.getItem('token')
    if (savedToken) {
      try {
        // Verify token format
        const tokenParts = savedToken.split('.')
        if (tokenParts.length === 3) {
          return savedToken
        }
      } catch (error) {
        localStorage.removeItem('token')
        return null
      }
    }
    return null
  })

  // API helper function with retry mechanism
  const apiCall = async (endpoint, options = {}, retryCount = 0) => {
    const url = `${API_BASE_URL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      credentials: 'include',
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      // Handle 401 Unauthorized
      if (response.status === 401 && retryCount === 0) {
        // Token might be expired, try to refresh or logout
        logout()
        throw new Error('Session expired. Please login again.')
      }

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'An error occurred')
      }

      return data
    } catch (error) {
      console.error('API call failed:', error)
      throw error
    }
  }

  // Load user on mount or token change
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const data = await apiCall('/auth/me')
          setUser(data.user)
        } catch (error) {
          console.error('Failed to load user:', error)
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
      const data = await apiCall('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })

      const { access_token, user: userData } = data
      
      // Validate token before storing
      if (!access_token || typeof access_token !== 'string') {
        throw new Error('Invalid token received')
      }

      // Set token first
      localStorage.setItem('token', access_token)
      setToken(access_token)
      
      // Then set user
      setUser(userData)

      return { success: true, user: userData }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  const register = async (userData) => {
    try {
      const data = await apiCall('/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData),
      })

      const { access_token, user: newUser } = data
      
      // Validate token before storing
      if (!access_token || typeof access_token !== 'string') {
        throw new Error('Invalid token received')
      }

      // Set token first
      localStorage.setItem('token', access_token)
      setToken(access_token)
      
      // Then set user
      setUser(newUser)

      return { success: true, user: newUser }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const updateProfile = async (profileData) => {
    try {
      const data = await apiCall('/profile/basic', {
        method: 'PUT',
        body: JSON.stringify(profileData),
      })

      setUser(data.user)
      return { success: true, user: data.user }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  const changePassword = async (currentPassword, newPassword) => {
    try {
      await apiCall('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
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
    apiCall,
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}


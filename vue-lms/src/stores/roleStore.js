/**
 * ROLE STORE
 * 
 * Central store for user role and authentication state.
 * 
 * State:
 *   - role: Current active role (null if not logged in)
 *   - availableRoles: All roles the user has access to
 *   - user: User data from backend
 * 
 * Methods:
 *   - setUserData(user, roles): Set user and available roles after login
 *   - setRole(role): Set the current active role
 *   - clearRole(): Clear everything on logout
 */

import { reactive } from 'vue'

export const ROLES = {
  ADMIN: 'Administrator',
  INSTRUCTOR: 'Instructor',
  LEARNER: 'Learner'
}

export function useRoleStore() {
  const state = reactive({
    role: null,              // Current active role
    availableRoles: [],      // All roles user can switch between
    user: null               // User data (name, email, etc.)
  })

  const setUserData = (userData, userRoles, accessToken) => {
    state.user = userData
    state.availableRoles = userRoles
    if (accessToken) {
      localStorage.setItem('access_token', accessToken)
    }
    localStorage.setItem('userData', JSON.stringify(userData))
    localStorage.setItem('availableRoles', JSON.stringify(userRoles))
  }

  const setRole = (newRole) => {
    state.role = newRole
    // Persist to localStorage
    localStorage.setItem('userRole', newRole)
  }

  const clearRole = () => {
    state.role = null
    state.availableRoles = []
    state.user = null
    localStorage.removeItem('userRole')
    localStorage.removeItem('userData')
    localStorage.removeItem('availableRoles')
    localStorage.removeItem('access_token')
  }

  // On store creation, restore from localStorage if available
  const savedRole = localStorage.getItem('userRole')
  const savedUser = localStorage.getItem('userData')
  const savedRoles = localStorage.getItem('availableRoles')
  
  if (savedRole && Object.values(ROLES).includes(savedRole)) {
    state.role = savedRole
  }
  
  if (savedUser) {
    try {
      state.user = JSON.parse(savedUser)
    } catch (e) {
      console.error('Failed to parse saved user data')
    }
  }
  
  if (savedRoles) {
    try {
      state.availableRoles = JSON.parse(savedRoles)
    } catch (e) {
      console.error('Failed to parse saved roles')
    }
  }

  return {
    state,
    setUserData,
    setRole,
    clearRole
  }
}


/**
 * useAccess - Complete helper for authentication and role-based access control
 * 
 * This replaces direct roleStore access for cleaner, consistent code.
 * 
 * Usage in any component:
 *   const { isAdmin, isInstructor, isLearner, hasRole, setUserData, setRole, clearRole, role, availableRoles, user } = useAccess()
 * 
 * Example:
 *   <button v-if="isAdmin">Admin Only</button>
 *   <div v-if="hasRole(['Administrator', 'Instructor'])">Admin or Instructor</div>
 * 
 * Login usage:
 *   const { setUserData, setRole } = useAccess()
 *   setUserData(userData, userRoles)
 *   setRole(userRoles[0])
 */

import { computed, inject } from 'vue'
import { ROLES } from '../stores/roleStore'

export function useAccess() {
  // Get the central role store
  const roleStore = inject('roleStore')
  
  // Current user's role
  const role = computed(() => roleStore.state.role)
  
  // Available roles for the user
  const availableRoles = computed(() => roleStore.state.availableRoles)
  
  // User data
  const user = computed(() => roleStore.state.user)
  
  // Simple helpers for each role type
  const isAdmin = computed(() => role.value === ROLES.ADMIN)
  const isInstructor = computed(() => role.value === ROLES.INSTRUCTOR)
  const isLearner = computed(() => role.value === ROLES.LEARNER)
  
  // Check if current role is in the allowed list
  const hasRole = (allowedRoles) => {
    if (!allowedRoles || allowedRoles.length === 0) return true
    return allowedRoles.includes(role.value)
  }
  
  // Set user data after login (stores user + all available roles)
  const setUserData = (userData, userRoles, accessToken) => {
    roleStore.setUserData(userData, userRoles, accessToken)
  }
  
  // Set/switch current active role
  const setRole = (newRole) => {
    roleStore.setRole(newRole)
  }
  
  // Clear all data (logout)
  const clearRole = () => {
    roleStore.clearRole()
  }
  
  return {
    // State
    role,
    availableRoles,
    user,
    
    // Role checks
    isAdmin,
    isInstructor,
    isLearner,
    hasRole,
    
    // Actions
    setUserData,
    setRole,
    clearRole
  }
}

// Export ROLES so components don't need to import from roleStore
export { ROLES }

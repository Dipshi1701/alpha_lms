/**
 * CENTRALIZED ROUTE PERMISSIONS
 * 
 * Route types:
 *   - Public routes: meta.public = true (login, role picker)
 *   - Protected routes: meta.roles = [...] (requires specific role)
 *   - Open routes: no meta (accessible to anyone logged in)
 * 
 * Flow:
 *   1. Public routes → Allow everyone
 *   2. Check if user has a role (logged in)
 *   3. Check if route requires specific roles
 *   4. Allow or redirect based on permissions
 */

import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/layout/Layout.vue'
import { authRoutes } from '../modules/auth/routes'
import { dashboardRoutes } from '../modules/dashboard/routes'
import { courseChildRoutes, courseStandaloneRoutes } from '../modules/courses/routes'
import { userRoutes } from '../modules/users/routes'
import { reportRoutes } from '../modules/reports/routes'
import { settingsRoutes } from '../modules/settings/routes'
import { miscRoutes } from '../modules/misc/routes'
import { useRoleStore } from '../stores/roleStore'

const childRoutes = [
  { path: '', redirect: '/dashboard' },
  ...dashboardRoutes,
  ...userRoutes,
  ...courseChildRoutes,
  ...reportRoutes,
  ...settingsRoutes,
  ...miscRoutes
]

const routes = [
  ...authRoutes,  // Login and role picker (public routes)
  ...courseStandaloneRoutes,
  {
    path: '/',
    component: Layout,
    children: childRoutes
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ===== GLOBAL AUTHENTICATION & AUTHORIZATION GUARD =====
router.beforeEach((to, from, next) => {
  const roleStore = useRoleStore()
  const currentRole = roleStore.state.role
  
  // 1. Check if route is public (login, role picker, etc.)
  if (to.meta?.public) {
    return next()  // Public routes always accessible
  }
  
  // 2. Check if user is logged in (has a role)
  if (!currentRole) {
    // Not logged in, redirect to login
    return next('/login')
  }
  
  // 3. Get required roles for this route
  const allowedRoles = to.meta?.roles
  
  // 4. If route has no role restriction, allow (logged-in users can access)
  if (!allowedRoles || allowedRoles.length === 0) {
    return next()
  }
  
  // 5. Check if current user's role is in the allowed list
  if (allowedRoles.includes(currentRole)) {
    return next()  // User has permission
  }
  
  // 6. User doesn't have permission, redirect to dashboard
  console.warn(`Access denied: ${currentRole} tried to access ${to.path}`)
  return next('/dashboard')
})

export default router

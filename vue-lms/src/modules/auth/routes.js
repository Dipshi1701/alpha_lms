/**
 * AUTHENTICATION ROUTES
 * 
 * Public routes (no authentication required):
 *   - /login: Login page
 */

import Login from './views/Login.vue'

export const authRoutes = [
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { public: true }  // No authentication required
  }
]

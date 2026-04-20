/**
 * USER MANAGEMENT ROUTES
 * 
 * Users page: Only Administrator can access
 * Groups page: Administrator + Instructor can access
 */

import Users from './views/Users.vue'
import Groups from './views/Groups.vue'
import { ROLES } from '../../composables/useAccess'

export const userRoutes = [
  {
    path: 'users',
    component: Users,
    meta: { roles: [ROLES.ADMIN] }  // Only admin can manage users
  },
  {
    path: 'groups',
    component: Groups,
    meta: { roles: [ROLES.ADMIN, ROLES.INSTRUCTOR] }  // Admin + Instructor
  },
]


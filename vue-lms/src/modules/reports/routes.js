/**
 * REPORTS & AUTOMATIONS ROUTES
 * 
 * Reports: Admin + Instructor can access
 * Automations: Only Admin can access
 */

import Reports from './views/Reports.vue'
import Automations from './views/Automations.vue'
import { ROLES } from '../../composables/useAccess'

export const reportRoutes = [
  {
    path: 'reports',
    component: Reports,
    meta: { roles: [ROLES.ADMIN, ROLES.INSTRUCTOR] }  // Admin + Instructor
  },
  {
    path: 'automations',
    component: Automations,
    meta: { roles: [ROLES.ADMIN] }  // Only Admin
  },
]


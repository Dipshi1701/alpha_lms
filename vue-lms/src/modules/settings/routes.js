/**
 * SETTINGS & HELP ROUTES
 * 
 * Account Settings: Only Admin can access
 * Notifications: Only Admin can access
 * Help: Instructor + Learner can access
 */

import AccountSettings from './views/AccountSettings.vue'
import StubPage from '../misc/views/StubPage.vue'
import { ROLES } from '../../composables/useAccess'

export const settingsRoutes = [
  {
    path: 'account-settings',
    component: AccountSettings,
    meta: { roles: [ROLES.ADMIN] }  // Only Admin
  },
  {
    path: 'notifications',
    component: StubPage,
    props: { title: 'Notifications' },
    meta: { roles: [ROLES.ADMIN] }  // Only Admin
  },
  {
    path: 'help',
    component: StubPage,
    props: { title: 'Help Center' },
    meta: { roles: [ROLES.INSTRUCTOR, ROLES.LEARNER] }  // Instructor + Learner
  },
]


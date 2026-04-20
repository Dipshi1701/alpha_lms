/**
 * CENTRALIZED NAVIGATION CONFIG
 * 
 * All menu items for all roles in one place.
 * Each item can have:
 *   - label: Text to show
 *   - icon: Icon component
 *   - to: Route path
 *   - roles: Array of roles that can see this item (if empty, everyone can see)
 *   - badge: Optional badge text
 *   - arrow: Show right arrow icon
 *   - children: Sub-menu items
 * 
 * To add a new menu item:
 *   1. Add it to this array
 *   2. Set which roles can see it
 *   3. That's it! The sidebar will automatically filter based on current role
 */

import {
  Home,
  BookOpen,
  Map,
  Users2,
  BarChart2,
  Calendar,
  Users,
  Zap,
  Bell,
  Settings,
  ShoppingBag,
  GraduationCap,
  Video,
  HelpCircle,
  BookMarked
} from 'lucide-vue-next'
import { ROLES } from '../composables/useAccess'

export const NAV_ITEMS = [
  // ===== SHARED ITEMS (all roles) =====
  {
    label: 'Home',
    icon: Home,
    to: '/dashboard',
    roles: [], // empty = everyone can see
    badge: null
  },
  
  // ===== ADMIN ONLY =====
  {
    label: 'Users',
    icon: Users,
    to: '/users',
    roles: [ROLES.ADMIN]
  },
  
  // ===== ADMIN + INSTRUCTOR =====
  {
    label: 'Courses',
    icon: BookOpen,
    to: '/courses',
    roles: [ROLES.ADMIN, ROLES.INSTRUCTOR, ROLES.LEARNER]
  },
  {
    label: 'Learning paths',
    icon: Map,
    to: '/learning-paths',
    roles: [ROLES.ADMIN, ROLES.INSTRUCTOR]
  },
  {
    label: 'Groups',
    icon: Users2,
    to: '/groups',
    roles: [ROLES.ADMIN, ROLES.INSTRUCTOR]
  },
  
  // ===== ADMIN ONLY (with submenu) =====
  {
    label: 'Course store',
    icon: ShoppingBag,
    to: '/course-store',
    roles: [ROLES.ADMIN],
    arrow: true,
    children: [
      { label: 'All courses',    to: '/course-store' },
      { label: 'My purchases',   to: '/course-store/purchases' },
      { label: 'Browse bundles', to: '/course-store/bundles' }
    ]
  },
  
  // ===== ADMIN ONLY =====
  {
    label: 'Automations',
    icon: Zap,
    to: '/automations',
    roles: [ROLES.ADMIN]
  },
  {
    label: 'Notifications',
    icon: Bell,
    to: '/notifications',
    roles: [ROLES.ADMIN]
  },
  
  // ===== INSTRUCTOR ONLY =====
  {
    label: 'Grading Hub',
    icon: GraduationCap,
    to: '/grading-hub',
    roles: [ROLES.INSTRUCTOR]
  },
  {
    label: 'Conferences',
    icon: Video,
    to: '/conferences',
    roles: [ROLES.INSTRUCTOR]
  },
  
  // ===== LEARNER ONLY =====
  {
    label: 'Catalog',
    icon: BookMarked,
    to: '/catalog',
    roles: [ROLES.LEARNER]
  },
  
  // ===== ADMIN + INSTRUCTOR + LEARNER =====
  {
    label: 'Calendar',
    icon: Calendar,
    to: '/calendar',
    roles: [ROLES.INSTRUCTOR, ROLES.LEARNER]
  },
  
  // ===== ADMIN + INSTRUCTOR =====
  {
    label: 'Reports',
    icon: BarChart2,
    to: '/reports',
    roles: [ROLES.ADMIN, ROLES.INSTRUCTOR],
    arrow: true
  },
  
  // ===== ADMIN ONLY =====
  {
    label: 'Account & Settings',
    icon: Settings,
    to: '/account-settings',
    roles: [ROLES.ADMIN],
    arrow: true
  }
]

// Help Center (shown for Instructor + Learner at bottom of sidebar)
export const HELP_CENTER_ITEM = {
  label: 'Help Center',
  icon: HelpCircle,
  to: '/help',
  roles: [ROLES.INSTRUCTOR, ROLES.LEARNER]
}

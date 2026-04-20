/**
 * COURSE-RELATED ROUTES
 * 
 * Courses, Learning Paths: Admin + Instructor can access
 * Grading Hub: Only Instructor can access
 * Course Player: Everyone can access (no role restriction)
 */

import Courses from './views/Courses.vue'
import LearningPaths from './views/LearningPaths.vue'
import GradingHub from './views/GradingHub.vue'
import CoursePlayer from './views/CoursePlayer.vue'
import { ROLES } from '../../composables/useAccess'

export const courseChildRoutes = [
  {
    path: 'courses',
    component: Courses,
    // Admin + Instructor: management table. Learner: My assignments / My learning.
    meta: { roles: [ROLES.ADMIN, ROLES.INSTRUCTOR, ROLES.LEARNER] }
  },
  {
    path: 'learning-paths',
    component: LearningPaths,
    meta: { roles: [ROLES.ADMIN, ROLES.INSTRUCTOR] }  // Admin + Instructor
  },
  {
    path: 'grading-hub',
    component: GradingHub,
    meta: { roles: [ROLES.INSTRUCTOR] }  // Only Instructor
  },
]

export const courseStandaloneRoutes = [
  {
    path: '/courses/:courseId/play',
    name: 'course-player',
    component: CoursePlayer,
    // No meta.roles = everyone can access (learners can view courses)
  },
]


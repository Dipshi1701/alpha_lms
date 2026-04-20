export const MASTER_COURSES = [
  { id: 1,  title: 'Company Overview',           code: '001', category: 'General',    price: '-', updatedAt: '23/03/2026', duration: '45m',    contentType: 'scorm12', color: 'bg-blue-400',   enrolled: 5,  completion: 80,  status: 'Published' },
  { id: 2,  title: 'Product Knowledge 101',      code: '002', category: 'Sales',      price: '-', updatedAt: '24/03/2026', duration: '1h 20m', contentType: 'scorm12', color: 'bg-indigo-400', enrolled: 4,  completion: 60,  status: 'Published' },
  { id: 3,  title: 'Sales Techniques',           code: '003', category: 'Sales',      price: '-', updatedAt: '22/01/2026', duration: '2h',     contentType: 'scorm12', color: 'bg-purple-400', enrolled: 3,  completion: 40,  status: 'Published' },
  { id: 4,  title: 'Effective Communication',    code: '004', category: 'Management', price: '-', updatedAt: '22/01/2026', duration: '1h',     contentType: 'scorm12', color: 'bg-emerald-400',enrolled: 2,  completion: 100, status: 'Published' },
  { id: 5,  title: 'Team Management',            code: '005', category: 'Management', price: '-', updatedAt: '20/01/2026', duration: '1h 30m', contentType: 'scorm12', color: 'bg-teal-400',   enrolled: 2,  completion: 50,  status: 'Published' },
  { id: 6,  title: 'Workplace Safety',           code: '006', category: 'Compliance', price: '-', updatedAt: '18/01/2026', duration: '2h',     contentType: 'scorm12', color: 'bg-orange-400', enrolled: 0,  completion: 0,   status: 'Draft'     },
  { id: 7,  title: 'Data Protection (GDPR)',     code: '007', category: 'Compliance', price: '-', updatedAt: '17/01/2026', duration: '1h 30m', contentType: 'scorm12', color: 'bg-red-400',    enrolled: 0,  completion: 0,   status: 'Draft'     },
  { id: 8,  title: 'Anti-Harassment Policy',     code: '008', category: 'Compliance', price: '-', updatedAt: '16/01/2026', duration: '45m',    contentType: 'scorm12', color: 'bg-pink-400',   enrolled: 0,  completion: 0,   status: 'Draft'     },
  { id: 9,  title: 'Code of Conduct',            code: '009', category: 'Compliance', price: '-', updatedAt: '15/01/2026', duration: '30m',    contentType: 'scorm12', color: 'bg-rose-400',   enrolled: 0,  completion: 0,   status: 'Draft'     },
  { id: 10, title: 'Customer Service Excellence',code: '010', category: 'Sales',      price: '-', updatedAt: '14/01/2026', duration: '1h 15m', contentType: 'scorm12', color: 'bg-cyan-400',   enrolled: 1,  completion: 20,  status: 'Published' },
  { id: 11, title: 'Project Management Basics',  code: '011', category: 'Technical',  price: '-', updatedAt: '13/01/2026', duration: '2h 30m', contentType: 'scorm12', color: 'bg-violet-400', enrolled: 1,  completion: 10,  status: 'Published' }
]

export const INITIAL_PATHS = [
  {
    id: 1,
    name: 'Sales Onboarding',
    code: '01. Sales Onboarding',
    category: 'Sales',
    color: 'bg-blue-500',
    description: 'A complete onboarding journey for new sales team members covering products, processes, and tools.',
    active: true,
    courseIds: [1, 2, 3],
    sections: [
      { id: 's1', title: 'Foundation', insertAfter: 0 },
      { id: 's2', title: 'Advanced Skills', insertAfter: 1 }
    ],
    enrolledUsers: 2,
    completionRule: 'all',
    courseOrder: 'sequential',
    createdAt: 'Jan 12, 2024'
  },
  {
    id: 2,
    name: 'Leadership Excellence',
    code: '02. Leadership',
    category: 'Management',
    color: 'bg-emerald-500',
    description: 'Develop essential leadership skills for managers and team leads.',
    active: true,
    courseIds: [4, 5],
    sections: [],
    enrolledUsers: 1,
    completionRule: 'percentage',
    completionPercentage: 80,
    courseOrder: 'free',
    createdAt: 'Feb 3, 2024'
  },
  {
    id: 3,
    name: 'Compliance & Safety',
    code: '03. Compliance',
    category: 'Compliance',
    color: 'bg-orange-500',
    description: 'Mandatory compliance training covering workplace safety, data protection, and regulations.',
    active: false,
    courseIds: [6, 7, 8, 9],
    sections: [],
    enrolledUsers: 0,
    completionRule: 'all',
    courseOrder: 'sequential',
    createdAt: 'Mar 1, 2024'
  }
]

// ─── Automation data ──────────────────────────────────────────────────────────

import {
  BookOpen, Clock, AlertCircle, Award, Users2, UserX,
  Play, Globe,
} from 'lucide-vue-next'

export const AUTOMATION_TYPES = [
  {
    id: 'course_complete_assign',
    label: 'On course X completion, assign course(s) Y',
    category: 'Course',
    icon: BookOpen,
    color: 'text-blue-500',
    bg: 'bg-blue-50',
    params: ['course_x', 'courses_y'],
  },
  {
    id: 'hours_after_course_complete_assign',
    label: 'Z hours after course X completion, assign course(s) Y',
    category: 'Course',
    icon: Clock,
    color: 'text-indigo-500',
    bg: 'bg-indigo-50',
    params: ['hours_z', 'course_x', 'courses_y'],
  },
  {
    id: 'hours_after_course_assign_assign',
    label: 'Z hours after course X assignment, assign course(s) Y',
    category: 'Course',
    icon: Clock,
    color: 'text-violet-500',
    bg: 'bg-violet-50',
    params: ['hours_z', 'course_x', 'courses_y'],
    supportsFilter: true,
  },
  {
    id: 'hours_after_course_failure_assign',
    label: 'Z hours after course X failure, assign course(s) Y',
    category: 'Course',
    icon: AlertCircle,
    color: 'text-red-500',
    bg: 'bg-red-50',
    params: ['hours_z', 'course_x', 'courses_y'],
  },
  {
    id: 'course_complete_score_assign',
    label: 'On course X completion, with a score between K and L, assign course(s) Y',
    category: 'Course',
    icon: Award,
    color: 'text-amber-500',
    bg: 'bg-amber-50',
    params: ['course_x', 'score_k', 'score_l', 'courses_y'],
  },
  {
    id: 'course_complete_give_points',
    label: 'On course X completion, give Z points',
    category: 'Gamification',
    icon: Award,
    color: 'text-yellow-500',
    bg: 'bg-yellow-50',
    params: ['course_x', 'hours_z'],
  },
  {
    id: 'cert_expiry_reset_assign',
    label: 'On course X certificate expiration, reset and assign course(s) Y',
    category: 'Certificate',
    icon: Award,
    color: 'text-green-500',
    bg: 'bg-green-50',
    params: ['course_x', 'courses_y'],
  },
  {
    id: 'hours_before_cert_expiry_assign',
    label: 'Z hours before course X certificate expiration, reset and assign course(s) Y',
    category: 'Certificate',
    icon: Clock,
    color: 'text-teal-500',
    bg: 'bg-teal-50',
    params: ['hours_z', 'course_x', 'courses_y'],
  },
  {
    id: 'hours_after_cert_expiry_assign',
    label: 'Z hours after course X certificate expiration, reset and assign course(s) Y',
    category: 'Certificate',
    icon: Clock,
    color: 'text-cyan-500',
    bg: 'bg-cyan-50',
    params: ['hours_z', 'course_x', 'courses_y'],
  },
  {
    id: 'hours_after_signup_assign',
    label: 'Z hours after user signup, assign course(s) Y',
    category: 'User',
    icon: Users2,
    color: 'text-purple-500',
    bg: 'bg-purple-50',
    params: ['hours_z', 'courses_y'],
  },
  {
    id: 'hours_after_last_login_deactivate',
    label: 'Z hours after last login, deactivate or delete user',
    category: 'User',
    icon: UserX,
    color: 'text-rose-500',
    bg: 'bg-rose-50',
    params: ['hours_z', 'action_deactivate_delete'],
    supportsFilter: true,
  },
  {
    id: 'lp_assign_assign_lp',
    label: 'Z hours after learning path X assignment, assign learning path(s) Y',
    category: 'Learning Path',
    icon: Play,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    params: ['hours_z', 'lp_x', 'lps_y'],
  },
  {
    id: 'lp_assign_assign_course',
    label: 'Z hours after learning path X assignment, assign course(s) Y',
    category: 'Learning Path',
    icon: Play,
    color: 'text-sky-500',
    bg: 'bg-sky-50',
    params: ['hours_z', 'lp_x', 'courses_y'],
  },
  {
    id: 'course_complete_call_url',
    label: 'On course X completion, call URL Z',
    category: 'Integration',
    icon: Globe,
    color: 'text-gray-600',
    bg: 'bg-gray-100',
    params: ['course_x', 'url_z'],
  },
]

export const AUTOMATION_MOCK_COURSES = [
  'Company Overview', 'Product Knowledge 101', 'Sales Techniques',
  'Effective Communication', 'Team Management', 'Workplace Safety',
  'Data Protection (GDPR)', 'Anti-Harassment Policy', 'Code of Conduct',
]

export const AUTOMATION_MOCK_LPS = ['Sales Onboarding', 'Leadership Excellence', 'Compliance & Safety']

export const AUTOMATION_CATEGORIES = ['All', 'Course', 'User', 'Certificate', 'Learning Path', 'Gamification', 'Integration']

export const INITIAL_AUTOMATIONS = [
  {
    id: 1, name: 'New hire course sequence', active: true,
    typeId: 'hours_after_signup_assign',
    params: { hours_z: '24', courses_y: 'Company Overview' },
    filter: null, runs: 5, lastRun: '2 days ago',
  },
  {
    id: 2, name: 'Safety refresher on cert expiry', active: true,
    typeId: 'cert_expiry_reset_assign',
    params: { course_x: 'Workplace Safety', courses_y: 'Workplace Safety' },
    filter: null, runs: 2, lastRun: '1 week ago',
  },
  {
    id: 3, name: 'Deactivate inactive users', active: false,
    typeId: 'hours_after_last_login_deactivate',
    params: { hours_z: '720', action_deactivate_delete: 'deactivate' },
    filter: 'Learners', runs: 0, lastRun: 'Never',
  },
]

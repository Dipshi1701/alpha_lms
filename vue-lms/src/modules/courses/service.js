import { get, patch, post, postForm, remove } from '../../api/api'

// ── SCORM Progress ──────────────────────────────────────────────────────────

/** Fetch progress across all of the current user's courses (for the list view). */
export function fetchMyProgress() {
  return get('/api/scorm/my-progress')
}

/** Load saved SCORM state for one course (used to resume a session). */
export function fetchScormState(courseId) {
  return get(`/api/scorm/${courseId}/state`)
}

/**
 * Save SCORM runtime values (called on every LMSCommit).
 * @param {number} courseId
 * @param {{ lesson_location, suspend_data, lesson_status, score_raw, session_time, total_time }} payload
 */
export function commitScormProgress(courseId, payload) {
  return post(`/api/scorm/${courseId}/commit`, payload)
}

/**
 * Finalize the SCORM session (called on LMSFinish).
 * @param {number} courseId
 * @param {{ lesson_location, suspend_data, lesson_status, score_raw, total_time }} payload
 */
export function finishScormSession(courseId, payload = {}) {
  return post(`/api/scorm/${courseId}/finish`, payload)
}

// ── Courses ─────────────────────────────────────────────────────────────────

const COURSE_COLORS = [
  'bg-blue-400',
  'bg-indigo-400',
  'bg-purple-400',
  'bg-emerald-400',
  'bg-teal-400',
  'bg-orange-400',
]

function mapCourse(course) {
  if (!course) return null
  return {
    id: course.id,
    title: course.title,
    description: course.description,
    category: course.category,
    code: course.code,
    price: course.price,
    status: course.status,
    contentType: course.content_type,
    scormZipName: course.scorm_zip_name,
    scormLaunchRelative: course.scorm_launch_relative,
    scormManifestTitle: course.scorm_manifest_title,
    scormValidatedAt: course.scorm_validated_at,
    assignedUserIds: course.assigned_user_ids || [],
    updatedAt: course.updated_at
      ? new Date(course.updated_at).toLocaleString(undefined, {
          dateStyle: 'medium',
          timeStyle: 'short',
        })
      : '—',
    color: COURSE_COLORS[Math.abs(Number(course.id)) % COURSE_COLORS.length],
  }
}

function mapAssignableUser(user) {
  return {
    id: user.id,
    name: user.full_name || user.email || `User ${user.id}`,
    role: user.roles?.includes('Learner') ? 'Learner' : user.roles?.[0] || '',
  }
}

export function fetchCoursesAdmin() {
  return get('/api/courses').then((rows) => rows.map(mapCourse))
}

export function fetchMyCoursesLearner() {
  return get('/api/courses/me').then((rows) => rows.map(mapCourse))
}

export function fetchAssignableUsers() {
  return get('/api/courses/assignable-users').then((rows) => rows.map(mapAssignableUser))
}

export function fetchCourse(courseId) {
  return get(`/api/courses/${courseId}`).then(mapCourse)
}

export function createCourse(payload) {
  return post('/api/courses', payload).then(mapCourse)
}

export function updateCourse(courseId, payload) {
  return patch(`/api/courses/${courseId}`, payload).then(mapCourse)
}

export function deleteCourse(courseId) {
  return remove(`/api/courses/${courseId}`)
}

export function assignCourseUsers(courseId, userIds) {
  return post(`/api/courses/${courseId}/assign`, { user_ids: userIds })
}

export function uploadScormZip(courseId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return postForm(`/api/courses/${courseId}/scorm/upload`, formData)
}

export function fetchLaunchUrl(courseId) {
  return get(`/api/courses/${courseId}/launch`)
}

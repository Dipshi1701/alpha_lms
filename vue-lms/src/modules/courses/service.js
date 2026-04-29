import { get, patch, post, postForm, remove } from '../../api/api'

// ── SCORM — Layer 1: Launch / Resume ────────────────────────────────────────

/**
 * Load raw SCORM launch state for one course.
 * Returns tl_sco_data shape — assign this to window.tl_sco_data before
 * loading the SCORM runtime JS and the iframe.
 *
 * @param {number} courseId
 * @returns {{ student_id, student_name, lesson_location, suspend_data,
 *             lesson_status, score_raw, total_time, entry, datafromlms,
 *             masteryscore, maxtimeallowed, timelimitaction,
 *             lesson_mode, comments_from_lms }}
 */
export function fetchScormState(courseId) {
  return get(`/api/scorm/${courseId}/state`)
}

// ── SCORM — Layer 2: Save APIs ───────────────────────────────────────────────

/**
 * Persist mid-session SCORM state (called on every LMSCommit).
 * Payload uses JS field names — backend maps them to DB columns.
 *
 * JS field name  →  DB column
 *   score        →  score_raw
 *   minscore     →  score_min
 *   maxscore     →  score_max
 *   scorm_exit   →  scorm_exit
 *
 * @param {number} courseId
 * @param {object} payload  — raw SCOState object from commitData()
 */
export function commitScormProgress(courseId, payload) {
  return post(`/api/scorm/${courseId}/commit`, payload)
}

/**
 * Finalize the SCORM session (called on LMSFinish).
 * total_time is updated on the backend only on finish.
 *
 * @param {number} courseId
 * @param {object} payload  — raw SCOState object from commitData('finish')
 */
export function finishScormSession(courseId, payload = {}) {
  return post(`/api/scorm/${courseId}/finish`, payload)
}

// ── SCORM — Layer 3: LMS Progress / Reporting ────────────────────────────────

/**
 * Fetch a summary of all SCORM progress for the current user.
 * Used by the learner's course list / dashboard.
 * Returns business summary fields — NOT raw SCORM launch state.
 */
export function fetchMyProgress() {
  return get('/api/scorm/my-progress')
}

/**
 * Fetch a detailed progress report for one course.
 * Returns course_progress and unit_progress in a dashboard-friendly shape.
 * Completely separate from the raw launch state returned by fetchScormState().
 *
 * @param {number} courseId
 */
export function fetchProgressSummary(courseId) {
  return get(`/api/scorm/${courseId}/progress-summary`)
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

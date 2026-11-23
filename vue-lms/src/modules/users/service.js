import { get, patch, post, remove } from '../../api/api'

export function fetchUsers() {
  return get('/api/users')
}

export function createUser(payload) {
  return post('/api/users', payload)
}

// ── Groups ────────────────────────────────────────────────────────────────
// Thin wrappers around the existing Groups API (see backend/app/routes/groups.py).
// Only methods backed by a real endpoint are exposed here. Group members
// and managers can both be listed.

function mapGroup(group) {
  if (!group) return null
  return {
    id: group.id,
    name: group.name,
    createdAt: group.created_at,
    createdById: group.created_by_id ?? null,
  }
}

function mapGroupCourse(course) {
  return {
    id: course.id,
    title: course.title,
    category: course.category,
    status: course.status,
  }
}

// Learners eligible to be added as group members — reuses the same
// Learner-only endpoint the Courses module already uses for its
// assign-learners picker (GET /api/courses/assignable-users).
function mapLearnerOption(user) {
  return {
    id: user.id,
    name: user.full_name || user.email || `User ${user.id}`,
  }
}

export function fetchGroups() {
  return get('/api/groups').then((rows) => rows.map(mapGroup))
}

export function fetchGroup(groupId) {
  return get(`/api/groups/${groupId}`).then(mapGroup)
}

export function createGroup(payload) {
  return post('/api/groups', payload).then(mapGroup)
}

export function updateGroup(groupId, payload) {
  return patch(`/api/groups/${groupId}`, payload).then(mapGroup)
}

export function deleteGroup(groupId) {
  return remove(`/api/groups/${groupId}`)
}

export function fetchAssignableLearners() {
  return get('/api/courses/assignable-users').then((rows) => rows.map(mapLearnerOption))
}

export function fetchGroupMembers(groupId) {
  return get(`/api/groups/${groupId}/members`).then((rows) =>
    (rows || []).map((member) => ({
      id: member.id,
      userId: member.user_id,
      name: member.full_name || member.email || `User ${member.user_id}`,
      email: member.email || '',
      addedAt: member.added_at,
    }))
  )
}

export function addGroupMember(groupId, userId) {
  return post(`/api/groups/${groupId}/members`, { user_id: userId })
}

export function removeGroupMember(groupId, userId) {
  return remove(`/api/groups/${groupId}/members/${userId}`)
}

// Instructors eligible to be assigned as a group manager. There is no
// dedicated "assignable instructors" endpoint, so this reuses GET
// /api/users (Administrator-only — matches the fact that manager
// assignment is itself Administrator-only) and filters to the Instructor
// role client-side.
export function fetchGroupManagers(groupId) {
  return get(`/api/groups/${groupId}/managers`).then((rows) =>
    (rows || []).map((manager) => ({
      id: manager.id,
      userId: manager.user_id,
      name: manager.full_name || manager.email || `User ${manager.user_id}`,
      email: manager.email || '',
      assignedAt: manager.assigned_at,
    }))
  )
}

export function fetchAssignableInstructors() {
  return fetchUsers().then((rows) =>
    rows
      .filter((u) => (u.roles || []).includes('Instructor'))
      .map((u) => ({
        id: u.id,
        name: u.full_name || u.email || `User ${u.id}`,
        email: u.email || '',
      }))
  )
}

export function assignGroupManager(groupId, userId) {
  return post(`/api/groups/${groupId}/managers`, { user_id: userId })
}

export function removeGroupManager(groupId, userId) {
  return remove(`/api/groups/${groupId}/managers/${userId}`)
}

export function fetchGroupCourses(groupId) {
  return get(`/api/groups/${groupId}/courses`).then((rows) => rows.map(mapGroupCourse))
}

export function assignGroupCourse(groupId, courseId) {
  return post(`/api/groups/${groupId}/courses`, { course_id: courseId })
}

export function removeGroupCourse(groupId, courseId) {
  return remove(`/api/groups/${groupId}/courses/${courseId}`)
}

// Courses available to offer in the "assign a course" picker — reuses the
// same admin/instructor course list the Courses module uses, filtered
// client-side to Published (the same "must be Published to assign" rule
// AdminInstructorCourses.vue already enforces for individual assignment).
export function fetchAssignableCourses() {
  return get('/api/courses').then((rows) =>
    rows
      .filter((c) => c.status === 'Published')
      .map((c) => ({ id: c.id, title: c.title }))
  )
}

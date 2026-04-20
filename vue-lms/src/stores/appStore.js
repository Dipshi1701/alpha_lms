import { reactive } from 'vue'
import { MASTER_COURSES, INITIAL_PATHS } from '../data/appData'

export function useAppStore() {
  const state = reactive({
    courses: [...MASTER_COURSES],
    paths: [...INITIAL_PATHS]
  })

  const addCourse = (course) => {
    const newCourse = { ...course, id: Date.now(), enrolled: 0, completion: 0 }
    state.courses.push(newCourse)
    return newCourse
  }

  const updateCourse = (updated) => {
    const idx = state.courses.findIndex(c => c.id === updated.id)
    if (idx === -1) return null
    state.courses[idx] = { ...state.courses[idx], ...updated }
    return state.courses[idx]
  }

  const deleteCourse = (courseId) => {
    const idx = state.courses.findIndex(c => c.id === courseId)
    if (idx === -1) return false
    state.courses.splice(idx, 1)
    state.paths.forEach((path) => {
      path.courseIds = (path.courseIds || []).filter((id) => id !== courseId)
    })
    return true
  }

  const createPath = (data) => {
    const path = { ...data, id: Date.now(), courseIds: [], enrolledUsers: 0, createdAt: 'Just now' }
    state.paths.unshift(path)
    return path
  }

  const updatePath = (updated) => {
    const idx = state.paths.findIndex(p => p.id === updated.id)
    if (idx !== -1) state.paths[idx] = updated
  }

  const deletePath = (id) => {
    const idx = state.paths.findIndex(p => p.id === id)
    if (idx !== -1) state.paths.splice(idx, 1)
  }

  const addCourseToPath = (courseId, pathId) => {
    const path = state.paths.find(p => p.id === pathId)
    if (!path) return
    const ids = path.courseIds || []
    if (!ids.includes(courseId)) {
      path.courseIds = [...ids, courseId]
    }
  }

  const removeCourseFromPath = (courseId, pathId) => {
    const path = state.paths.find(p => p.id === pathId)
    if (!path) return
    path.courseIds = (path.courseIds || []).filter(id => id !== courseId)
  }

  const getPathsForCourse = (courseId) =>
    state.paths.filter(p => (p.courseIds || []).includes(courseId))

  const getCoursesForPath = (path) =>
    (path.courseIds || []).map(id => state.courses.find(c => c.id === id)).filter(Boolean)

  return {
    state,
    addCourse,
    updateCourse,
    deleteCourse,
    createPath,
    updatePath,
    deletePath,
    addCourseToPath,
    removeCourseFromPath,
    getPathsForCourse,
    getCoursesForPath
  }
}


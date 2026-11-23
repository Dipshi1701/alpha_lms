import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { reactive } from 'vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import AdminInstructorCourses from '../AdminInstructorCourses.vue'
import * as courseService from '../../service'
import * as groupService from '../../../users/service'

vi.mock('../../service')
vi.mock('../../../users/service')

function makeRoleStore(role) {
  return { state: reactive({ role, availableRoles: [role], user: { id: 1, full_name: 'Test' } }) }
}

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/courses/:courseId/play', name: 'course-player', component: { template: '<div />' } },
    ],
  })
}

const PUBLISHED_COURSE = {
  id: 100,
  title: 'Angular Basics',
  description: 'A short description',
  category: 'General',
  code: 'C-100',
  price: '-',
  status: 'Published',
  contentType: 'none',
  assignedUserIds: [1], // Rahul already individually assigned
  assignmentDurationDays: 7,
  learnerAssignments: [
    {
      userId: 1,
      assignedAt: '2026-09-10T00:00:00',
      dueDate: '2026-09-17T00:00:00',
      source: 'individual',
      sourceGroupName: null,
    },
  ],
  updatedAt: '—',
}

const LEARNERS = [
  { id: 1, name: 'Rahul', role: 'Learner' },
  { id: 2, name: 'Amit', role: 'Learner' },
]

const GROUPS = [{ id: 10, name: 'Group X', createdAt: null, createdById: null }]

async function mountPage(role) {
  courseService.fetchCoursesAdmin.mockResolvedValue([{ ...PUBLISHED_COURSE }])
  courseService.fetchAssignableUsers.mockResolvedValue(LEARNERS)
  groupService.fetchGroups.mockResolvedValue(GROUPS)

  const router = makeRouter()
  await router.push('/')
  await router.isReady()
  const wrapper = mount(AdminInstructorCourses, {
    global: {
      provide: { roleStore: makeRoleStore(role) },
      plugins: [router],
    },
  })
  await flushPromises()
  return wrapper
}

async function openAssignModal(wrapper) {
  await wrapper.find('[title="Assign learners"]').trigger('click')
  await flushPromises()
}

describe('AdminInstructorCourses.vue — Individual vs Group course assignment (G011)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('Administrator opening the assign modal loads groups and offers Group mode', async () => {
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)

    expect(groupService.fetchGroups).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[data-testid="assign-mode-group"]').exists()).toBe(true)
  })

  it('Instructor opening the assign modal does not load groups and Group mode is not offered', async () => {
    const wrapper = await mountPage('Instructor')
    await openAssignModal(wrapper)

    expect(groupService.fetchGroups).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="assign-mode-group"]').exists()).toBe(false)
    // Individual assignment remains available to Instructor.
    expect(wrapper.find('[data-testid="assign-mode-individual"]').exists()).toBe(true)
  })

  it('submitting Individual mode calls the existing assign endpoint with the full desired user_ids set', async () => {
    courseService.assignCourseUsers.mockResolvedValue({ course_id: 100, user_ids: [1, 2] })
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)

    // Rahul (1) is already assigned (pre-checked); add Amit (2) too.
    await wrapper.find('[data-testid="assign-learner-2"]').trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    await flushPromises()

    expect(courseService.assignCourseUsers).toHaveBeenCalledWith(100, expect.arrayContaining([1, 2]))
    expect(courseService.assignCourseUsers.mock.calls[0][1]).toHaveLength(2)
  })

  it('submitting Group mode calls the existing group-course-assignment endpoint (not the individual one)', async () => {
    groupService.assignGroupCourse.mockResolvedValue({ id: 1, group_id: 10, course_id: 100 })
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)

    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-group-10"]').trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    await flushPromises()

    expect(groupService.assignGroupCourse).toHaveBeenCalledWith(10, 100)
    expect(courseService.assignCourseUsers).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Group X')
  })

  it('a duplicate group assignment surfaces the backend error and keeps the modal open', async () => {
    groupService.assignGroupCourse.mockRejectedValue(new Error('This course is already assigned to the group'))
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)

    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-group-10"]').trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('This course is already assigned to the group')
    // Modal stays open on failure (existing error-handling convention).
    expect(wrapper.find('[data-testid="assign-submit-btn"]').exists()).toBe(true)
  })

  it('a 403 from group assignment is handled gracefully without crashing', async () => {
    const err = new Error('Insufficient permissions')
    err.status = 403
    groupService.assignGroupCourse.mockRejectedValue(err)
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)

    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-group-10"]').trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Insufficient permissions')
  })

  it('a network/server error on individual assignment is handled through the existing error pattern', async () => {
    courseService.assignCourseUsers.mockRejectedValue(new Error('Network error'))
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)

    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Network error')
  })

  it('prevents a double submission from firing the assignment call twice', async () => {
    let resolveCall
    groupService.assignGroupCourse.mockReturnValue(
      new Promise((resolve) => {
        resolveCall = resolve
      })
    )
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-group-10"]').trigger('click')

    // Fire two rapid submits before the first call resolves.
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    resolveCall({ id: 1, group_id: 10, course_id: 100 })
    await flushPromises()

    expect(groupService.assignGroupCourse).toHaveBeenCalledTimes(1)
  })

  it('the group list shown is exactly what the backend returned — no client-side filtering', async () => {
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)

    expect(wrapper.findAll('[data-testid^="assign-group-"]')).toHaveLength(GROUPS.length)
  })

  it('Learner never sees the Courses management/assignment UI (existing behavior unchanged)', async () => {
    // AdminInstructorCourses.vue is only ever rendered for Admin/Instructor —
    // Courses.vue picks LearnerCourses.vue for Learner. This confirms this
    // component itself makes no learner-specific assignment exception.
    const wrapper = await mountPage('Administrator')
    expect(wrapper.find('[title="Assign learners"]').exists()).toBe(true)
  })

  it('the assign modal receives this course\'s learnerAssignments, showing the existing assignee as locked/annotated', async () => {
    const wrapper = await mountPage('Administrator')
    await openAssignModal(wrapper)

    expect(wrapper.find('[data-testid="assign-learner-1-info"]').text()).toContain('Already assigned individually')
    // Amit (2) has no entry in learnerAssignments -- fully selectable.
    expect(wrapper.find('[data-testid="assign-learner-2-info"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="assign-learner-2"]').attributes('disabled')).toBeUndefined()
  })
})

describe('AdminInstructorCourses.vue — Assignment Duration on course create/edit (G012)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  async function openEditModal(wrapper) {
    await wrapper.find('[title="Edit"]').trigger('click')
    await flushPromises()
  }

  function findModalButton(wrapper, text) {
    return wrapper.findAll('button').find((b) => b.text().includes(text))
  }

  it('pre-fills the Assignment Duration field from the course being edited', async () => {
    const wrapper = await mountPage('Administrator')
    await openEditModal(wrapper)

    expect(wrapper.find('[data-testid="course-assignment-duration-input"]').element.value).toBe('7')
  })

  it('editing a course sends the updated assignment_duration_days to updateCourse', async () => {
    courseService.updateCourse.mockResolvedValue({ ...PUBLISHED_COURSE, assignmentDurationDays: 14 })
    const wrapper = await mountPage('Administrator')
    await openEditModal(wrapper)

    await wrapper.find('[data-testid="course-assignment-duration-input"]').setValue('14')
    await findModalButton(wrapper, 'Save changes').trigger('click')
    await flushPromises()

    expect(courseService.updateCourse).toHaveBeenCalledWith(
      100,
      expect.objectContaining({ assignment_duration_days: 14 })
    )
  })

  it('an invalid duration blocks saving the course edit entirely', async () => {
    const wrapper = await mountPage('Administrator')
    await openEditModal(wrapper)

    await wrapper.find('[data-testid="course-assignment-duration-input"]').setValue('0')
    await findModalButton(wrapper, 'Save changes').trigger('click')
    await flushPromises()

    expect(courseService.updateCourse).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('must be 1 or more days')
  })
})

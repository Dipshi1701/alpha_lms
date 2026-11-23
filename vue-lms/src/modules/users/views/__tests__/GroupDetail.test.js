import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import GroupDetail from '../GroupDetail.vue'
import { createTestRouter, makeRoleStore } from './testUtils'
import * as groupService from '../../service'

vi.mock('../../service')

function withStatus(message, status) {
  const err = new Error(message)
  err.status = status
  return err
}

async function mountDetail(role, groupId = '5') {
  const router = createTestRouter()
  await router.push(`/groups/${groupId}`)
  await router.isReady()
  const wrapper = mount(GroupDetail, {
    global: {
      provide: { roleStore: makeRoleStore(role) },
      plugins: [router],
    },
  })
  await flushPromises()
  return { wrapper, router }
}

describe('GroupDetail.vue', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    groupService.fetchGroupCourses.mockResolvedValue([])
    groupService.fetchAssignableCourses.mockResolvedValue([])
    groupService.fetchUsers.mockResolvedValue([])
    groupService.fetchGroupMembers.mockResolvedValue([])
    groupService.fetchGroupManagers.mockResolvedValue([])
    groupService.fetchAssignableLearners.mockResolvedValue([])
    groupService.fetchAssignableInstructors.mockResolvedValue([])
  })

  it('loads and displays group details correctly', async () => {
    groupService.fetchGroup.mockResolvedValue({
      id: 5, name: 'Frontend Batch', createdAt: '2026-01-01T00:00:00', createdById: 1,
    })

    const { wrapper } = await mountDetail('Administrator')

    expect(groupService.fetchGroup).toHaveBeenCalledWith('5')
    expect(wrapper.text()).toContain('Frontend Batch')
    expect(wrapper.find('[data-testid="group-load-error"]').exists()).toBe(false)
  })

  it('loads and renders the group course list', async () => {
    groupService.fetchGroup.mockResolvedValue({ id: 5, name: 'Frontend Batch', createdAt: null, createdById: null })
    groupService.fetchGroupCourses.mockResolvedValue([
      { id: 10, title: 'Angular Basics', status: 'Published' },
      { id: 11, title: 'Vue Basics', status: 'Published' },
    ])

    const { wrapper } = await mountDetail('Administrator')
    await wrapper.find('[data-testid="tab-Courses"]').trigger('click')
    await flushPromises()

    expect(groupService.fetchGroupCourses).toHaveBeenCalledWith('5')
    expect(wrapper.text()).toContain('Angular Basics')
    expect(wrapper.text()).toContain('Vue Basics')
  })

  it('shows an empty state when the group has zero assigned courses', async () => {
    groupService.fetchGroup.mockResolvedValue({ id: 5, name: 'Empty Group', createdAt: null, createdById: null })
    groupService.fetchGroupCourses.mockResolvedValue([])

    const { wrapper } = await mountDetail('Administrator')
    await wrapper.find('[data-testid="tab-Courses"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('No courses assigned to this group yet')
  })

  it('handles a 403 response gracefully instead of crashing (unmanaged group for a scoped Instructor)', async () => {
    groupService.fetchGroup.mockRejectedValue(withStatus('Not allowed', 403))

    const { wrapper } = await mountDetail('Instructor')

    expect(wrapper.find('[data-testid="group-load-error"]').exists()).toBe(true)
    expect(wrapper.text()).toContain("don't have access")
    // No unhandled crash — the "Back to Groups" affordance is present.
    expect(wrapper.text()).toContain('Back to Groups')
  })

  it('handles a 404 (missing group) response gracefully', async () => {
    groupService.fetchGroup.mockRejectedValue(withStatus('Group not found', 404))

    const { wrapper } = await mountDetail('Administrator')

    expect(wrapper.find('[data-testid="group-load-error"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Group not found')
  })

  it('handles a generic network/server error gracefully', async () => {
    groupService.fetchGroup.mockRejectedValue(new Error('Network error'))

    const { wrapper } = await mountDetail('Administrator')

    expect(wrapper.find('[data-testid="group-load-error"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Network error')
  })

  it('lists current members and hides learners who are already in the group from the add picker', async () => {
    groupService.fetchGroup.mockResolvedValue({ id: 5, name: 'Frontend Batch', createdAt: null, createdById: null })
    groupService.fetchGroupMembers.mockResolvedValue([
      { id: 1, userId: 8, name: 'Asha Learner', email: 'asha@test.com', addedAt: '2026-01-02T00:00:00' },
    ])
    groupService.fetchAssignableLearners.mockResolvedValue([
      { id: 8, name: 'Asha Learner' },
      { id: 9, name: 'Ravi Learner' },
    ])

    const { wrapper } = await mountDetail('Administrator')
    await wrapper.find('[data-testid="tab-Members"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Asha Learner')
    expect(wrapper.text()).toContain('asha@test.com')

    await wrapper.find('[data-testid="add-members-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="pick-learner-8"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="pick-learner-9"]').exists()).toBe(true)
  })

  it('does not show Admin-only member/manager mutation controls to a scoped Instructor', async () => {
    groupService.fetchGroup.mockResolvedValue({ id: 5, name: 'Frontend Batch', createdAt: null, createdById: null })

    const { wrapper } = await mountDetail('Instructor')
    await wrapper.find('[data-testid="tab-Members"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Only an Administrator can add or remove group members')
    expect(wrapper.find('[data-testid="detail-edit-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="detail-delete-btn"]').exists()).toBe(false)
  })
})

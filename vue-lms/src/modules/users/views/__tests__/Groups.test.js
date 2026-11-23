import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Groups from '../Groups.vue'
import { createTestRouter, makeRoleStore } from './testUtils'
import * as groupService from '../../service'

vi.mock('../../service')

async function mountGroups(role, groups = []) {
  groupService.fetchGroups.mockResolvedValue(groups)
  const router = createTestRouter()
  await router.push('/groups')
  await router.isReady()
  const wrapper = mount(Groups, {
    global: {
      provide: { roleStore: makeRoleStore(role) },
      plugins: [router],
    },
  })
  await flushPromises()
  return { wrapper, router }
}

describe('Groups.vue (list page)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('Administrator sees the Create group action', async () => {
    const { wrapper } = await mountGroups('Administrator', [])
    expect(wrapper.find('[data-testid="create-group-btn"]').exists()).toBe(true)
  })

  it('Instructor does not see admin-only mutation actions (Create/Edit/Delete)', async () => {
    const { wrapper } = await mountGroups('Instructor', [
      { id: 1, name: 'Frontend Batch', createdAt: '2026-01-01T00:00:00', createdById: 2 },
    ])
    expect(wrapper.find('[data-testid="create-group-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="edit-group-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="delete-group-btn"]').exists()).toBe(false)
    // Instructor can still view a group they were returned.
    expect(wrapper.find('[data-testid="view-group-btn"]').exists()).toBe(true)
  })

  it('loads groups from the backend and renders them (does not filter client-side)', async () => {
    const { wrapper } = await mountGroups('Administrator', [
      { id: 1, name: 'Alpha Cohort', createdAt: '2026-01-01T00:00:00', createdById: 2 },
      { id: 2, name: 'Beta Cohort', createdAt: '2026-01-02T00:00:00', createdById: 2 },
    ])
    expect(groupService.fetchGroups).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Alpha Cohort')
    expect(wrapper.text()).toContain('Beta Cohort')
  })

  it('shows the Administrator empty state when there are no groups', async () => {
    const { wrapper } = await mountGroups('Administrator', [])
    expect(wrapper.text()).toContain('No groups yet')
  })

  it('shows the proper empty state for an Instructor managing zero groups', async () => {
    const { wrapper } = await mountGroups('Instructor', [])
    expect(wrapper.text()).toContain('No groups assigned to you yet')
  })

  it('creates a group successfully and refreshes the list', async () => {
    const { wrapper } = await mountGroups('Administrator', [])
    groupService.createGroup.mockResolvedValue({ id: 9, name: 'New Group', createdAt: null, createdById: null })
    groupService.fetchGroups.mockResolvedValue([{ id: 9, name: 'New Group', createdAt: null, createdById: null }])

    await wrapper.find('[data-testid="create-group-btn"]').trigger('click')
    await wrapper.find('[data-testid="group-name-input"]').setValue('New Group')
    await wrapper.find('[data-testid="group-form-submit"]').trigger('click')
    await flushPromises()

    expect(groupService.createGroup).toHaveBeenCalledWith({ name: 'New Group' })
    expect(groupService.fetchGroups).toHaveBeenCalledTimes(2) // initial load + refresh
    expect(wrapper.text()).toContain('New Group')
  })

  it('shows the API error in the modal when create fails and keeps the modal open', async () => {
    const { wrapper } = await mountGroups('Administrator', [])
    groupService.createGroup.mockRejectedValue(new Error('A group with this name already exists'))

    await wrapper.find('[data-testid="create-group-btn"]').trigger('click')
    await wrapper.find('[data-testid="group-name-input"]').setValue('Duplicate')
    await wrapper.find('[data-testid="group-form-submit"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('A group with this name already exists')
    // Modal should still be open (input still present) rather than silently closing.
    expect(wrapper.find('[data-testid="group-name-input"]').exists()).toBe(true)
  })

  it('edits a group successfully', async () => {
    const { wrapper } = await mountGroups('Administrator', [
      { id: 5, name: 'Old Name', createdAt: '2026-01-01T00:00:00', createdById: 1 },
    ])
    groupService.updateGroup.mockResolvedValue({ id: 5, name: 'Renamed', createdAt: '2026-01-01T00:00:00', createdById: 1 })
    groupService.fetchGroups.mockResolvedValue([{ id: 5, name: 'Renamed', createdAt: '2026-01-01T00:00:00', createdById: 1 }])

    await wrapper.find('[data-testid="edit-group-btn"]').trigger('click')
    await wrapper.find('[data-testid="group-name-input"]').setValue('Renamed')
    await wrapper.find('[data-testid="group-form-submit"]').trigger('click')
    await flushPromises()

    expect(groupService.updateGroup).toHaveBeenCalledWith(5, { name: 'Renamed' })
    expect(wrapper.text()).toContain('Renamed')
  })

  it('deletes a group after confirmation and removes it from the list', async () => {
    const { wrapper } = await mountGroups('Administrator', [
      { id: 5, name: 'To Delete', createdAt: '2026-01-01T00:00:00', createdById: 1 },
    ])
    window.confirm = vi.fn(() => true)
    groupService.deleteGroup.mockResolvedValue({})
    groupService.fetchGroups.mockResolvedValue([])

    await wrapper.find('[data-testid="delete-group-btn"]').trigger('click')
    await flushPromises()

    expect(window.confirm).toHaveBeenCalled()
    expect(groupService.deleteGroup).toHaveBeenCalledWith(5)
    // The row itself is gone (list refreshed to empty) — the deleted
    // group's name legitimately still appears once, inside the success
    // snackbar's own message.
    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.text()).toContain('No groups yet')
  })

  it('does not delete when the confirmation dialog is dismissed', async () => {
    const { wrapper } = await mountGroups('Administrator', [
      { id: 5, name: 'Keep Me', createdAt: '2026-01-01T00:00:00', createdById: 1 },
    ])
    window.confirm = vi.fn(() => false)

    await wrapper.find('[data-testid="delete-group-btn"]').trigger('click')
    await flushPromises()

    expect(groupService.deleteGroup).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Keep Me')
  })

  it('handles a network/server error on initial load without crashing', async () => {
    groupService.fetchGroups.mockRejectedValue(new Error('Network error'))
    const router = createTestRouter()
    await router.push('/groups')
    await router.isReady()
    const wrapper = mount(Groups, {
      global: {
        provide: { roleStore: makeRoleStore('Administrator') },
        plugins: [router],
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Network error')
    // Page remains usable — the Create action is still rendered.
    expect(wrapper.find('[data-testid="create-group-btn"]').exists()).toBe(true)
  })
})

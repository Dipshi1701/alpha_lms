import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CourseAssignModal from '../CourseAssignModal.vue'

const LEARNERS = [
  { id: 1, name: 'Rahul', role: 'Learner' }, // no group
  { id: 2, name: 'Amit', role: 'Learner' }, // in Group X
  { id: 3, name: 'Priya', role: 'Learner' }, // in Group X + Group Y
]

const GROUPS = [
  { id: 10, name: 'Group X' },
  { id: 20, name: 'Group Y' },
]

function mountModal(props = {}) {
  return mount(CourseAssignModal, {
    props: {
      open: true,
      courseTitle: 'Angular Basics',
      users: LEARNERS,
      initialAssignedUserIds: [],
      canAssignToGroup: true,
      groups: GROUPS,
      groupsLoading: false,
      groupsLoadError: '',
      saving: false,
      ...props,
    },
  })
}

describe('CourseAssignModal.vue', () => {
  it('renders Individual Learner mode by default with the full eligible learner list', () => {
    const wrapper = mountModal()
    expect(wrapper.find('[data-testid="assign-mode-individual"]').element.checked).toBe(true)
    // All three learners are shown regardless of (hypothetical) group membership —
    // the component never filters `users` by group at all.
    expect(wrapper.text()).toContain('Rahul')
    expect(wrapper.text()).toContain('Amit')
    expect(wrapper.text()).toContain('Priya')
  })

  it('hides the Group mode option entirely when canAssignToGroup is false', () => {
    const wrapper = mountModal({ canAssignToGroup: false })
    expect(wrapper.find('[data-testid="assign-mode-group"]').exists()).toBe(false)
  })

  it('shows the Group mode option when canAssignToGroup is true', () => {
    const wrapper = mountModal()
    expect(wrapper.find('[data-testid="assign-mode-group"]').exists()).toBe(true)
  })

  it('switching to Group mode hides the learner list and shows the group list', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    expect(wrapper.find('[data-testid="assign-learner-1"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="assign-group-10"]').exists()).toBe(true)
  })

  it('switching Individual -> Group clears learner selections so they are not submitted with the group assignment', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-testid="assign-learner-1"]').trigger('click')
    await wrapper.find('[data-testid="assign-learner-2"]').trigger('click')
    // Now switch to Group and pick a group, then submit.
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-group-10"]').trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')

    const emitted = wrapper.emitted('save')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0]).toEqual({ mode: 'group', groupId: 10 })
  })

  it('switching Group -> Individual restores the real current assignment state, dropping any group pick', async () => {
    const wrapper = mountModal({ initialAssignedUserIds: [2] })
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-group-10"]').trigger('click')
    await wrapper.find('[data-testid="assign-mode-individual"]').setValue(true)
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')

    const emitted = wrapper.emitted('save')
    expect(emitted[0][0]).toEqual({ mode: 'individual', assignedUserIds: [2] })
  })

  it('toggling a learner and submitting emits the individual assignment payload', async () => {
    // Mirrors real usage: the parent always mounts the modal closed, then
    // flips `open` to true once the target course (and its current
    // assignments) is known — matching AdminInstructorCourses.vue's
    // openAssignModal().
    const wrapper = mountModal({ open: false, initialAssignedUserIds: [] })
    await wrapper.setProps({ open: true, initialAssignedUserIds: [1] })
    await wrapper.find('[data-testid="assign-learner-3"]').trigger('click') // add Priya
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')

    const emitted = wrapper.emitted('save')
    expect(emitted[0][0].mode).toBe('individual')
    expect(emitted[0][0].assignedUserIds.sort()).toEqual([1, 3])
  })

  it('un-toggling an already-assigned learner removes them from the submitted payload', async () => {
    const wrapper = mountModal({ open: false, initialAssignedUserIds: [] })
    await wrapper.setProps({ open: true, initialAssignedUserIds: [1, 2] })
    await wrapper.find('[data-testid="assign-learner-2"]').trigger('click') // remove Amit
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')

    expect(wrapper.emitted('save')[0][0].assignedUserIds).toEqual([1])
  })

  it('selecting a group and submitting emits the group assignment payload', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-group-20"]').trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')

    expect(wrapper.emitted('save')[0][0]).toEqual({ mode: 'group', groupId: 20 })
  })

  it('blocks submission in Group mode when no group is selected and shows a validation message', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')

    expect(wrapper.emitted('save')).toBeUndefined()
    expect(wrapper.text()).toContain('Select a group')
  })

  it('shows an empty state when there are no eligible learners', () => {
    const wrapper = mountModal({ users: [] })
    expect(wrapper.text()).toContain('No eligible learners found')
  })

  it('shows an empty state when there are no groups available', async () => {
    const wrapper = mountModal({ groups: [] })
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    expect(wrapper.text()).toContain('No groups available')
  })

  it('shows a loading state while groups are being fetched', async () => {
    const wrapper = mountModal({ groupsLoading: true })
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    expect(wrapper.text()).toContain('Loading groups')
    expect(wrapper.find('[data-testid="assign-group-10"]').exists()).toBe(false)
  })

  it('shows the actual group-load error message when groups fail to load', async () => {
    const wrapper = mountModal({ groupsLoadError: 'Failed to load groups' })
    await wrapper.find('[data-testid="assign-mode-group"]').setValue(true)
    expect(wrapper.text()).toContain('Failed to load groups')
  })

  it('disables the submit/cancel controls while saving (prevents double submission)', () => {
    const wrapper = mountModal({ saving: true })
    expect(wrapper.find('[data-testid="assign-submit-btn"]').attributes('disabled')).toBeDefined()
  })

  it('re-opening the modal for a course always resets to Individual mode with that course\'s current assignments', async () => {
    const wrapper = mountModal({ open: false, initialAssignedUserIds: [] })
    await wrapper.setProps({ open: true, initialAssignedUserIds: [3] })
    expect(wrapper.find('[data-testid="assign-mode-individual"]').element.checked).toBe(true)
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    expect(wrapper.emitted('save')[0][0]).toEqual({ mode: 'individual', assignedUserIds: [3] })
  })

  // ── G012: duplicate-prevention + Assigned/Due/Source display ────────────

  const LEARNER_ASSIGNMENTS = [
    {
      userId: 1,
      assignedAt: '2026-09-10T00:00:00',
      dueDate: '2026-09-17T00:00:00',
      source: 'individual',
      sourceGroupName: null,
    },
    {
      userId: 2,
      assignedAt: '2026-09-12T00:00:00',
      dueDate: '2026-09-19T00:00:00',
      source: 'group',
      sourceGroupName: 'Group X',
    },
  ]

  it('shows "Already assigned individually" for an individually-sourced learner and keeps them toggleable', async () => {
    // Mount closed then open (see "toggling a learner..." above) -- the
    // form.assignedUserIds watch only fires on a real open transition.
    const wrapper = mountModal({ open: false, initialAssignedUserIds: [] })
    await wrapper.setProps({
      open: true,
      initialAssignedUserIds: [1, 2],
      learnerAssignments: LEARNER_ASSIGNMENTS,
    })
    const info = wrapper.find('[data-testid="assign-learner-1-info"]')
    expect(info.text()).toContain('Already assigned individually')

    const button = wrapper.find('[data-testid="assign-learner-1"]')
    expect(button.attributes('disabled')).toBeUndefined()
    expect(button.text()).toContain('Assigned')

    // Still the existing supported unassign flow: un-toggling removes them.
    await button.trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    expect(wrapper.emitted('save')[0][0].assignedUserIds).toEqual([2])
  })

  it('locks a group-sourced learner (cannot be un-toggled from the Individual list) and shows the group name', async () => {
    const wrapper = mountModal({ open: false, initialAssignedUserIds: [] })
    await wrapper.setProps({
      open: true,
      initialAssignedUserIds: [1, 2],
      learnerAssignments: LEARNER_ASSIGNMENTS,
    })
    const info = wrapper.find('[data-testid="assign-learner-2-info"]')
    expect(info.text()).toContain('Already assigned via group: Group X')

    const button = wrapper.find('[data-testid="assign-learner-2"]')
    expect(button.attributes('disabled')).toBeDefined()
    expect(button.text()).toContain('Locked')

    // Clicking a locked control must not remove them from the submitted set.
    await button.trigger('click')
    await wrapper.find('[data-testid="assign-submit-btn"]').trigger('click')
    expect(wrapper.emitted('save')[0][0].assignedUserIds.sort()).toEqual([1, 2])
  })

  it('shows a normal, unannotated Assign button for a learner with no existing assignment for this course', () => {
    const wrapper = mountModal({
      initialAssignedUserIds: [1],
      learnerAssignments: [LEARNER_ASSIGNMENTS[0]], // only learner 1 has an entry
    })
    expect(wrapper.find('[data-testid="assign-learner-2-info"]').exists()).toBe(false)
    const button = wrapper.find('[data-testid="assign-learner-2"]')
    expect(button.attributes('disabled')).toBeUndefined()
    expect(button.text()).toContain('Assign')
  })

  it('defaults learnerAssignments to empty and shows no lock/info state when the prop is omitted', () => {
    const wrapper = mountModal({ initialAssignedUserIds: [1] })
    expect(wrapper.find('[data-testid="assign-learner-1-info"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="assign-learner-1"]').attributes('disabled')).toBeUndefined()
  })
})

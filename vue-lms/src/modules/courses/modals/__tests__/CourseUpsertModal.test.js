import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CourseUpsertModal from '../CourseUpsertModal.vue'

const CATEGORIES = ['All', 'General', 'Sales']

// The component only (re-)populates `form` from `initialValue` inside a
// `watch([open, initialValue])` callback, which never fires on the very
// first render (no prior value to diff against). So every test mounts
// closed with the desired initialValue already in place, then opens via
// setProps -- mirroring how the real parent component
// (AdminInstructorCourses.vue) always toggles `open` from false to true.
async function mountModal({ open = true, ...props } = {}) {
  const wrapper = mount(CourseUpsertModal, {
    props: {
      open: false,
      mode: 'edit', // 'edit' mode skips the SCORM-file-required rule, keeping these tests focused on duration
      categories: CATEGORIES,
      initialValue: { title: 'Angular Basics', description: 'A short description' },
      saving: false,
      ...props,
    },
  })
  if (open) await wrapper.setProps({ open: true })
  return wrapper
}

function findSaveButton(wrapper) {
  return wrapper.findAll('button').find((b) => /Save changes|Create course/.test(b.text()))
}

describe('CourseUpsertModal.vue — Assignment Duration (G012)', () => {
  it('renders the Assignment Duration field with a default of 7 days on create', async () => {
    const wrapper = await mountModal({ mode: 'create', initialValue: {} })
    const input = wrapper.find('[data-testid="course-assignment-duration-input"]')
    expect(input.exists()).toBe(true)
    expect(input.element.value).toBe('7')
    expect(wrapper.text()).toContain('7 days from the date they are assigned')
  })

  it('pre-fills the field from initialValue.assignmentDurationDays on edit', async () => {
    const wrapper = await mountModal({ open: false, initialValue: { title: 'Angular Basics', description: 'x', assignmentDurationDays: 14 } })
    await wrapper.setProps({ open: true })
    expect(wrapper.find('[data-testid="course-assignment-duration-input"]').element.value).toBe('14')
  })

  it.each([
    ['0', 'must be 1 or more days'],
    ['-1', 'must be 1 or more days'],
    ['-7', 'must be 1 or more days'],
    ['3.5', 'whole number of days'],
    // Non-numeric text can't actually be entered into a type="number" input --
    // the browser (and jsdom) resets the value to '' instead, so it surfaces
    // as the same "required" error as leaving it blank.
    ['abc', 'required'],
    ['', 'required'],
  ])('rejects an invalid duration value "%s" and blocks saving', async (value, expectedMessage) => {
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="course-assignment-duration-input"]').setValue(value)
    await findSaveButton(wrapper).trigger('click')

    expect(wrapper.emitted('save')).toBeUndefined()
    expect(wrapper.text()).toContain(expectedMessage)
  })

  it.each([1, 7, 30])('accepts a valid duration value %i and includes it in the saved payload', async (value) => {
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="course-assignment-duration-input"]').setValue(String(value))
    await findSaveButton(wrapper).trigger('click')

    const emitted = wrapper.emitted('save')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0].assignmentDurationDays).toBe(value)
  })

  it('disables the duration input while saving', async () => {
    const wrapper = await mountModal({ saving: true })
    expect(wrapper.find('[data-testid="course-assignment-duration-input"]').attributes('disabled')).toBeDefined()
  })

  it('resets to the initial value each time the modal is re-opened', async () => {
    const wrapper = await mountModal({ open: false, initialValue: { title: 'A', description: 'x', assignmentDurationDays: 21 } })
    await wrapper.setProps({ open: true })
    expect(wrapper.find('[data-testid="course-assignment-duration-input"]').element.value).toBe('21')

    await wrapper.setProps({ open: false })
    await wrapper.setProps({ open: true, initialValue: { title: 'B', description: 'y', assignmentDurationDays: 3 } })
    expect(wrapper.find('[data-testid="course-assignment-duration-input"]').element.value).toBe('3')
  })
})

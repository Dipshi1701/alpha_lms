import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import LearnerCourses from '../LearnerCourses.vue'
import * as courseService from '../../service'

vi.mock('../../service')

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/courses/:courseId/play', name: 'course-player', component: { template: '<div />' } },
    ],
  })
}

const BASE_COURSE = {
  id: 1,
  title: 'Angular Basics',
  category: 'General',
  content_type: 'scorm12',
  description: 'Learn Angular',
}

async function mountPage(courses) {
  courseService.fetchMyCoursesLearner.mockResolvedValue(courses)
  courseService.fetchMyProgress.mockResolvedValue({})

  const router = makeRouter()
  await router.push('/')
  await router.isReady()
  const wrapper = mount(LearnerCourses, { global: { plugins: [router] } })
  await flushPromises()
  return wrapper
}

// The page header's filter <select> also carries a `cursor-pointer` class,
// so target the card's own "View Course" button (which also opens the
// overview modal) rather than a generic `.cursor-pointer` selector.
function findViewCourseButton(wrapper) {
  return wrapper.findAll('button').find((b) => b.text().includes('View Course'))
}

describe('LearnerCourses.vue — Assigned/Due display (G012 PART 15)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  // The overview modal renders via <Teleport to="body">, which survives past
  // wrapper.unmount() only if the source component is actually torn down --
  // do that explicitly so teleported nodes never leak into the next test.
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('shows Assigned/Due chips in the course overview modal when learnerAssignments has an entry', async () => {
    const wrapper = await mountPage([
      {
        ...BASE_COURSE,
        learnerAssignments: [
          {
            userId: 5,
            assignedAt: '2026-09-20T00:00:00',
            dueDate: '2026-09-27T00:00:00',
            source: 'individual',
            sourceGroupName: null,
          },
        ],
      },
    ])

    await findViewCourseButton(wrapper).trigger('click')
    await flushPromises()

    // The overview modal is rendered via <Teleport to="body">, so it lands
    // in document.body rather than inside wrapper.element.
    expect(document.body.textContent).toContain('Assigned')
    expect(document.body.textContent).toContain('Due')
  })

  it('does not render Assigned/Due chips when the course has no learnerAssignments entry', async () => {
    const wrapper = await mountPage([{ ...BASE_COURSE, learnerAssignments: [] }])

    await findViewCourseButton(wrapper).trigger('click')
    await flushPromises()

    // "About this Course" heading is always present; Assigned/Due should not be.
    expect(document.body.textContent).toContain('About this Course')
    expect(document.body.textContent).not.toContain('Assigned ')
  })
})

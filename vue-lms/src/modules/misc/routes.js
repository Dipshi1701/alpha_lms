import StubPage from './views/StubPage.vue'

export const miscRoutes = [
  {
    path: 'conferences',
    component: StubPage,
    props: { title: 'Conferences' },
  },
  {
    path: 'calendar',
    component: StubPage,
    props: { title: 'Calendar' },
  },
  {
    path: 'catalog',
    component: StubPage,
    props: { title: 'Catalog' },
  },
  {
    path: 'skills',
    component: StubPage,
    props: { title: 'Skills' },
  },
  {
    path: 'course-store',
    component: StubPage,
    props: { title: 'Course Store' },
  },
]


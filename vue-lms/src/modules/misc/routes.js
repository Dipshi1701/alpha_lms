import StubPage from './views/StubPage.vue'
import CalendarView from './views/CalendarView.vue'
import CatalogView from './views/CatalogView.vue'

export const miscRoutes = [
  {
    path: 'conferences',
    component: StubPage,
    props: { title: 'Conferences' },
  },
  {
    path: 'calendar',
    component: CalendarView,
  },
  {
    path: 'catalog',
    component: CatalogView,
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


import { reactive } from 'vue'
import { createRouter, createMemoryHistory } from 'vue-router'

/**
 * Minimal roleStore stand-in for provide('roleStore', ...) — mirrors the
 * real shape from src/stores/roleStore.js closely enough for useAccess()
 * (the real composable, unmocked) to compute isAdmin/isInstructor/isLearner
 * correctly in tests.
 */
export function makeRoleStore(role) {
  return {
    state: reactive({
      role,
      availableRoles: role ? [role] : [],
      user: role ? { id: 1, full_name: 'Test User', email: 'test@example.com' } : null,
    }),
  }
}

/** A tiny in-memory router with just the routes Groups/GroupDetail use. */
export function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/groups', name: 'groups', component: { template: '<div />' } },
      { path: '/groups/:groupId', name: 'group-detail', component: { template: '<div />' } },
    ],
  })
}

import { get, post } from '../../api/api'

export function fetchUsers() {
  return get('/api/users')
}

export function createUser(payload) {
  return post('/api/users', payload)
}

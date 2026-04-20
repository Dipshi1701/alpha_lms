import { get, post } from '../../api/api'

export function login(credentials) {
  return post('/api/auth/login', credentials, {}, { skipAuth: true })
}

export function getMyProfile() {
  return get('/api/auth/me')
}

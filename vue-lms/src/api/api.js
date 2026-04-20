import { request } from './httpClient'

export function get(path, requestOptions = {}, requestMeta = {}) {
  return request(path, { method: 'GET', ...requestOptions }, requestMeta)
}

export function post(path, requestBody, requestOptions = {}, requestMeta = {}) {
  return request(
    path,
    {
      method: 'POST',
      body: JSON.stringify(requestBody),
      ...requestOptions,
    },
    requestMeta
  )
}

export function put(path, requestBody, requestOptions = {}, requestMeta = {}) {
  return request(
    path,
    {
      method: 'PUT',
      body: JSON.stringify(requestBody),
      ...requestOptions,
    },
    requestMeta
  )
}

export function patch(path, requestBody, requestOptions = {}, requestMeta = {}) {
  return request(
    path,
    {
      method: 'PATCH',
      body: JSON.stringify(requestBody),
      ...requestOptions,
    },
    requestMeta
  )
}

export function remove(path, requestOptions = {}, requestMeta = {}) {
  return request(path, { method: 'DELETE', ...requestOptions }, requestMeta)
}

export function postForm(path, formData, requestOptions = {}, requestMeta = {}) {
  return request(
    path,
    {
      method: 'POST',
      body: formData,
      ...requestOptions,
    },
    { ...requestMeta, isFormData: true }
  )
}

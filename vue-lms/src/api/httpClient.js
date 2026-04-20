const requestInterceptors = []
const responseInterceptors = []

export function addRequestInterceptor(interceptor) {
  requestInterceptors.push(interceptor)
}

export function addResponseInterceptor(onSuccess, onError) {
  responseInterceptors.push({ onSuccess, onError })
}

function getAccessToken() {
  if (typeof localStorage === 'undefined') return null
  return localStorage.getItem('access_token')
}

function clearSessionAndRedirectToLogin() {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('access_token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('userData')
    localStorage.removeItem('availableRoles')
  }

  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export function apiUrl(path) {
  const baseUrl = import.meta.env.VITE_API_URL || ''
  if (path.startsWith('http')) return path
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${baseUrl}${normalizedPath}`
}

function parseErrorMessage(parsedResponse, statusText) {
  const detail =
    parsedResponse?.error?.detail ??
    parsedResponse?.detail ??
    parsedResponse?.message ??
    statusText

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || String(item)).join(', ')
  }
  return String(detail)
}

async function applyRequestInterceptors(requestConfig) {
  let nextConfig = requestConfig
  for (const interceptor of requestInterceptors) {
    nextConfig = await interceptor(nextConfig)
  }
  return nextConfig
}

async function applyResponseInterceptors(responseContext) {
  let nextContext = responseContext
  for (const interceptor of responseInterceptors) {
    if (nextContext.error && interceptor.onError) {
      nextContext = await interceptor.onError(nextContext)
    } else if (!nextContext.error && interceptor.onSuccess) {
      nextContext = await interceptor.onSuccess(nextContext)
    }
  }
  return nextContext
}

export async function request(path, options = {}, meta = {}) {
  const requestConfig = await applyRequestInterceptors({
    url: apiUrl(path),
    options,
    meta,
  })

  const response = await fetch(requestConfig.url, requestConfig.options)
  const responseText = await response.text()
  let parsedResponse = null
  if (responseText) {
    try {
      parsedResponse = JSON.parse(responseText)
    } catch {
      parsedResponse = responseText
    }
  }

  let error = null
  if (!response.ok) {
    error = new Error(parseErrorMessage(parsedResponse, response.statusText))
    error.status = response.status
    error.payload = parsedResponse
  }

  const finalContext = await applyResponseInterceptors({
    response,
    parsedResponse,
    error,
    meta: requestConfig.meta,
  })

  if (finalContext.error) {
    throw finalContext.error
  }

  if (
    finalContext.parsedResponse &&
    typeof finalContext.parsedResponse === 'object' &&
    Object.prototype.hasOwnProperty.call(finalContext.parsedResponse, 'success')
  ) {
    if (finalContext.parsedResponse.success === false) {
      throw new Error(finalContext.parsedResponse.message || 'Request failed')
    }
    return finalContext.parsedResponse.data
  }

  return finalContext.parsedResponse
}

addRequestInterceptor(async ({ url, options, meta }) => {
  const accessToken = getAccessToken()
  const headers = { ...(options.headers || {}) }

  if (!meta.skipAuth && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }

  if (!meta.isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  return {
    url,
    options: { ...options, headers },
    meta,
  }
})

addResponseInterceptor(
  async (context) => context,
  async (context) => {
    if (context.error?.status === 401 && !context.meta?.skipAuth) {
      clearSessionAndRedirectToLogin()
    }
    return context
  }
)

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAccess } from '../../../composables/useAccess'
import { login } from '../service'
import { Mail, Lock, AlertCircle } from 'lucide-vue-next'

const router = useRouter()
const { setUserData, setRole } = useAccess()

const form = reactive({
  email: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const data = await login({
      email: form.email.trim(),
      password: form.password
    })
    setUserData(data.user, data.roles, data.access_token)
    if (data.roles?.length) {
      setRole(data.roles[0])
    }
    router.push('/dashboard')
  } catch (err) {
    error.value = err?.message || 'Invalid email or password'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
      <!-- Logo/Header -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <span class="text-3xl font-black text-white">A</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-800">Welcome to Alpha Learn</h1>
        <p class="text-gray-500 text-sm mt-1">Sign in to continue</p>
      </div>
      
      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-5">
        <!-- Email Field -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">
            Email Address
          </label>
          <div class="relative">
            <Mail :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input 
              v-model="form.email" 
              type="email" 
              required
              placeholder="you@example.com"
              class="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <!-- Password Field -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">
            Password
          </label>
          <div class="relative">
            <Lock :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input 
              v-model="form.password" 
              type="password" 
              required
              placeholder="Enter your password"
              class="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <!-- Error Message -->
        <div 
          v-if="error" 
          class="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
        >
          <AlertCircle :size="16" class="flex-shrink-0" />
          <span>{{ error }}</span>
        </div>
        
        <!-- Submit Button -->
        <button 
          type="submit" 
          :disabled="loading"
          class="w-full py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>
      
    </div>
  </div>
</template>

<script setup>
import { provide, onMounted } from 'vue'
import { useAppStore } from './stores/appStore'
import { useRoleStore } from './stores/roleStore'
import { RouterView } from 'vue-router'
import { getMyProfile } from './modules/auth/service'

const appStore = useAppStore()
const roleStore = useRoleStore()

provide('appStore', appStore)
provide('roleStore', roleStore)

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (!token) return
  try {
    const data = await getMyProfile()
    const roles = data.roles || []
    roleStore.setUserData(data.user, roles, token)
    const saved = roleStore.state.role
    if (!saved || !roles.includes(saved)) {
      if (roles.length) roleStore.setRole(roles[0])
    }
  } catch {
    roleStore.clearRole()
  }
})
</script>

<template>
  <RouterView />
</template>


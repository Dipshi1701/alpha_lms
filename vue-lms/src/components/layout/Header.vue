<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Menu, Search, Bell, ChevronDown, X, Check, LogOut } from 'lucide-vue-next'
import clsx from 'clsx'
import { useAccess, ROLES } from '../../composables/useAccess'

const props = defineProps({
  onToggleSidebar: {
    type: Function,
    required: true
  }
})

const router = useRouter()
const { role, user, availableRoles, clearRole, setRole } = useAccess()

const displayName = computed(() => {
  const u = user.value
  if (!u) return 'User'
  return u.full_name || u.email || 'User'
})

const displayInitial = computed(() => {
  const n = displayName.value
  if (!n || n === 'User') return '?'
  return n.trim().charAt(0).toUpperCase()
})
// Single avatar + badge color for every role — consistent ASI purple identity.
const ROLE_COLORS      = 'bg-asi-purple'
const ROLE_BADGE_COLORS = 'bg-asi-purple-light text-asi-purple'

const searchVal = ref('')
const userOpen = ref(false)
const notifOpen = ref(false)
const dropRef = ref(null)

const handleOutside = (e) => {
  if (dropRef.value && !dropRef.value.contains(e.target)) {
    userOpen.value = false
    notifOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleOutside)
})

const handleRoleSwitch = (newRole) => {
  setRole(newRole)
  userOpen.value = false
}

const handleLogout = () => {
  clearRole()
  router.push('/login')
}
</script>

<template>
  <header class="h-16 bg-white border-b border-asi-border flex items-center px-4 gap-3 flex-shrink-0 z-30 relative">
    <button
      @click="props.onToggleSidebar"
      class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray transition-colors"
    >
      <Menu :size="20" />
    </button>

    <div class="flex-1 max-w-md">
      <div class="relative">
        <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-asi-gray" />
        <input
          v-model="searchVal"
          type="text"
          placeholder="Search"
          class="w-full pl-9 pr-4 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20 focus:border-asi-lavender transition-all text-asi-black"
        />
        <button
          v-if="searchVal"
          @click="searchVal = ''"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-asi-gray hover:text-asi-black"
        >
          <X :size="13" />
        </button>
      </div>
    </div>

    <div class="flex-1" />

    <div class="flex items-center gap-1" ref="dropRef">
      <div class="relative">
        <button
          @click="() => { notifOpen = !notifOpen; userOpen = false }"
          class="p-2 rounded-lg hover:bg-asi-surface text-asi-gray transition-colors relative"
        >
          <Bell :size="18" />
          <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-asi-red rounded-full" />
        </button>
        <div
          v-if="notifOpen"
          class="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-xl border border-asi-border z-50"
        >
          <div class="flex items-center justify-between px-4 py-3 border-b border-asi-border">
            <span class="text-sm font-semibold text-asi-black">Notifications</span>
            <button class="text-xs text-asi-purple font-medium hover:text-asi-red transition-colors">Mark all read</button>
          </div>
          <div class="py-2">
            <div
              v-for="(n, i) in [
                { msg: 'j. s completed Sales Techniques', time: '2m ago', unread: true },
                { msg: 'New user registered: alice@example.com', time: '1h ago', unread: true },
                { msg: 'Automation triggered: Course assigned', time: 'Yesterday', unread: false }
              ]"
              :key="i"
              :class="clsx(
                'flex items-start gap-3 px-4 py-3 hover:bg-asi-surface',
                n.unread ? 'bg-asi-purple-light/50' : ''
              )"
            >
              <div
                :class="clsx(
                  'w-2 h-2 rounded-full mt-1.5 flex-shrink-0',
                  n.unread ? 'bg-asi-red' : 'bg-gray-300'
                )"
              />
              <div>
                <p class="text-sm text-asi-black">{{ n.msg }}</p>
                <p class="text-xs text-asi-gray mt-0.5">{{ n.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="relative ml-1">
        <button
          @click="() => { userOpen = !userOpen; notifOpen = false }"
          class="flex items-center gap-2 cursor-pointer group pl-1"
        >
          <div
            :class="clsx(
              'w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-sm transition-colors',
              ROLE_COLORS
            )"
          >
            {{ displayInitial }}
          </div>
          <div class="hidden sm:block text-left">
            <div class="text-sm font-semibold text-asi-black leading-tight">{{ displayName }}</div>
            <div class="text-xs text-asi-gray leading-tight">{{ role }}</div>
          </div>
          <ChevronDown
            :size="14"
            :class="clsx(
              'text-asi-gray transition-transform',
              userOpen ? 'rotate-180' : ''
            )"
          />
        </button>

        <div
          v-if="userOpen"
          class="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-xl border border-asi-border z-50 overflow-hidden"
        >
          <div class="px-4 py-3 border-b border-asi-border bg-asi-surface">
            <div class="flex items-center gap-3">
              <div
              :class="clsx(
                'w-9 h-9 rounded-full flex items-center justify-center text-white font-bold',
                ROLE_COLORS
              )"
              >
                {{ displayInitial }}
              </div>
              <div>
                <p class="text-sm font-semibold text-asi-black">{{ displayName }}</p>
                <span
                  :class="clsx(
                    'text-xs font-medium px-2 py-0.5 rounded-full',
                    ROLE_BADGE_COLORS
                  )"
                >
                  {{ role }}
                </span>
              </div>
            </div>
          </div>

          <div class="px-4 pt-3 pb-2">
            <div class="space-y-1">
              <button
                v-for="r in availableRoles"
                :key="r"
                @click="() => handleRoleSwitch(r)"
                class="flex items-center gap-3 w-full px-2 py-2 rounded-lg hover:bg-asi-surface transition-colors group"
              >
                <div
                  :class="clsx(
                    'w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all',
                    role === r ? 'border-asi-orange bg-asi-orange' : 'border-gray-300 group-hover:border-asi-lavender'
                  )"
                >
                  <div
                    v-if="role === r"
                    class="w-1.5 h-1.5 bg-white rounded-full"
                  />
                </div>
                <span
                  :class="clsx(
                    'text-sm transition-colors',
                    role === r ? 'font-semibold text-asi-black' : 'text-asi-gray group-hover:text-asi-black'
                  )"
                >
                  {{ r }}
                </span>
                <Check
                  v-if="role === r"
                  :size="13"
                  class="ml-auto text-asi-orange"
                />
              </button>
            </div>
          </div>

          
          <div class="border-t border-asi-border py-1 px-2">
            <button 
              @click="handleLogout"
              class="flex items-center gap-2 w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut :size="14" />
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>


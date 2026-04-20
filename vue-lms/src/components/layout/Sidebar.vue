
<script setup>
import { computed, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import {
  ChevronRight,
  Trophy
} from 'lucide-vue-next'
import clsx from 'clsx'
import { useAccess, ROLES } from '../../composables/useAccess'
import { NAV_ITEMS, HELP_CENTER_ITEM } from '../../config/navigation'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

// Get current role and route
const { role } = useAccess()
const route = useRoute()

// --- COLORS / BRANDING PER ROLE ---
const BRAND_COLORS = {
  [ROLES.ADMIN]: 'bg-[#1a3a5c]',
  [ROLES.INSTRUCTOR]: 'bg-[#2d1b69]',
  [ROLES.LEARNER]: 'bg-[#0f4c75]'
}

const ICON_GRAD = {
  [ROLES.ADMIN]: 'from-blue-400 to-blue-600',
  [ROLES.INSTRUCTOR]: 'from-purple-400 to-purple-600',
  [ROLES.LEARNER]: 'from-teal-400 to-teal-600'
}

// --- FILTER NAV ITEMS BY CURRENT ROLE ---
// This automatically shows only items the current role can see
const navItems = computed(() => {
  return NAV_ITEMS.filter(item => {
    // If item has no roles array or empty array, everyone can see it
    if (!item.roles || item.roles.length === 0) return true
    // Otherwise check if current role is in the allowed list
    return item.roles.includes(role.value)
  })
})

// Check if help center should be shown (instructor + learner only)
const showHelpCenter = computed(() => {
  return HELP_CENTER_ITEM.roles.includes(role.value)
})

const bgColor = computed(() => BRAND_COLORS[role.value])
const iconGrad = computed(() => ICON_GRAD[role.value])

// Helper: is a route active
const isActive = (to) => {
  if (route.path === to) return true
  if (to !== '/dashboard' && route.path.startsWith(to)) return true
  return false
}

// --- SIMPLE SUBMENU STATE (WORKS FOR ANY ITEM WITH CHILDREN) ---
const openSubmenu = ref(null)

const toggleSubmenu = (itemLabel) => {
  if (openSubmenu.value === itemLabel) {
    openSubmenu.value = null  // Close if already open
  } else {
    openSubmenu.value = itemLabel  // Open this one
  }
}
</script>

<template>
  <aside
    :class="clsx(
      'flex flex-col h-screen text-white transition-all duration-300 flex-shrink-0',
      bgColor,
      props.collapsed ? 'w-16' : 'w-56'
    )"
  >
    <!-- Logo / Brand -->
    <div class="flex items-center gap-2.5 px-4 h-14 border-b border-white/10 flex-shrink-0">
      <div
        v-if="props.collapsed"
        :class="`w-8 h-8 rounded-lg bg-gradient-to-br ${iconGrad} flex items-center justify-center font-black text-white text-base mx-auto select-none`"
      >
        A
      </div>
      <div v-else class="flex items-center gap-2.5">
        <div
          :class="`w-8 h-8 rounded-lg bg-gradient-to-br ${iconGrad} flex items-center justify-center font-black text-white text-base select-none`"
        >
          A
        </div>
        <span class="font-extrabold text-white text-base tracking-tight leading-none">
          Alpha<span class="opacity-70"> Learn</span>
        </span>
      </div>
    </div>

    <!-- Role badge -->
    <div v-if="!props.collapsed" class="px-4 py-2 border-b border-white/10">
      <span class="text-xs font-semibold bg-white/15 text-white/80 px-2.5 py-1 rounded-full">
        {{ role }}
      </span>
    </div>

    <!-- MAIN NAV (role-filtered automatically) -->
    <nav class="flex-1 overflow-y-auto py-2">
      <!-- Wrap each item in a div so we can put submenu below it -->
      <div v-for="item in navItems" :key="item.to">
        <!-- Main menu row -->
        <RouterLink
          :to="item.to"
          :title="props.collapsed ? item.label : undefined"
          :class="clsx(
            'flex items-center gap-3 px-3 py-2.5 mx-2 my-0.5 rounded-lg text-sm font-medium transition-all duration-150',
            isActive(item.to)
              ? 'bg-white/20 text-white'
              : 'text-white/70 hover:bg-white/10 hover:text-white'
          )"
          @click.prevent="
            item.children && item.children.length > 0
              ? toggleSubmenu(item.label)
              : null
          "
        >
          <component :is="item.icon" :size="17" class="flex-shrink-0" />
          <template v-if="!props.collapsed">
            <span class="flex-1 truncate">{{ item.label }}</span>
            <span
              v-if="item.badge"
              class="flex items-center gap-0.5 text-xs bg-white/20 text-white px-1.5 py-0.5 rounded-full flex-shrink-0"
            >
              <Trophy :size="9" />
              {{ item.badge }}
            </span>
            <ChevronRight
              v-if="item.arrow"
              :size="13"
              class="text-white/40 flex-shrink-0"
            />
          </template>
        </RouterLink>

        <!-- Submenu (if item has children and is open) -->
        <div
          v-if="
            !props.collapsed &&
            item.children &&
            item.children.length > 0 &&
            openSubmenu === item.label
          "
          class="ml-10 mt-1 space-y-1 mb-2"
        >
          <RouterLink
            v-for="child in item.children"
            :key="child.to"
            :to="child.to"
            class="block text-xs text-white/70 hover:text-white py-1 px-3"
          >
            {{ child.label }}
          </RouterLink>
        </div>
      </div>
    </nav>

    <!-- Help Center (instructor + learner only) -->
    <div v-if="showHelpCenter" class="border-t border-white/10 py-2">
      <RouterLink
        :to="HELP_CENTER_ITEM.to"
        :title="props.collapsed ? HELP_CENTER_ITEM.label : undefined"
        class="flex items-center gap-3 px-3 py-2.5 mx-2 rounded-lg text-sm font-medium text-white/60 hover:bg-white/10 hover:text-white transition-all"
      >
        <component :is="HELP_CENTER_ITEM.icon" :size="17" class="flex-shrink-0" />
        <template v-if="!props.collapsed">
          <span class="flex-1">{{ HELP_CENTER_ITEM.label }}</span>
          <ChevronRight :size="13" class="text-white/40" />
        </template>
      </RouterLink>
    </div>

    <!-- Footer -->
    <div v-if="!props.collapsed" class="px-4 py-3 border-t border-white/10 flex-shrink-0">
      <p class="text-xs text-white/30 text-center">Alpha Learn</p>
    </div>
  </aside>
</template>

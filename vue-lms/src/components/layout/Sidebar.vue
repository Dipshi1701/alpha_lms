
<script setup>
import { computed, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { ChevronRight, Trophy } from 'lucide-vue-next'
import clsx from 'clsx'
import { useAccess } from '../../composables/useAccess'
import { NAV_ITEMS, HELP_CENTER_ITEM } from '../../config/navigation'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const { role } = useAccess()
const route   = useRoute()

// ── Role accent stripe (left border on active item) ──────────────────────────
// Same accent for every role — consistent ASI orange across the board.
const roleAccent = 'bg-asi-orange'

const navItems = computed(() =>
  NAV_ITEMS.filter(item =>
    !item.roles || item.roles.length === 0 || item.roles.includes(role.value)
  )
)

const showHelpCenter = computed(() =>
  HELP_CENTER_ITEM.roles.includes(role.value)
)

const isActive = (to) => {
  if (route.path === to) return true
  if (to !== '/dashboard' && route.path.startsWith(to)) return true
  return false
}

const openSubmenu = ref(null)
const toggleSubmenu = (label) => {
  openSubmenu.value = openSubmenu.value === label ? null : label
}
</script>

<template>
  <!-- ASI purple sidebar — consistent across every role -->
  <aside
    :class="clsx(
      'flex flex-col h-screen bg-asi-purple text-white transition-all duration-300 flex-shrink-0',
      props.collapsed ? 'w-16' : 'w-56'
    )"
  >
    <!-- ── Logo ─────────────────────────────────────────────────────────── -->
    <div class="flex items-center justify-center bg-white border-b border-asi-border flex-shrink-0"
         :class="props.collapsed ? 'h-16 px-4' : 'h-16 px-4'">
      <img
        v-if="props.collapsed"
        src="../../assets/circle_logo.png"
        alt="Logo"
        class="h-8 w-8 object-contain"
      />
      <img
        v-else
        src="../../assets/alphalogo.png"
        alt="Alphanumeric"
        class="h-10 w-auto object-contain max-w-[160px]"
      />
    </div>

    <!-- ── Role badge ────────────────────────────────────────────────────── -->
   

    <!-- ── Main nav ──────────────────────────────────────────────────────── -->
    <nav class="flex-1 overflow-y-auto py-2">
      <div v-for="item in navItems" :key="item.to || item.label">

        <!-- Disabled item (greyed out, not clickable) -->
        <div
          v-if="item.disabled"
          :title="props.collapsed ? item.label : undefined"
          class="flex items-center gap-3 px-3 py-2.5 mx-2 my-0.5 rounded-lg text-sm font-medium cursor-not-allowed select-none opacity-30"
        >
          <component :is="item.icon" :size="17" class="flex-shrink-0" />
          <span v-if="!props.collapsed" class="flex-1 truncate">{{ item.label }}</span>
        </div>

        <!-- Active/normal item -->
        <RouterLink
          v-else
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
          <!-- accent stripe for active item -->
          <span
            v-if="isActive(item.to) && !props.collapsed"
            :class="['absolute left-0 w-0.5 h-6 rounded-r-full', roleAccent]"
          />

          <component :is="item.icon" :size="17" class="flex-shrink-0" />
          <template v-if="!props.collapsed">
            <span class="flex-1 truncate">{{ item.label }}</span>
            <span
              v-if="item.badge"
              class="flex items-center gap-0.5 text-[10px] bg-white/20 text-white px-1.5 py-0.5 rounded-full flex-shrink-0"
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

        <!-- Submenu (only for non-disabled items) -->
        <div
          v-if="!item.disabled && !props.collapsed && item.children?.length && openSubmenu === item.label"
          class="ml-10 mt-1 space-y-1 mb-2"
        >
          <RouterLink
            v-for="child in item.children"
            :key="child.to"
            :to="child.to"
            class="block text-xs text-white/70 hover:text-white py-1 px-3 rounded-lg hover:bg-white/10 transition-colors"
          >
            {{ child.label }}
          </RouterLink>
        </div>
      </div>
    </nav>

    <!-- ── Footer ────────────────────────────────────────────────────────── -->
    <div v-if="!props.collapsed" class="px-4 py-3 border-t border-white/10 flex-shrink-0">
      <p class="text-[11px] text-white/30 text-center">© Alphanumeric</p>
    </div>
  </aside>
</template>

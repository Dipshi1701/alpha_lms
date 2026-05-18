<script setup>
import { ref } from 'vue'
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'
import { RouterView } from 'vue-router'

const collapsed = ref(false)

const toggle = () => {
  collapsed.value = !collapsed.value
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">
    <Sidebar :collapsed="collapsed" />
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <Header :onToggleSidebar="toggle" />
      <main class="flex-1 overflow-y-auto">
        <RouterView />
      </main>
      <footer class="py-3 text-center text-xs text-asi-gray bg-white border-t border-asi-border">
        Powered by <span class="font-semibold text-asi-purple">Alphanumeric Innovation</span>
      </footer>
    </div>
  </div>
</template>


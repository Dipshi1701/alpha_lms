<script setup>
import { ChevronRight } from 'lucide-vue-next'

const events = [
  { actor: 'You', action: 'signed in', time: '43 minutes ago', color: '#462C6B', self: true },
  { actor: 'You', action: 'signed in', time: 'Yesterday',      color: '#462C6B', self: true },
  { actor: 'j. s', action: 'unlocked the', highlight: 'Certification Newbie', suffix: 'badge', time: 'Yesterday', color: '#CA1F47' },
  { actor: 'j. s', action: 'was awarded a certificate for the course', highlight: 'Wha...', time: 'Yesterday', color: '#F26524' },
  { actor: 'j. s', action: 'unlocked the', highlight: 'Learning Newbie', suffix: 'badge', time: 'Yesterday', color: '#4890C0' },
]
</script>

<template>
  <div class="widget-card">
    <div class="flex items-center gap-1 cursor-pointer group mb-4">
      <h3 class="text-base font-semibold text-asi-black group-hover:text-asi-purple transition-colors">
        Timeline
      </h3>
      <ChevronRight :size="16" class="text-asi-gray group-hover:text-asi-lavender transition-colors" />
    </div>

    <div class="space-y-0 max-h-64 overflow-y-auto -mx-1 px-1">
      <div
        v-for="(event, index) in events"
        :key="index"
        class="flex items-start gap-3 py-2.5 border-b border-asi-border/50 last:border-0"
      >
        <div
          class="w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0"
          :style="{ backgroundColor: event.color }"
        />
        <div class="flex-1 min-w-0">
          <p class="text-sm text-asi-black leading-snug">
            <span class="font-medium">{{ event.actor }}</span>
            <span class="text-asi-gray">{{ ' ' + event.action }}</span>
            <template v-if="event.highlight">
              <span class="font-semibold italic text-asi-black">{{ ' ' + event.highlight }}</span>
            </template>
            <template v-if="event.suffix">
              <span class="text-asi-gray">{{ ' ' + event.suffix }}</span>
            </template>
          </p>
        </div>
        <span class="text-xs text-asi-gray/70 flex-shrink-0 mt-0.5">{{ event.time }}</span>
      </div>
    </div>
  </div>
</template>

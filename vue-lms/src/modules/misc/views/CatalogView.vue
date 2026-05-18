<script setup>
import { ref, computed } from 'vue'
import {
  Search, BookOpen, Star, Clock, Users,
  ChevronRight, ChevronDown, X, Award,
  Heart, Tag, GraduationCap
} from 'lucide-vue-next'

const CATALOG = [
  {
    id: 1,
    title: 'Workplace Safety & Compliance',
    description: 'Learn essential workplace safety regulations and how to stay compliant with national standards.',
    category: 'compliance',
    duration: '2h 30m',
    enrolled: 1240,
    rating: 4.8,
    level: 'Beginner',
    tags: ['Safety', 'Regulation'],
    new: false,
    accent: '#462C6B',
    iconBg: 'bg-gradient-to-br from-[#462C6B] to-[#7D6B9D]',
  },
  {
    id: 2,
    title: 'Cybersecurity Awareness',
    description: 'Protect your organisation from modern cyber threats with hands-on security training.',
    category: 'it',
    duration: '3h 15m',
    enrolled: 980,
    rating: 4.9,
    level: 'Intermediate',
    tags: ['Cyber', 'Phishing'],
    new: true,
    accent: '#1a73e8',
    iconBg: 'bg-gradient-to-br from-blue-500 to-blue-700',
  },
  {
    id: 3,
    title: 'Effective Communication',
    description: 'Build confidence in written and verbal communication for professional environments.',
    category: 'soft',
    duration: '1h 45m',
    enrolled: 2100,
    rating: 4.7,
    level: 'Beginner',
    tags: ['Communication', 'Presentation'],
    new: false,
    accent: '#059669',
    iconBg: 'bg-gradient-to-br from-emerald-500 to-teal-600',
  },
  {
    id: 4,
    title: 'Leadership Essentials',
    description: 'Develop the leadership skills needed to inspire teams and drive results.',
    category: 'management',
    duration: '4h 00m',
    enrolled: 870,
    rating: 4.6,
    level: 'Advanced',
    tags: ['Leadership', 'Strategy'],
    new: false,
    accent: '#d97706',
    iconBg: 'bg-gradient-to-br from-amber-500 to-orange-600',
  },
  {
    id: 5,
    title: 'Diversity & Inclusion',
    description: 'Foster an inclusive culture and understand the value of diverse perspectives.',
    category: 'hr',
    duration: '2h 00m',
    enrolled: 3200,
    rating: 4.8,
    level: 'Beginner',
    tags: ['DEI', 'Culture'],
    new: false,
    accent: '#CA1F47',
    iconBg: 'bg-gradient-to-br from-pink-500 to-[#CA1F47]',
  },
  {
    id: 6,
    title: 'Financial Risk Management',
    description: 'Understand risk frameworks, financial exposure and mitigation strategies.',
    category: 'finance',
    duration: '3h 30m',
    enrolled: 560,
    rating: 4.5,
    level: 'Intermediate',
    tags: ['Risk', 'Finance'],
    new: true,
    accent: '#7c3aed',
    iconBg: 'bg-gradient-to-br from-violet-500 to-purple-700',
  },
  {
    id: 7,
    title: 'Data Privacy Fundamentals',
    description: 'Master GDPR, data handling and privacy-by-design principles.',
    category: 'compliance',
    duration: '2h 15m',
    enrolled: 1890,
    rating: 4.9,
    level: 'Beginner',
    tags: ['GDPR', 'Privacy'],
    new: false,
    accent: '#0891b2',
    iconBg: 'bg-gradient-to-br from-cyan-500 to-blue-600',
  },
  {
    id: 8,
    title: 'Project Management Basics',
    description: 'Get up to speed on Agile, Waterfall and hybrid PM methodologies.',
    category: 'management',
    duration: '5h 00m',
    enrolled: 1430,
    rating: 4.7,
    level: 'Intermediate',
    tags: ['Agile', 'Scrum'],
    new: false,
    accent: '#462C6B',
    iconBg: 'bg-gradient-to-br from-[#462C6B] to-[#CA1F47]',
  },
  {
    id: 9,
    title: 'Mental Health at Work',
    description: 'Equip managers and employees with tools to support wellbeing at work.',
    category: 'hr',
    duration: '1h 30m',
    enrolled: 2750,
    rating: 4.9,
    level: 'Beginner',
    tags: ['Wellbeing', 'HR'],
    new: true,
    accent: '#db2777',
    iconBg: 'bg-gradient-to-br from-rose-400 to-pink-600',
  },
  {
    id: 10,
    title: 'Anti-Bribery & Corruption',
    description: 'Understand legal obligations and ethical decision-making in global business.',
    category: 'compliance',
    duration: '1h 50m',
    enrolled: 740,
    rating: 4.6,
    level: 'Beginner',
    tags: ['Ethics', 'Legal'],
    new: false,
    accent: '#475569',
    iconBg: 'bg-gradient-to-br from-slate-500 to-slate-700',
  },
  {
    id: 11,
    title: 'Cross-Cultural Communication',
    description: 'Navigate cultural differences and communicate effectively across borders.',
    category: 'global',
    duration: '2h 45m',
    enrolled: 660,
    rating: 4.7,
    level: 'Intermediate',
    tags: ['Culture', 'Global'],
    new: false,
    accent: '#7c3aed',
    iconBg: 'bg-gradient-to-br from-fuchsia-500 to-violet-600',
  },
  {
    id: 12,
    title: 'Introduction to SCORM & E-Learning',
    description: 'Build and deploy SCORM-compliant content for modern LMS platforms.',
    category: 'it',
    duration: '3h 00m',
    enrolled: 320,
    rating: 4.4,
    level: 'Advanced',
    tags: ['SCORM', 'LMS'],
    new: true,
    accent: '#0d9488',
    iconBg: 'bg-gradient-to-br from-teal-500 to-emerald-600',
  },
]

const CATEGORIES = [
  { id: 'all',        label: 'All Categories' },
  { id: 'compliance', label: 'Compliance'      },
  { id: 'it',         label: 'IT & Security'   },
  { id: 'soft',       label: 'Soft Skills'     },
  { id: 'management', label: 'Management'      },
  { id: 'hr',         label: 'HR & Culture'    },
  { id: 'finance',    label: 'Finance'         },
  { id: 'global',     label: 'Global'          },
]

const LEVEL_STYLES = {
  Beginner:     'bg-emerald-50 text-emerald-700',
  Intermediate: 'bg-amber-50 text-amber-700',
  Advanced:     'bg-rose-50 text-rose-700',
}

// ── State ─────────────────────────────────────────────────────────────────────
const search         = ref('')
const activeCategory = ref('all')
const sortBy         = ref('popular')
const wishlist       = ref(new Set())

const SORT_OPTIONS = [
  { id: 'popular',  label: 'Most Popular'  },
  { id: 'rating',   label: 'Highest Rated' },
  { id: 'newest',   label: 'Newest'        },
  { id: 'shortest', label: 'Shortest'      },
]

// ── Computed ──────────────────────────────────────────────────────────────────
const filtered = computed(() => {
  let list = CATALOG
  if (activeCategory.value !== 'all')
    list = list.filter(c => c.category === activeCategory.value)
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(c =>
      c.title.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      c.tags.some(t => t.toLowerCase().includes(q))
    )
  }
  const sorted = [...list]
  if (sortBy.value === 'popular')  sorted.sort((a, b) => b.enrolled - a.enrolled)
  if (sortBy.value === 'rating')   sorted.sort((a, b) => b.rating - a.rating)
  if (sortBy.value === 'newest')   sorted.sort((a, b) => (b.new ? 1 : 0) - (a.new ? 1 : 0))
  if (sortBy.value === 'shortest') sorted.sort((a, b) => a.duration.localeCompare(b.duration))
  return sorted
})

const stats = computed(() => [
  {
    label:     'Total Courses',
    value:     CATALOG.length,
    iconClass: 'bg-gradient-to-br from-[#462C6B] to-[#7D6B9D]',
    border:    'border-[#E8E2F0]',
    type:      'book',
  },
  {
    label:     'New This Month',
    value:     CATALOG.filter(c => c.new).length,
    iconClass: 'bg-gradient-to-br from-[#CA1F47] to-rose-600',
    border:    'border-[#FAEAEE]',
    type:      'award',
  },
  {
    label:     'Total Enrolled',
    value:     formatEnrolled(CATALOG.reduce((a, c) => a + c.enrolled, 0)),
    iconClass: 'bg-gradient-to-br from-emerald-400 to-teal-500',
    border:    'border-emerald-100',
    type:      'graduation',
  },
])

function toggleWishlist(id) {
  const w = new Set(wishlist.value)
  w.has(id) ? w.delete(id) : w.add(id)
  wishlist.value = w
}

function formatEnrolled(n) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)
}
</script>

<template>
  <div class="min-h-screen bg-[#F7F5FA] p-6">

    <!-- ── Page header ──────────────────────────────────────────────────────── -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-asi-black">Course Catalog</h1>
        <p class="text-sm text-asi-gray mt-0.5">Browse and enroll in available courses</p>
      </div>

      <!-- Search + Filters inline -->
      <div class="flex items-center gap-2 flex-wrap">
        <div class="relative w-full sm:w-64">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] pointer-events-none" />
          <input
            v-model="search"
            type="text"
            placeholder="Search courses or topics…"
            class="w-full h-10 bg-white rounded-xl pl-9 pr-8 text-sm text-[#231F20] placeholder-[#7D6B9D] border border-[#E8E2F0] outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] shadow-sm transition-all"
          />
          <button
            v-if="search"
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] hover:text-[#231F20] transition-colors"
            @click="search = ''"
          >
            <X :size="13" />
          </button>
        </div>

        <!-- Category dropdown -->
        <div class="relative">
          <select
            v-model="activeCategory"
            class="appearance-none h-10 pl-4 pr-9 text-sm bg-white border border-[#E8E2F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] text-[#231F20] cursor-pointer shadow-sm"
          >
            <option v-for="cat in CATEGORIES" :key="cat.id" :value="cat.id">{{ cat.label }}</option>
          </select>
          <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] pointer-events-none" />
        </div>

        <!-- Sort dropdown -->
        <div class="relative">
          <select
            v-model="sortBy"
            class="appearance-none h-10 pl-4 pr-9 text-sm bg-white border border-[#E8E2F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] text-[#231F20] cursor-pointer shadow-sm"
          >
            <option v-for="s in SORT_OPTIONS" :key="s.id" :value="s.id">{{ s.label }}</option>
          </select>
          <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] pointer-events-none" />
        </div>
      </div>
    </div>

    <!-- ── Stats strip ──────────────────────────────────────────────────────── -->
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
      <div
        v-for="s in stats"
        :key="s.label"
        :class="['bg-white rounded-2xl border p-4 flex items-center gap-3 shadow-sm', s.border]"
      >
        <div :class="['w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm', s.iconClass]">
          <BookOpen      v-if="s.type === 'book'"       :size="16" class="text-white" />
          <Award         v-else-if="s.type === 'award'"      :size="16" class="text-white" />
          <GraduationCap v-else-if="s.type === 'graduation'" :size="16" class="text-white" />
          <Star          v-else                               :size="16" class="text-white" />
        </div>
        <div>
          <p class="text-xl font-extrabold text-[#231F20] leading-none">{{ s.value }}</p>
          <p class="text-[11px] text-[#67686B] mt-0.5">{{ s.label }}</p>
        </div>
      </div>
    </div>

    <!-- Result count -->
    <p class="text-xs text-[#67686B] mb-4 font-medium">
      Showing <span class="font-bold text-[#231F20]">{{ filtered.length }}</span>
      course{{ filtered.length !== 1 ? 's' : '' }}
      <template v-if="search"> for "<span class="text-[#231F20]">{{ search }}</span>"</template>
    </p>

    <!-- ── Course grid ──────────────────────────────────────────────────────── -->
    <div v-if="filtered.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-8">
      <div
        v-for="course in filtered"
        :key="course.id"
        class="bg-white rounded-2xl border border-[#E8E2F0] shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex flex-col group cursor-pointer overflow-hidden"
      >
        <!-- Top accent bar -->
        <div class="h-1 w-full" :style="{ background: `linear-gradient(to right, ${course.accent}, ${course.accent}99)` }" />

        <div class="p-4 flex flex-col flex-1">
          <!-- Icon + wishlist row -->
          <div class="flex items-start justify-between mb-3">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center shadow-sm flex-shrink-0', course.iconBg]">
              <BookOpen :size="16" class="text-white" />
            </div>

            <div class="flex items-center gap-2">
              <!-- NEW badge -->
              <span
                v-if="course.new"
                class="text-[9px] font-extrabold uppercase tracking-wider bg-[#FAEAEE] text-[#CA1F47] px-2 py-0.5 rounded-full"
              >
                New
              </span>
            </div>
          </div>

        
          
          <h3 class="text-sm font-extrabold text-[#231F20] leading-snug line-clamp-2 mb-1.5 group-hover:text-[#462C6B] transition-colors">
            {{ course.title }}
          </h3>

          <!-- Description -->
          <p class="text-[11px] text-[#67686B] leading-relaxed line-clamp-2 mb-3 flex-1">
            {{ course.description }}
          </p>

          <!-- Tags -->
          <div class="flex flex-wrap gap-1 mb-3">
            <span
              v-for="tag in course.tags"
              :key="tag"
              class="inline-flex items-center gap-0.5 text-[9px] font-semibold bg-[#F0EDF6] text-[#7D6B9D] px-1.5 py-0.5 rounded-md"
            >
              <Tag :size="8" />{{ tag }}
            </span>
          </div>

          <!-- Meta row: rating · duration · enrolled -->
          <div class="flex items-center justify-between text-[10px] text-[#67686B] mb-3">
            <div class="flex items-center gap-1">
              <Clock :size="10" />{{ course.duration }}
            </div>
            <div class="flex items-center gap-1">
              <Users :size="10" />{{ formatEnrolled(course.enrolled) }}
            </div>
          </div>

          <!-- Level + CTA -->
          <div class="flex items-center justify-between pt-3 border-t border-[#F0EDF6]">
            <span :class="['text-[10px] font-bold px-2 py-0.5 rounded-full', LEVEL_STYLES[course.level]]">
              {{ course.level }}
            </span>
            <button
              type="button"
              class="flex items-center gap-1 text-xs font-bold text-[#462C6B] hover:text-[#CA1F47] transition-colors"
            >
              Enroll <ChevronRight :size="13" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Empty state ──────────────────────────────────────────────────────── -->
    <div v-else class="flex flex-col items-center justify-center py-20 text-center">
      <div class="w-16 h-16 rounded-2xl bg-[#F0EDF6] flex items-center justify-center mb-4">
        <BookOpen :size="24" class="text-[#7D6B9D]" />
      </div>
      <p class="text-base font-extrabold text-[#231F20] mb-1">No courses found</p>
      <p class="text-sm text-[#67686B] mb-4">Try a different search term or category</p>
      <button
        type="button"
        class="text-xs font-bold text-[#462C6B] hover:text-[#CA1F47] transition-colors flex items-center gap-1"
        @click="search = ''; activeCategory = 'all'"
      >
        <X :size="13" /> Clear filters
      </button>
    </div>

  </div>
</template>

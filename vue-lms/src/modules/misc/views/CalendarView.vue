<script setup>
import { ref, computed } from 'vue'
import {
  ChevronLeft, ChevronRight, ChevronDown, Calendar,
  Clock, CheckCircle2, AlertCircle, Sparkles, X, MapPin
} from 'lucide-vue-next'

// ── Static mock data ──────────────────────────────────────────────────────────
const today = new Date()

function daysFromToday(n) {
  const d = new Date(today)
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

const MOCK_COURSES = [
  {
    id: 1,
    title: 'Workplace Safety & Compliance',
    category: 'Health & Safety',
    dueDate: daysFromToday(-5),
    status: 'overdue',
    progress: 40,
    assignedTo: 'All Employees',
  },
  {
    id: 2,
    title: 'Data Privacy Fundamentals',
    category: 'IT & Security',
    dueDate: daysFromToday(-2),
    status: 'overdue',
    progress: 70,
    assignedTo: 'IT Department',
  },
  {
    id: 3,
    title: 'Leadership Essentials',
    category: 'Management',
    dueDate: daysFromToday(0),
    status: 'due-today',
    progress: 85,
    assignedTo: 'Team Leads',
  },
  {
    id: 4,
    title: 'Customer Service Excellence',
    category: 'Soft Skills',
    dueDate: daysFromToday(0),
    status: 'due-today',
    progress: 20,
    assignedTo: 'Support Team',
  },
  {
    id: 5,
    title: 'Financial Risk Management',
    category: 'Finance',
    dueDate: daysFromToday(3),
    status: 'upcoming',
    progress: 55,
    assignedTo: 'Finance Dept',
  },
  {
    id: 6,
    title: 'Introduction to SCORM',
    category: 'E-Learning',
    dueDate: daysFromToday(3),
    status: 'upcoming',
    progress: 0,
    assignedTo: 'L&D Team',
  },
  {
    id: 7,
    title: 'Cybersecurity Awareness',
    category: 'IT & Security',
    dueDate: daysFromToday(7),
    status: 'upcoming',
    progress: 10,
    assignedTo: 'All Employees',
  },
  {
    id: 8,
    title: 'Effective Communication',
    category: 'Soft Skills',
    dueDate: daysFromToday(7),
    status: 'upcoming',
    progress: 30,
    assignedTo: 'All Employees',
  },
  {
    id: 9,
    title: 'Project Management Basics',
    category: 'Management',
    dueDate: daysFromToday(14),
    status: 'upcoming',
    progress: 0,
    assignedTo: 'Project Managers',
  },
  {
    id: 10,
    title: 'Diversity & Inclusion',
    category: 'HR & Culture',
    dueDate: daysFromToday(-10),
    status: 'completed',
    progress: 100,
    assignedTo: 'All Employees',
  },
  {
    id: 11,
    title: 'Anti-Bribery & Corruption',
    category: 'Compliance',
    dueDate: daysFromToday(21),
    status: 'upcoming',
    progress: 0,
    assignedTo: 'All Employees',
  },
  {
    id: 12,
    title: 'Mental Health at Work',
    category: 'HR & Culture',
    dueDate: daysFromToday(10),
    status: 'upcoming',
    progress: 15,
    assignedTo: 'Managers',
  },
]

// ── Filters ───────────────────────────────────────────────────────────────────
const activeFilter = ref('all')
const FILTERS = [
  { id: 'all',       label: 'All' },
  { id: 'overdue',   label: 'Overdue' },
  { id: 'due-today', label: 'Due Today' },
  { id: 'upcoming',  label: 'Upcoming' },
  { id: 'completed', label: 'Completed' },
]

const filteredCourses = computed(() =>
  activeFilter.value === 'all'
    ? MOCK_COURSES
    : MOCK_COURSES.filter(c => c.status === activeFilter.value)
)

// ── Calendar state ─────────────────────────────────────────────────────────────
const viewYear  = ref(today.getFullYear())
const viewMonth = ref(today.getMonth())

function prevMonth() {
  if (viewMonth.value === 0) { viewMonth.value = 11; viewYear.value-- }
  else viewMonth.value--
}
function nextMonth() {
  if (viewMonth.value === 11) { viewMonth.value = 0; viewYear.value++ }
  else viewMonth.value++
}

const MONTH_NAMES = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December',
]
const DAY_NAMES = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

const calendarDays = computed(() => {
  const firstDay    = new Date(viewYear.value, viewMonth.value, 1).getDay()
  const daysInMonth = new Date(viewYear.value, viewMonth.value + 1, 0).getDate()
  const daysInPrev  = new Date(viewYear.value, viewMonth.value, 0).getDate()
  const cells = []

  for (let i = firstDay - 1; i >= 0; i--)
    cells.push({ day: daysInPrev - i, month: 'prev', date: null })

  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(viewYear.value, viewMonth.value, d)
    cells.push({ day: d, month: 'cur', date })
  }

  const remaining = 42 - cells.length
  for (let d = 1; d <= remaining; d++)
    cells.push({ day: d, month: 'next', date: null })

  return cells
})

// ── Date helpers ──────────────────────────────────────────────────────────────
function toKey(dateObj) {
  if (!dateObj) return null
  const d = new Date(dateObj)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

const todayKey = toKey(today)

const coursesByDate = computed(() => {
  const map = {}
  for (const c of filteredCourses.value) {
    if (!c.dueDate) continue
    if (!map[c.dueDate]) map[c.dueDate] = []
    map[c.dueDate].push(c)
  }
  return map
})

function cellKey(cell) {
  return cell.date ? toKey(cell.date) : null
}

function isToday(cell) {
  return cell.date ? toKey(cell.date) === todayKey : false
}

// ── Status config ─────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  'overdue':   { chip: 'bg-[#FAEAEE] text-[#CA1F47]',   dot: 'bg-[#CA1F47]',   label: 'Overdue'   },
  'due-today': { chip: 'bg-amber-50 text-amber-700',     dot: 'bg-amber-500',   label: 'Due Today' },
  'upcoming':  { chip: 'bg-[#F0EDF6] text-[#462C6B]',   dot: 'bg-[#7D6B9D]',  label: 'Upcoming'  },
  'completed': { chip: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500', label: 'Completed' },
}

function dominantStatus(courses) {
  if (courses.some(c => c.status === 'overdue'))   return 'overdue'
  if (courses.some(c => c.status === 'due-today')) return 'due-today'
  if (courses.some(c => c.status === 'upcoming'))  return 'upcoming'
  return 'completed'
}

// ── Selected day ──────────────────────────────────────────────────────────────
const selectedCell = ref(null)

function selectCell(cell) {
  if (cell.month !== 'cur') return
  selectedCell.value = (selectedCell.value === cell) ? null : cell
}

const selectedCourses = computed(() => {
  if (!selectedCell.value) return []
  const key = cellKey(selectedCell.value)
  return key ? (coursesByDate.value[key] || []) : []
})

// ── Stats bar ─────────────────────────────────────────────────────────────────
const stats = computed(() => ({
  overdue:   MOCK_COURSES.filter(c => c.status === 'overdue').length,
  dueToday:  MOCK_COURSES.filter(c => c.status === 'due-today').length,
  upcoming:  MOCK_COURSES.filter(c => c.status === 'upcoming').length,
  completed: MOCK_COURSES.filter(c => c.status === 'completed').length,
}))

// ── AI Mark feature ───────────────────────────────────────────────────────────
const aiInput     = ref('')
const aiThinking  = ref(false)
const aiMarks     = ref([])   // [{ dateKey, label, color }]
const aiError     = ref('')

const AI_COLORS = [
  { bg: 'bg-violet-500',  ring: 'ring-violet-300',  chip: 'bg-violet-100 text-violet-700',  dot: 'bg-violet-500'  },
  { bg: 'bg-pink-500',    ring: 'ring-pink-300',     chip: 'bg-pink-100 text-pink-700',      dot: 'bg-pink-500'    },
  { bg: 'bg-cyan-500',    ring: 'ring-cyan-300',     chip: 'bg-cyan-100 text-cyan-700',      dot: 'bg-cyan-500'    },
  { bg: 'bg-fuchsia-500', ring: 'ring-fuchsia-300',  chip: 'bg-fuchsia-100 text-fuchsia-700',dot: 'bg-fuchsia-500' },
  { bg: 'bg-teal-500',    ring: 'ring-teal-300',     chip: 'bg-teal-100 text-teal-700',      dot: 'bg-teal-500'    },
]

const MONTH_MAP = {
  jan:0, january:0, feb:1, february:1, mar:2, march:2, apr:3, april:3,
  may:4, jun:5, june:5, jul:6, july:6, aug:7, august:7,
  sep:8, september:8, oct:9, october:9, nov:10, november:10, dec:11, december:11,
}

function parseAIDate(text) {
  const lower = text.toLowerCase().trim()
  const now   = new Date()

  // "today"
  if (/\btoday\b/.test(lower)) return new Date(now)
  // "tomorrow"
  if (/\btomorrow\b/.test(lower)) { const d = new Date(now); d.setDate(d.getDate()+1); return d }
  // "next monday" etc.
  const weekdays = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
  for (let i = 0; i < weekdays.length; i++) {
    if (lower.includes(weekdays[i])) {
      const d   = new Date(now)
      const diff = (i - d.getDay() + 7) % 7 || 7
      d.setDate(d.getDate() + diff)
      return d
    }
  }
  // "in N days"
  const inDays = lower.match(/in\s+(\d+)\s+days?/)
  if (inDays) { const d = new Date(now); d.setDate(d.getDate() + parseInt(inDays[1])); return d }
  // "May 25" or "25 May" or "25th May"
  for (const [mname, midx] of Object.entries(MONTH_MAP)) {
    const re1 = new RegExp(`\\b${mname}\\b\\s+(\\d{1,2})`, 'i')
    const re2 = new RegExp(`(\\d{1,2})(?:st|nd|rd|th)?\\s+\\b${mname}\\b`, 'i')
    const m1 = lower.match(re1)
    const m2 = lower.match(re2)
    const day = m1 ? parseInt(m1[1]) : m2 ? parseInt(m2[1]) : null
    if (day) {
      const yr = (midx < now.getMonth()) ? now.getFullYear() + 1 : now.getFullYear()
      return new Date(yr, midx, day)
    }
  }
  // ISO or slash date  e.g. 2026-06-15 or 6/15
  const iso = lower.match(/(\d{4})-(\d{1,2})-(\d{1,2})/)
  if (iso) return new Date(parseInt(iso[1]), parseInt(iso[2])-1, parseInt(iso[3]))
  const slash = lower.match(/(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?/)
  if (slash) {
    const yr = slash[3] ? parseInt(slash[3]) : now.getFullYear()
    return new Date(yr < 100 ? 2000+yr : yr, parseInt(slash[1])-1, parseInt(slash[2]))
  }
  return null
}

function extractLabel(text) {
  return text
    .replace(/\b(mark|remind|pin|highlight|set|add|flag|note|deadline|on|for|as)\b/gi, '')
    .replace(/\s+/g, ' ')
    .trim() || 'Marked by AI'
}

function runAIMark() {
  aiError.value = ''
  if (!aiInput.value.trim()) return
  aiThinking.value = true

  setTimeout(() => {
    const date = parseAIDate(aiInput.value)
    if (!date || isNaN(date)) {
      aiError.value = "Couldn't understand that date. Try: \"Mark May 25\" or \"Remind me in 3 days\"."
      aiThinking.value = false
      return
    }
    const key   = toKey(date)
    const label = extractLabel(aiInput.value)
    const color = AI_COLORS[aiMarks.value.length % AI_COLORS.length]

    // navigate to that month
    viewYear.value  = date.getFullYear()
    viewMonth.value = date.getMonth()

    aiMarks.value.push({ dateKey: key, label, color })
    aiInput.value   = ''
    aiThinking.value = false
  }, 900)
}

const aiMarksByDate = computed(() => {
  const map = {}
  for (const m of aiMarks.value) {
    if (!map[m.dateKey]) map[m.dateKey] = []
    map[m.dateKey].push(m)
  }
  return map
})

function removeAIMark(idx) {
  aiMarks.value.splice(idx, 1)
}
</script>

<template>
  <div class="min-h-screen bg-[#F7F5FA] p-6">

    <!-- ── Page header ──────────────────────────────────────────────────────── -->
    <div class="mb-4">
      <h1 class="text-xl font-bold text-asi-black">Course Calendar</h1>
      <p class="text-sm text-asi-gray mt-0.5">View all course due dates at a glance</p>
    </div>

    <!-- ── AI Date Marker ──────────────────────────────────────────────────── -->
    <div class="mb-5 bg-white rounded-2xl border border-[#E8E2F0] shadow-sm overflow-hidden">
      <div class="px-5 py-4">
        <div class="flex flex-wrap items-center gap-4">

          <!-- Icon + label block -->
          <div class="flex items-center gap-3 flex-shrink-0">
            <div class="relative">
              <div class="w-10 h-10 rounded-xl bg-[#462C6B] flex items-center justify-center">
                <Sparkles :size="18" class="text-white" />
              </div>
              <!-- AI badge dot -->
              <span class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#CA1F47] border-2 border-white flex items-center justify-center">
                <span class="text-[7px] font-black text-white leading-none tracking-tight">AI</span>
              </span>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <p class="text-sm font-extrabold text-[#231F20] leading-tight">Date Marker</p>
                <span class="text-[9px] font-bold px-1.5 py-0.5 bg-[#F0EDF6] text-[#462C6B] rounded-full uppercase tracking-wider">Beta</span>
              </div>
              <p class="text-[10px] text-[#7D6B9D] mt-0.5">Describe a date and I'll pin it on the calendar</p>
            </div>
          </div>

          <!-- Vertical divider -->
          <div class="hidden sm:block w-px h-9 bg-[#E8E2F0] flex-shrink-0" />

          <!-- Input + button -->
          <div class="flex-1 flex items-center gap-2 min-w-[240px]">
            <div class="relative flex-1">
              <input
                v-model="aiInput"
                type="text"
                placeholder='e.g. "Mark June 10 as Final Review" or "Remind me in 5 days"'
                class="w-full h-10 bg-[#F7F5FA] border border-[#E8E2F0] rounded-xl pl-4 pr-10 text-sm text-[#231F20] placeholder-[#C5B8D8] outline-none focus:border-[#462C6B] focus:ring-2 focus:ring-[#462C6B]/10 transition-all"
                @keydown.enter="runAIMark"
              />
              <Sparkles
                v-if="!aiThinking"
                :size="13"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-[#C5B8D8]"
              />
              <svg
                v-else
                class="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 animate-spin text-[#7D6B9D]"
                fill="none" viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
            </div>

            <button
              type="button"
              :disabled="aiThinking || !aiInput.trim()"
              class="h-10 flex-shrink-0 flex items-center gap-1.5 px-5 rounded-xl text-xs font-bold bg-[#462C6B] hover:bg-[#3a2459] disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all"
              @click="runAIMark"
            >
              <MapPin :size="13" />
              Pin it
            </button>
          </div>

          <!-- Vertical divider -->
          <div class="hidden sm:block w-px h-9 bg-[#E8E2F0] flex-shrink-0" />

          <!-- Filter dropdown -->
          <div class="relative flex-shrink-0">
            <select
              v-model="activeFilter"
              class="appearance-none h-10 pl-4 pr-9 text-sm bg-white border border-[#E8E2F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] text-[#231F20] cursor-pointer shadow-sm"
              @change="selectedCell = null"
            >
              <option v-for="f in FILTERS" :key="f.id" :value="f.id">{{ f.label }}</option>
            </select>
            <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] pointer-events-none" />
          </div>
        </div>

        <!-- Error -->
        <p v-if="aiError" class="mt-3 text-xs text-[#CA1F47] flex items-center gap-1.5 pl-1">
          <AlertCircle :size="12" /> {{ aiError }}
        </p>

        <!-- Active marks -->
        <div v-if="aiMarks.length" class="mt-4 pt-3 border-t border-[#F0EDF6]">
          <p class="text-[9px] font-bold uppercase tracking-widest text-[#C5B8D8] mb-2">Pinned dates</p>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="(mark, idx) in aiMarks"
              :key="idx"
              :class="['flex items-center gap-1.5 pl-3 pr-2 py-1.5 rounded-lg text-[11px] font-semibold border', mark.color.chip]"
            >
              <MapPin :size="10" class="flex-shrink-0" />
              <span>{{ mark.label }}</span>
              <span class="text-[9px] opacity-60 font-normal pl-0.5">
                · {{ new Date(mark.dateKey).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }}
              </span>
              <button
                type="button"
                class="ml-1 opacity-40 hover:opacity-90 transition-opacity"
                @click="removeAIMark(idx)"
              >
                <X :size="10" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Stats strip ──────────────────────────────────────────────────────── -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
      <div
        v-for="(cfg, key) in {
          overdue:  { label: 'Overdue',   count: stats.overdue,   icon: 'AlertCircle',   color: 'from-[#CA1F47] to-rose-600',        ring: 'border-[#FAEAEE]', bg: 'bg-[#FAEAEE]', text: 'text-[#CA1F47]' },
          dueToday: { label: 'Due Today', count: stats.dueToday,  icon: 'Clock',         color: 'from-amber-400 to-orange-500',       ring: 'border-amber-100', bg: 'bg-amber-50',   text: 'text-amber-700' },
          upcoming: { label: 'Upcoming',  count: stats.upcoming,  icon: 'Calendar',      color: 'from-[#462C6B] to-[#7D6B9D]',       ring: 'border-[#E8E2F0]', bg: 'bg-[#F0EDF6]',  text: 'text-[#462C6B]' },
          completed:{ label: 'Completed', count: stats.completed, icon: 'CheckCircle2',  color: 'from-emerald-400 to-teal-500',       ring: 'border-emerald-100', bg: 'bg-emerald-50', text: 'text-emerald-700' },
        }"
        :key="key"
        :class="['bg-white rounded-2xl border p-4 flex items-center gap-3 shadow-sm', cfg.ring]"
      >
        <div :class="['w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-gradient-to-br shadow-sm', cfg.color]">
          <AlertCircle v-if="cfg.icon === 'AlertCircle'" :size="16" class="text-white" />
          <Clock       v-else-if="cfg.icon === 'Clock'"       :size="16" class="text-white" />
          <Calendar    v-else-if="cfg.icon === 'Calendar'"    :size="16" class="text-white" />
          <CheckCircle2 v-else                                :size="16" class="text-white" />
        </div>
        <div>
          <p class="text-xl font-extrabold leading-none" :class="cfg.text">{{ cfg.count }}</p>
          <p class="text-[11px] text-[#67686B] mt-0.5">{{ cfg.label }}</p>
        </div>
      </div>
    </div>

    <!-- ── Main content ─────────────────────────────────────────────────────── -->
    <div class="flex flex-col xl:flex-row gap-5">

      <!-- ── Calendar card ──────────────────────────────────────────────────── -->
      <div class="flex-1 bg-white rounded-2xl shadow-sm border border-[#E8E2F0] overflow-hidden">

        <!-- Month navigation -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-[#E8E2F0]">
          <button
            type="button"
            class="w-8 h-8 rounded-lg flex items-center justify-center text-[#462C6B] hover:bg-[#F0EDF6] transition-colors"
            @click="prevMonth"
          >
            <ChevronLeft :size="18" />
          </button>

          <div class="text-center">
            <h2 class="text-base font-extrabold text-[#231F20] leading-tight">
              {{ MONTH_NAMES[viewMonth] }} {{ viewYear }}
            </h2>
            <p class="text-[10px] text-[#7D6B9D] font-semibold">
              {{ filteredCourses.filter(c => {
                const d = new Date(c.dueDate)
                return d.getMonth() === viewMonth && d.getFullYear() === viewYear
              }).length }} course(s) this month
            </p>
          </div>

          <button
            type="button"
            class="w-8 h-8 rounded-lg flex items-center justify-center text-[#462C6B] hover:bg-[#F0EDF6] transition-colors"
            @click="nextMonth"
          >
            <ChevronRight :size="18" />
          </button>
        </div>

        <!-- Day-of-week headers -->
        <div class="grid grid-cols-7 border-b border-[#E8E2F0] bg-[#FAFAF9]">
          <div
            v-for="name in DAY_NAMES"
            :key="name"
            class="py-2.5 text-center text-[10px] font-bold uppercase tracking-widest text-[#7D6B9D]"
          >
            {{ name }}
          </div>
        </div>

        <!-- Calendar grid -->
        <div class="grid grid-cols-7">
          <div
            v-for="(cell, idx) in calendarDays"
            :key="idx"
            :class="[
              'min-h-[90px] p-1.5 border-r border-b border-[#F0EDF6] relative transition-all duration-150',
              cell.month !== 'cur' ? 'bg-[#FAFAF9]' : 'bg-white',
              cell.month === 'cur' ? 'cursor-pointer hover:bg-[#F7F5FA]' : 'cursor-default',
              selectedCell === cell ? 'bg-[#F0EDF6] ring-2 ring-inset ring-[#7D6B9D]/40' : '',
              cell.month === 'cur' && cellKey(cell) && aiMarksByDate[cellKey(cell)]?.length
                ? 'ring-2 ring-inset ' + aiMarksByDate[cellKey(cell)][0].color.ring : '',
            ]"
            @click="selectCell(cell)"
          >
            <!-- Day number -->
            <div class="flex items-start justify-between mb-1">
              <span
                :class="[
                  'inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold flex-shrink-0',
                  isToday(cell)
                    ? 'bg-gradient-to-br from-[#462C6B] to-[#CA1F47] text-white shadow-sm'
                    : cell.month !== 'cur'
                      ? 'text-[#C5B8D8]'
                      : 'text-[#231F20]',
                ]"
              >
                {{ cell.day }}
              </span>

              <!-- Dot indicator for dominant status -->
              <span
                v-if="cell.month === 'cur' && cellKey(cell) && coursesByDate[cellKey(cell)]?.length"
                :class="['w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0', STATUS_CONFIG[dominantStatus(coursesByDate[cellKey(cell)])].dot]"
              />
            </div>

            <!-- Course chips (up to 2) -->
            <template v-if="cell.month === 'cur' && cellKey(cell)">
              <div
                v-for="course in (coursesByDate[cellKey(cell)] || []).slice(0, 2)"
                :key="course.id"
                :class="[
                  'text-[9px] font-semibold truncate px-1.5 py-0.5 rounded mb-0.5 leading-tight',
                  STATUS_CONFIG[course.status].chip,
                ]"
                :title="course.title"
              >
                {{ course.title }}
              </div>

              <!-- Overflow badge -->
              <div
                v-if="(coursesByDate[cellKey(cell)] || []).length > 2"
                class="text-[9px] font-bold text-[#7D6B9D] px-1 leading-tight"
              >
                +{{ coursesByDate[cellKey(cell)].length - 2 }} more
              </div>
            </template>

            <!-- AI marks on this cell -->
            <template v-if="cell.month === 'cur' && cellKey(cell) && aiMarksByDate[cellKey(cell)]?.length">
              <div
                v-for="(mark, mi) in aiMarksByDate[cellKey(cell)]"
                :key="'ai-' + mi"
                :class="['flex items-center gap-0.5 text-[9px] font-bold truncate px-1.5 py-0.5 rounded mb-0.5 leading-tight', mark.color.chip]"
                :title="mark.label"
              >
                <MapPin :size="8" class="flex-shrink-0" />
                {{ mark.label }}
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ── Right panel ─────────────────────────────────────────────────────── -->
      <div class="xl:w-72 flex flex-col gap-4">

        <!-- Next Deadlines card -->
        <div class="bg-white rounded-2xl shadow-sm border border-[#E8E2F0] overflow-hidden">
          <div class="px-4 py-3 border-b border-[#F0EDF6] flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-[#F0EDF6] flex items-center justify-center">
                <Clock :size="14" class="text-[#462C6B]" />
              </div>
              <p class="text-xs font-bold text-[#231F20]">Next Deadlines</p>
            </div>
            <span class="text-[10px] font-semibold text-[#7D6B9D] bg-[#F0EDF6] px-2 py-0.5 rounded-full">
              {{ MOCK_COURSES.filter(c => c.status === 'upcoming' || c.status === 'due-today').length }} pending
            </span>
          </div>

          <ul class="divide-y divide-[#F7F5FA]">
            <li
              v-for="course in MOCK_COURSES
                .filter(c => c.status === 'upcoming' || c.status === 'due-today')
                .sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate))
                .slice(0, 6)"
              :key="course.id"
              class="flex items-center gap-3 px-4 py-3 hover:bg-[#F7F5FA] transition-colors"
            >
              <span :class="['w-2 h-2 rounded-full flex-shrink-0', STATUS_CONFIG[course.status].dot]" />
              <div class="min-w-0 flex-1">
                <p class="text-[11px] font-semibold text-[#231F20] truncate">{{ course.title }}</p>
                <p class="text-[10px] text-[#67686B] mt-0.5">
                  {{ new Date(course.dueDate).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }) }}
                </p>
              </div>
              <span :class="['text-[9px] font-bold px-2 py-0.5 rounded-full flex-shrink-0', STATUS_CONFIG[course.status].chip]">
                {{ STATUS_CONFIG[course.status].label }}
              </span>
            </li>
          </ul>
        </div>

      </div>
    </div>
  </div>
</template>

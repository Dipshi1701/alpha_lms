<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { X, UserPlus, Users2, Loader2, Lock } from 'lucide-vue-next'
import clsx from 'clsx'

const props = defineProps({
  open: { type: Boolean, default: false },
  courseTitle: { type: String, default: '' },
  users: { type: Array, required: true }, // [{id,name,role}] — ALL eligible learners, regardless of group membership
  initialAssignedUserIds: { type: Array, default: () => [] },
  // G012: this course's existing per-learner CourseAssignment rows —
  // [{ userId, assignedAt, dueDate, source: 'individual'|'group', sourceGroupName }].
  // Powers duplicate-prevention + Assigned/Due/Source display below. Never
  // used to filter `users` — every eligible learner still appears, just
  // annotated (and, for group-sourced rows, locked — see isLocked()).
  learnerAssignments: { type: Array, default: () => [] },
  // Group mode is only offered when the backend actually permits this user
  // to assign a course to a group (Administrator-only — see G006/G009).
  // Hiding it for everyone else isn't "frontend authorization", it just
  // avoids offering a control that would deterministically always 403.
  canAssignToGroup: { type: Boolean, default: false },
  groups: { type: Array, default: () => [] }, // [{id,name}] — exactly what GET /api/groups returned for this user
  groupsLoading: { type: Boolean, default: false },
  groupsLoadError: { type: String, default: '' },
  saving: { type: Boolean, default: false },
})

// G012 PART 9/10: keyed lookup of this course's existing assignment info
// per learner, so the Individual-mode list can show "Already assigned
// individually" / "Already assigned via group: Sales" and lock the
// group-sourced ones (see isLocked()) — never a new assignment system,
// just a read view over what the backend already derived.
const assignmentByUserId = computed(() => {
  const map = {}
  for (const a of props.learnerAssignments || []) {
    map[a.userId] = a
  }
  return map
})

const assignmentInfo = (userId) => assignmentByUserId.value[userId] || null

// Group-sourced assignments are locked here (cannot be un-toggled from the
// Individual list): the individual /assign endpoint has full-set/replace
// semantics, so un-toggling a group-derived row here would silently
// delete a CourseAssignment that a group assignment is still responsible
// for (see PART 6/9). Individually-sourced rows stay toggleable — that IS
// the existing supported unassign flow (PART 12), unchanged from before.
const isLocked = (userId) => assignmentInfo(userId)?.source === 'group'

const formatDate = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

const emit = defineEmits(['close', 'save'])

// 'individual' | 'group'
const mode = ref('individual')

const form = reactive({
  assignedUserIds: [],
})
const selectedGroupId = ref(null)

watch(
  () => [props.open, props.initialAssignedUserIds],
  () => {
    if (!props.open) return
    // Every time the modal is (re)opened for a course, start from a clean,
    // known state — Individual mode, pre-filled with that course's actual
    // current assignments (source-agnostic: includes learners who got the
    // course via a Group as well as individually-assigned ones).
    mode.value = 'individual'
    form.assignedUserIds = [...(props.initialAssignedUserIds || [])]
    selectedGroupId.value = null
  },
  { deep: true }
)

watch(mode, (next, prev) => {
  if (next === prev) return
  if (next === 'group') {
    // Switching away from Individual must not let stale learner toggles
    // leak into a Group submission.
    form.assignedUserIds = []
  } else {
    // Switching back to Individual: drop any group pick and restore the
    // real current assignment state rather than whatever was toggled
    // before switching away.
    selectedGroupId.value = null
    form.assignedUserIds = [...(props.initialAssignedUserIds || [])]
  }
})

const toggleAssignUser = (userId) => {
  if (props.saving || isLocked(userId)) return
  if (form.assignedUserIds.includes(userId)) {
    form.assignedUserIds = form.assignedUserIds.filter((id) => id !== userId)
    return
  }
  form.assignedUserIds = [...form.assignedUserIds, userId]
}

const selectGroup = (groupId) => {
  if (props.saving) return
  selectedGroupId.value = groupId
}

const validationError = ref('')

const submit = () => {
  if (props.saving) return
  validationError.value = ''
  if (mode.value === 'group') {
    if (!selectedGroupId.value) {
      validationError.value = 'Select a group to assign this course to'
      return
    }
    emit('save', { mode: 'group', groupId: selectedGroupId.value })
    return
  }
  emit('save', { mode: 'individual', assignedUserIds: [...form.assignedUserIds] })
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
  >
    <div class="w-full max-w-xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-asi-border flex flex-col">
      <div class="px-6 py-4 border-b border-asi-border flex items-center justify-between">
        <div>
          <h2 class="text-base font-semibold text-asi-black">Assign course</h2>
          <p class="text-xs text-asi-gray mt-0.5">
            {{ courseTitle }}
          </p>
        </div>
        <button
          @click="emit('close')"
          :disabled="saving"
          class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray"
        >
          <X :size="18" />
        </button>
      </div>

      <div class="p-6 space-y-4 overflow-y-auto min-h-[200px]">
        <div>
          <p class="text-xs font-semibold text-asi-gray mb-1.5">Assign to</p>
          <div class="flex items-center gap-4">
            <label class="inline-flex items-center gap-2 text-sm text-asi-black cursor-pointer">
              <input
                type="radio"
                value="individual"
                v-model="mode"
                data-testid="assign-mode-individual"
                :disabled="saving"
                class="accent-asi-purple"
              />
              Individual Learner
            </label>
            <label
              v-if="canAssignToGroup"
              class="inline-flex items-center gap-2 text-sm text-asi-black cursor-pointer"
            >
              <input
                type="radio"
                value="group"
                v-model="mode"
                data-testid="assign-mode-group"
                :disabled="saving"
                class="accent-asi-purple"
              />
              Group
            </label>
          </div>
        </div>

        <div v-if="validationError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ validationError }}
        </div>

        <!-- Individual Learner mode -->
        <div v-if="mode === 'individual'" class="space-y-3">
          <div class="flex items-center gap-2">
            <UserPlus :size="14" class="text-asi-gray" />
            <p class="text-sm text-asi-gray">
              Select learners to assign this course. A learner stays available here even if they
              already belong to a group.
            </p>
          </div>
          <div v-if="!users.length" class="py-8 text-center text-sm text-asi-gray">
            No eligible learners found.
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div
              v-for="u in users"
              :key="u.id"
              :class="clsx(
                'flex flex-col gap-1 border rounded-lg px-3 py-2 transition-colors',
                isLocked(u.id) ? 'border-asi-border bg-asi-surface' : 'border-asi-border hover:border-asi-lavender'
              )"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-asi-black">{{ u.name }}</p>
                  <p class="text-xs text-asi-gray">{{ u.role }}</p>
                </div>
                <button
                  type="button"
                  :data-testid="`assign-learner-${u.id}`"
                  :disabled="saving || isLocked(u.id)"
                  :title="isLocked(u.id) ? 'Assigned via a group — remove it from the group\'s courses instead' : ''"
                  @click="toggleAssignUser(u.id)"
                  :class="clsx(
                    'inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-md border flex-shrink-0',
                    isLocked(u.id)
                      ? 'bg-asi-surface text-asi-gray border-asi-border cursor-not-allowed'
                      : form.assignedUserIds.includes(u.id)
                        ? 'bg-asi-purple text-white border-asi-purple'
                        : 'bg-white text-asi-gray border-asi-border'
                  )"
                >
                  <Lock v-if="isLocked(u.id)" :size="11" />
                  {{ isLocked(u.id) ? 'Locked' : form.assignedUserIds.includes(u.id) ? 'Assigned' : 'Assign' }}
                </button>
              </div>
              <p
                v-if="assignmentInfo(u.id)"
                :data-testid="`assign-learner-${u.id}-info`"
                class="text-[11px] text-asi-gray leading-snug"
              >
                {{
                  assignmentInfo(u.id).source === 'group'
                    ? `Already assigned via group: ${assignmentInfo(u.id).sourceGroupName}`
                    : 'Already assigned individually'
                }}
                · Assigned {{ formatDate(assignmentInfo(u.id).assignedAt) }} · Due {{ formatDate(assignmentInfo(u.id).dueDate) }}
              </p>
            </div>
          </div>
        </div>

        <!-- Group mode -->
        <div v-else class="space-y-3">
          <div class="flex items-center gap-2">
            <Users2 :size="14" class="text-asi-gray" />
            <p class="text-sm text-asi-gray">
              Assigning to a group assigns this course to every current Learner member of that
              group.
            </p>
          </div>

          <div v-if="groupsLoading" class="flex items-center justify-center py-8 text-asi-gray gap-2">
            <Loader2 :size="18" class="animate-spin" />
            Loading groups…
          </div>
          <div
            v-else-if="groupsLoadError"
            class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
          >
            {{ groupsLoadError }}
          </div>
          <div v-else-if="!groups.length" class="py-8 text-center text-sm text-asi-gray">
            No groups available.
          </div>
          <div v-else class="space-y-2">
            <label
              v-for="g in groups"
              :key="g.id"
              class="flex items-center gap-3 border border-asi-border rounded-lg px-3 py-2 cursor-pointer hover:border-asi-lavender transition-colors"
              :data-testid="`assign-group-${g.id}`"
              @click="selectGroup(g.id)"
            >
              <input
                type="radio"
                :checked="selectedGroupId === g.id"
                :disabled="saving"
                class="accent-asi-purple"
                @change="selectGroup(g.id)"
              />
              <p class="text-sm font-medium text-asi-black">{{ g.name }}</p>
            </label>
          </div>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-asi-border flex items-center justify-end gap-2">
        <button
          @click="emit('close')"
          :disabled="saving"
          class="px-3 py-2 text-sm font-medium text-asi-gray hover:bg-asi-surface rounded-lg"
        >
          Cancel
        </button>
        <button
          @click="submit"
          data-testid="assign-submit-btn"
          :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a] transition-colors disabled:opacity-60"
        >
          <Loader2 v-if="saving" :size="15" class="animate-spin" />
          {{ saving ? 'Saving...' : mode === 'group' ? 'Assign to group' : 'Save assignment' }}
        </button>
      </div>
    </div>
  </div>
</template>

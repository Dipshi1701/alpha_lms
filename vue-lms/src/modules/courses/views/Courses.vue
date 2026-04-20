<script setup>
import { useAccess } from '../../../composables/useAccess'
import AdminInstructorCourses from './AdminInstructorCourses.vue'
import LearnerCourses from './LearnerCourses.vue'

const { isAdmin, isInstructor } = useAccess()
</script>

<template>
  <AdminInstructorCourses v-if="isAdmin || isInstructor" />
  <LearnerCourses v-else />
</template>

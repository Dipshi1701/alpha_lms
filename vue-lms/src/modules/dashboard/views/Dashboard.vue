/**
 * DASHBOARD VIEW
 * 
 * Shows different dashboard based on user role:
 *   - Administrator: Full admin dashboard with all widgets
 *   - Instructor: Instructor-specific dashboard
 *   - Learner: Simple learner dashboard
 * 
 * This uses the centralized useAccess() helper for cleaner code
 */

<script setup>
import { useAccess } from '../../../composables/useAccess'
import AdminDashboard from '../../../components/dashboard/AdminDashboard.vue'
import InstructorDashboard from '../../../components/dashboard/InstructorDashboard.vue'
import LearnerDashboard from '../../../components/dashboard/LearnerDashboard.vue'

// Use the centralized access helper
const { isAdmin, isInstructor } = useAccess()
console.log(isAdmin, isInstructor)

</script>

<template>
  <div>
    <!-- Show different dashboard based on role -->
    <AdminDashboard v-if="isAdmin" />
    <InstructorDashboard v-else-if="isInstructor" />
    <LearnerDashboard v-else />
  </div>
</template>



<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import { Doughnut } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({
  slices: {
    type: Array,
    required: true
  }
})

const chartData = computed(() => ({
  labels: props.slices.map(s => s.name),
  datasets: [
    {
      data: props.slices.map(s => s.value),
      backgroundColor: props.slices.map(s => s.color),
      borderWidth: 0,
      cutout: '70%'
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: '#ffffff',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      titleColor: '#111827',
      bodyColor: '#4b5563',
      padding: 10
    }
  }
}
</script>

<template>
  <Doughnut :data="chartData" :options="chartOptions" />
</template>


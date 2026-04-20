<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({
  dataPoints: {
    type: Array,
    required: true
  }
})

const chartData = computed(() => ({
  labels: props.dataPoints.map(p => p.time),
  datasets: [
    {
      label: 'Logins',
      data: props.dataPoints.map(p => p.logins),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.15)',
      tension: 0.4,
      fill: true,
      borderWidth: 2,
      pointRadius: 0
    },
    {
      label: 'Completions',
      data: props.dataPoints.map(p => p.completions),
      borderColor: '#22c55e',
      backgroundColor: 'rgba(34,197,94,0.15)',
      tension: 0.4,
      fill: true,
      borderWidth: 2,
      pointRadius: 0
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
      padding: 12,
      displayColors: true
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: '#9ca3af',
        maxRotation: 0,
        autoSkip: true,
        maxTicksLimit: 8
      }
    },
    y: {
      grid: {
        color: '#f3f4f6'
      },
      ticks: {
        color: '#9ca3af',
        stepSize: 1
      },
      beginAtZero: true
    }
  }
}
</script>

<template>
  <Line :data="chartData" :options="chartOptions" />
</template>


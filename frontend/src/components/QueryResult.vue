<template>
  <div class="space-y-6">
    <!-- Metro Map Visualization (Answer Mode) -->
    <div class="mb-4">
      <MetroMap
        mode="answer"
        :startStation="gameStore.startStation"
        :endStation="gameStore.endStation"
        :path="mapPath"
        :pathData="firstPathData"
      />
    </div>

    <!-- All Shortest Paths -->
    <div v-if="gameStore.systemPaths.length > 0" class="p-4 bg-blue-50 rounded-lg border-2 border-blue-300">
      <h4 class="font-semibold text-blue-700 mb-3 flex items-center gap-1">
        <BadgeCheck class="w-5 h-5" /> 所有最短路径 (共 {{ gameStore.systemPaths.length }} 条，乘坐 {{ stationCount }} 站):
      </h4>
      <div class="space-y-2">
        <div
          v-for="(pathData, index) in gameStore.systemPaths"
          :key="index"
          class="p-3 bg-white rounded border border-blue-200"
        >
          <p class="text-sm font-medium text-blue-600 mb-1">路径 {{ index + 1 }}:</p>
          <p class="text-sm text-gray-600" v-html="formatPathWithTransfers(pathData)"></p>
        </div>
      </div>
    </div>

    <!-- Action Button: Only Reset -->
    <div class="text-center">
      <button
        @click="handleReset"
        class="px-8 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium flex items-center gap-2 mx-auto"
      >
        <RefreshCw class="w-5 h-5" /> 重新选站
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from '@/stores/game'
import MetroMap from './MetroMap.vue'
import { BadgeCheck, RefreshCw } from 'lucide-vue-next'

const gameStore = useGameStore()

// First path data (structured format from backend)
const firstPathData = computed(() => {
  if (gameStore.systemPaths.length > 0) {
    return gameStore.systemPaths[0]
  }
  return null
})

// Map path: use the first system path's stations for visualization
const mapPath = computed(() => {
  const pathData = firstPathData.value
  if (!pathData) return []
  
  // New structured format: {annotated, stations, lines, transfers}
  if (pathData.stations) {
    return pathData.stations
  }
  // Legacy string format: "站A → 站B(换乘X号线) → 站C"
  if (typeof pathData === 'string') {
    return pathData.split(' → ').map(s => s.replace(/\([^)]*\)/g, '').trim())
  }
  return []
})

// Station count: number of stations in the first path minus 1
const stationCount = computed(() => {
  return mapPath.value.length > 0 ? mapPath.value.length - 1 : 0
})

const handleReset = () => {
  gameStore.resetGame()
}

// Format path with transfer annotations
const formatPathWithTransfers = (pathData) => {
  // Helper function to highlight only transfer annotations (containing '换乘')
  const highlightTransfers = (str) => {
    return str.replace(/\(([^)]*换乘[^)]*)\)/g, '<span class="text-orange-600 font-semibold">($1)</span>')
  }
  
  // New structured format: {annotated, stations, lines, transfers}
  if (pathData && pathData.annotated) {
    return highlightTransfers(pathData.annotated)
  }
  // Legacy string format with transfer annotations
  if (typeof pathData === 'string') {
    return highlightTransfers(pathData)
  }
  return String(pathData)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Metro Map Visualization (Answer Mode) -->
    <div class="mb-4">
      <MetroMap
        mode="answer"
        :startStation="gameStore.startStation"
        :endStation="gameStore.endStation"
        :path="mapPath"
      />
    </div>

    <!-- All Shortest Paths -->
    <div v-if="gameStore.systemPaths.length > 0" class="p-4 bg-blue-50 rounded-lg border-2 border-blue-300">
      <h4 class="font-semibold text-blue-700 mb-3">
        ✅ 所有最短路径 (共 {{ gameStore.systemPaths.length }} 条):
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
        class="px-8 py-3 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition font-medium"
      >
        🎮 重新选站
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from '@/stores/game'
import MetroMap from './MetroMap.vue'

const gameStore = useGameStore()

// Map path: use the first system path for visualization
const mapPath = computed(() => {
  if (gameStore.systemPaths.length > 0) {
    const firstPath = gameStore.systemPaths[0]
    if (typeof firstPath === 'string') {
      // String format: "站A → 站B(换乘X号线) → 站C"
      return firstPath.split(' → ').map(s => s.replace(/\([^)]*\)/g, '').trim())
    } else if (Array.isArray(firstPath)) {
      // Array format: [{station: '站A'}, {station: '站B', transfer: 'X号线'}]
      return firstPath.map(item => typeof item === 'object' ? item.station : item)
    }
  }
  return []
})

const handleReset = () => {
  gameStore.resetGame()
}

// Format path with transfer annotations
const formatPathWithTransfers = (pathData) => {
  if (typeof pathData === 'string') {
    // String format with transfer annotations
    return pathData.replace(/\(/g, '<span class="text-orange-600 font-semibold">(')
                    .replace(/\)/g, ')</span>')
  } else if (Array.isArray(pathData)) {
    // Array format
    if (pathData.length > 0 && typeof pathData[0] === 'object' && pathData[0].station) {
      // Object array with transfer info
      return pathData.map(item => {
        if (item.transfer) {
          return `${item.station}<span class="text-orange-600 font-semibold">(${item.transfer})</span>`
        }
        return item.station
      }).join(' → ')
    } else {
      // Simple station array
      return pathData.join(' → ')
    }
  }
  return String(pathData)
}
</script>

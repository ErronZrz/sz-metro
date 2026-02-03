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

    <!-- All Shortest Paths (答对时自动显示，紧跟在地图下方) -->
    <div v-if="gameStore.systemPaths.length > 0" class="p-4 bg-blue-50 rounded-lg border-2 border-blue-300">
      <h4 class="font-semibold text-blue-700 mb-3 flex items-center gap-1">
        <BadgeCheck class="w-5 h-5" /> 所有最短路径 (共 {{ gameStore.systemPaths.length }} 条) (minCost = {{ formattedCost }}):
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

    <!-- Result Message (只显示答对的情况) -->
    <div class="p-6 rounded-lg border-2 bg-green-50 border-green-500">
      <h3 class="text-2xl font-bold mb-2 text-green-700 flex items-center gap-2">
        <Trophy class="w-7 h-7" /> 恭喜！答对了！
      </h3>
      
      <div class="mt-4 space-y-2">
        <p v-if="gameStore.validationResult?.user_cost" class="text-lg">
          你的成本: <span class="font-bold">{{ gameStore.validationResult.user_cost }}</span>
        </p>
        <p class="text-lg">
          最短成本: <span class="font-bold">{{ gameStore.validationResult?.shortest_cost }}</span>
        </p>
      </div>
    </div>

    <!-- Your Path -->
    <div class="p-4 bg-gray-50 rounded-lg">
      <h4 class="font-semibold text-gray-700 mb-2">你的路径:</h4>
      <p class="text-gray-600" v-html="formatPathWithTransfers(gameStore.validationResult?.user_path_annotated || gameStore.userPath.join(' → '))"></p>
    </div>

    <!-- Action Buttons -->
    <div class="text-center">
      <button
        @click="handleNewGame"
        class="px-8 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium flex items-center gap-2"
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
import { BadgeCheck, Trophy, RefreshCw } from 'lucide-vue-next'

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

// Format cost: integer without decimal point, float with decimal point
const formattedCost = computed(() => {
  const cost = gameStore.shortestCost
  if (cost === null || cost === undefined) return ''
  return Number.isInteger(cost) ? cost.toString() : cost.toString()
})

const handleNewGame = () => {
  gameStore.newGame()
}

const handleReset = () => {
  gameStore.resetGame()
}

// 格式化路径，标注换乘站
const formatPathWithTransfers = (pathData) => {
  // Helper function to highlight only transfer annotations (containing '换乘')
  const highlightTransfers = (str) => {
    return str.replace(/\(([^)]*换乘[^)]*)\)/g, '<span class="text-orange-600 font-semibold">($1)</span>')
  }
  
  // New structured format: {annotated, stations, lines, transfers}
  if (pathData && pathData.annotated) {
    return highlightTransfers(pathData.annotated)
  }
  // Legacy string format (带换乘标注)
  if (typeof pathData === 'string') {
    return highlightTransfers(pathData)
  }
  return String(pathData)
}
</script>

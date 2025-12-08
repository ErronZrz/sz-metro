<template>
  <div class="space-y-4">
    <div class="grid md:grid-cols-2 gap-4">
      <!-- Start Station -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">起点站</label>
        <SearchableSelect
          :value="gameStore.startStation"
          :options="gameStore.availableStations"
          :disabled="isLocked || !gameStore.hasSelectedLines"
          :placeholder="startPlaceholder"
          @update:value="handleStartChange"
        />
      </div>

      <!-- End Station -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">终点站</label>
        <SearchableSelect
          :value="gameStore.endStation"
          :options="gameStore.reachableStations"
          :disabled="isLocked || !gameStore.startStation"
          :placeholder="endPlaceholder"
          @update:value="handleEndChange"
        />
      </div>
    </div>

    <div v-if="!isLocked" class="flex gap-4">
      <button
        @click="handleRandomStations"
        :disabled="!gameStore.hasSelectedLines"
        class="flex-1 px-6 py-3 bg-metro-secondary text-white rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
      >
        🎲 随机生成起终点
      </button>
      <button
        v-if="gameStore.startStation && gameStore.endStation"
        @click="handleStartGame"
        class="flex-1 px-6 py-3 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition font-medium"
      >
        ▶️ 开始游戏
      </button>
    </div>

    <div v-if="gameStore.hasStations" class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <p class="text-blue-700">
        🎯 起点: <span class="font-bold">{{ gameStore.startStation }}</span> → 
        终点: <span class="font-bold">{{ gameStore.endStation }}</span>
      </p>
      <p v-if="gameStore.gameStatus === 'playing' && gameStore.displayCost > 0" class="text-blue-600 mt-2">
        💡 提示：最短路径大约需要 <span class="font-bold text-lg">{{ gameStore.displayCost }}</span> 站
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { useGameStore } from '@/stores/game'
import SearchableSelect from './SearchableSelect.vue'

const gameStore = useGameStore()

// Game in progress or result page locks station selection
const isLocked = computed(() => gameStore.gameStatus === 'playing' || gameStore.gameStatus === 'result')

// Placeholder texts
const startPlaceholder = computed(() => {
  if (!gameStore.hasSelectedLines) return '请先选择线路'
  if (gameStore.availableStations.length === 0) return '加载中...'
  return '输入关键字搜索起点站'
})

const endPlaceholder = computed(() => {
  if (!gameStore.startStation) return '请先选择起点站'
  if (gameStore.reachableStations.length === 0) return '加载中...'
  return '输入关键字搜索终点站'
})

// Watch for line selection changes to load available stations
watch(
  () => gameStore.selectedLines,
  async (newLines) => {
    if (newLines.length > 0) {
      await gameStore.loadAvailableStations()
    }
  },
  { immediate: true, deep: true }
)

const handleStartChange = async (station) => {
  await gameStore.setStartStation(station)
}

const handleEndChange = (station) => {
  gameStore.setEndStation(station)
}

const handleRandomStations = async () => {
  await gameStore.generateRandomStations()
}

const handleStartGame = () => {
  if (gameStore.startStation && gameStore.endStation) {
    gameStore.setStations(gameStore.startStation, gameStore.endStation)
  }
}
</script>

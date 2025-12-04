<template>
  <div class="space-y-4">
    <div class="grid md:grid-cols-2 gap-4">
      <!-- Start Station -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">起点站</label>
        <input
          v-model="gameStore.startStation"
          type="text"
          placeholder="输入起点站名"
          :disabled="isLocked"
          :class="[
            'w-full px-4 py-2 border rounded-lg',
            isLocked 
              ? 'border-gray-200 bg-gray-100 text-gray-500 cursor-not-allowed' 
              : 'border-gray-300 focus:ring-2 focus:ring-metro-primary focus:border-transparent'
          ]"
        />
      </div>

      <!-- End Station -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">终点站</label>
        <input
          v-model="gameStore.endStation"
          type="text"
          placeholder="输入终点站名"
          :disabled="isLocked"
          :class="[
            'w-full px-4 py-2 border rounded-lg',
            isLocked 
              ? 'border-gray-200 bg-gray-100 text-gray-500 cursor-not-allowed' 
              : 'border-gray-300 focus:ring-2 focus:ring-metro-primary focus:border-transparent'
          ]"
        />
      </div>
    </div>

    <div v-if="!isLocked" class="flex gap-4">
      <button
        @click="handleRandomStations"
        class="flex-1 px-6 py-3 bg-metro-secondary text-white rounded-lg hover:bg-green-700 transition font-medium"
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
import { computed } from 'vue'
import { useGameStore } from '@/stores/game'

const gameStore = useGameStore()

// 游戏进行中或结果页时锁定站点选择
const isLocked = computed(() => gameStore.gameStatus === 'playing' || gameStore.gameStatus === 'result')

const handleRandomStations = async () => {
  await gameStore.generateRandomStations()
}

const handleStartGame = () => {
  if (gameStore.startStation && gameStore.endStation) {
    gameStore.setStations(gameStore.startStation, gameStore.endStation)
  }
}
</script>

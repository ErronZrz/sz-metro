<template>
  <div class="space-y-6">
    <!-- Result Message (只显示答对的情况) -->
    <div class="p-6 rounded-lg border-2 bg-green-50 border-green-500">
      <h3 class="text-2xl font-bold mb-2 text-green-700">
        🎉 恭喜！答对了！
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

    <!-- All Shortest Paths (答对时自动显示) -->
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

    <!-- Action Buttons -->
    <div class="text-center">
      <button
        @click="handleNewGame"
        class="px-8 py-3 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition font-medium"
      >
        🎮 再来一局
      </button>
    </div>
  </div>
</template>

<script setup>
import { useGameStore } from '@/stores/game'

const gameStore = useGameStore()

const handleNewGame = () => {
  gameStore.newGame()
}

const handleReset = () => {
  gameStore.resetGame()
}

// 格式化路径，标注换乘站
const formatPathWithTransfers = (pathData) => {
  if (typeof pathData === 'string') {
    // 如果是字符串格式（带换乘标注）
    return pathData.replace(/\(/g, '<span class="text-orange-600 font-semibold">(')
                    .replace(/\)/g, ')</span>')
  } else if (Array.isArray(pathData)) {
    // 如果是数组格式
    if (pathData.length > 0 && typeof pathData[0] === 'object' && pathData[0].station) {
      // 带换乘信息的对象数组
      return pathData.map(item => {
        if (item.transfer) {
          return `${item.station}<span class="text-orange-600 font-semibold">(${item.transfer})</span>`
        }
        return item.station
      }).join(' → ')
    } else {
      // 普通站点数组
      return pathData.join(' → ')
    }
  }
  return String(pathData)
}
</script>

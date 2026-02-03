<template>
  <div class="space-y-4">
    <div class="flex gap-4 mb-4">
      <button
        @click="gameStore.selectAllLines"
        :disabled="gameStore.isPlaying"
        class="px-4 py-2 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
      >
        <CheckCheck class="w-4 h-4" /> 全选
      </button>
      <button
        @click="gameStore.clearLines"
        :disabled="gameStore.isPlaying"
        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
      >
        <XCircle class="w-4 h-4" /> 清空
      </button>
    </div>

    <div class="flex flex-wrap gap-4">
      <span
        v-for="line in gameStore.allLines"
        :key="line"
        @click="!gameStore.isPlaying && gameStore.toggleLine(line)"
        class="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-all"
        :class="{
          'cursor-pointer hover:opacity-80': !gameStore.isPlaying,
          'cursor-not-allowed': gameStore.isPlaying,
          'ring-2 ring-offset-2 ring-gray-400': gameStore.selectedLines.includes(line)
        }"
        :style="getLineStyle(line)"
      >
        {{ line }}
      </span>
    </div>

    <div v-if="gameStore.hasSelectedLines" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
      <p class="text-green-700 flex items-center gap-1">
        <CheckCircle class="w-5 h-5" /> 已选择 {{ gameStore.selectedLines.length }} 条线路: 
        <span class="font-semibold">{{ gameStore.sortedSelectedLines.join(', ') }}</span>
      </p>
    </div>

    <!-- Selected Lines Map Preview -->
    <div v-if="gameStore.hasSelectedLines" class="mt-4">
      <SelectedLinesMap :selectedLines="gameStore.sortedSelectedLines" />
    </div>
  </div>
</template>

<script setup>
import { useGameStore } from '@/stores/game'
import SelectedLinesMap from './SelectedLinesMap.vue'
import { CheckCircle, CheckCheck, XCircle } from 'lucide-vue-next'

const gameStore = useGameStore()

// Get line style with background color
const getLineStyle = (lineName) => {
  const lineData = gameStore.linesData[lineName]
  const color = lineData?.color || '#6B7280'
  const isSelected = gameStore.selectedLines.includes(lineName)
  
  return {
    backgroundColor: isSelected ? color : `${color}40`,
    color: isSelected ? '#FFFFFF' : color,
    opacity: gameStore.isPlaying ? 0.6 : 1
  }
}
</script>

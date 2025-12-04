<template>
  <div class="space-y-4">
    <div class="flex gap-4 mb-4">
      <button
        @click="gameStore.selectAllLines"
        :disabled="gameStore.isPlaying"
        class="px-4 py-2 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        全选
      </button>
      <button
        @click="gameStore.clearLines"
        :disabled="gameStore.isPlaying"
        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        清空
      </button>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      <label
        v-for="line in gameStore.allLines"
        :key="line"
        class="flex items-center space-x-2 p-3 border-2 rounded-lg transition"
        :class="{
          'border-metro-primary bg-blue-50': gameStore.selectedLines.includes(line),
          'border-gray-200': !gameStore.selectedLines.includes(line),
          'cursor-pointer hover:bg-gray-50': !gameStore.isPlaying,
          'cursor-not-allowed opacity-60': gameStore.isPlaying
        }"
      >
        <input
          type="checkbox"
          :checked="gameStore.selectedLines.includes(line)"
          @change="gameStore.toggleLine(line)"
          :disabled="gameStore.isPlaying"
          class="w-4 h-4 text-metro-primary rounded focus:ring-metro-primary disabled:cursor-not-allowed"
        />
        <span class="font-medium text-gray-700">{{ line }}</span>
      </label>
    </div>

    <div v-if="gameStore.hasSelectedLines" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
      <p class="text-green-700">
        ✅ 已选择 {{ gameStore.selectedLines.length }} 条线路: 
        <span class="font-semibold">{{ gameStore.selectedLines.join(', ') }}</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { useGameStore } from '@/stores/game'

const gameStore = useGameStore()
</script>

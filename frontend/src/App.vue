<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <header class="text-center mb-8">
        <h1 class="text-4xl font-bold text-white mb-2">🚇 深圳地铁寻路挑战</h1>
        <p class="text-white/80">找出两个站点之间的最短路径</p>
      </header>

      <!-- Main Game Card -->
      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <!-- Error Message -->
        <div v-if="gameStore.error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-600">{{ gameStore.error }}</p>
        </div>

        <!-- Loading Indicator -->
        <div v-if="gameStore.loading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-metro-primary"></div>
          <p class="mt-4 text-gray-600">加载中...</p>
        </div>

        <!-- Game Content -->
        <div v-else>
          <!-- Step 1: Line Selection -->
          <section class="mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">📍 步骤 1: 选择线路</h2>
            <LineSelector />
          </section>

          <!-- Step 2: Station Selection -->
          <section v-if="gameStore.hasSelectedLines" class="mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">🎯 步骤 2: 设定起终点</h2>
            <StationSelector />
          </section>

          <!-- Step 3: Path Input -->
          <section v-if="gameStore.gameStatus === 'playing'" class="mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">✏️ 步骤 3: 输入你的路径</h2>
            <PathInput />
          </section>

          <!-- Step 4: Results (只在答对时显示) -->
          <section v-if="gameStore.gameStatus === 'result'">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">🎉 恭喜答对！</h2>
            <GameResult />
          </section>
        </div>
      </div>

      <!-- Footer -->
      <footer class="text-center mt-8 text-white/60">
        <p>深圳地铁寻路游戏 v1.0 | 使用 Vue 3 + FastAPI 构建</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useGameStore } from '@/stores/game'
import LineSelector from '@/components/LineSelector.vue'
import StationSelector from '@/components/StationSelector.vue'
import PathInput from '@/components/PathInput.vue'
import GameResult from '@/components/GameResult.vue'

const gameStore = useGameStore()

onMounted(() => {
  gameStore.loadLines()
})
</script>

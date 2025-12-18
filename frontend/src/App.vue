<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <header class="text-center mb-8">
        <h1 class="text-4xl font-bold text-white mb-2">{{ gameStore.currentCityConfig.title }}</h1>
        <p class="text-white/80">{{ gameStore.currentCityConfig.subtitle }}</p>
        <!-- City Switcher -->
        <div class="mt-4 flex justify-center gap-3">
          <router-link
            to="/"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            :class="city === 'sz' ? 'bg-white text-blue-600' : 'bg-white/20 text-white hover:bg-white/30'"
          >
            <img :src="szLogo" alt="深圳地铁" class="w-6 h-6" />
            深圳地铁
          </router-link>
          <router-link
            to="/sh"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            :class="city === 'sh' ? 'bg-white text-blue-600' : 'bg-white/20 text-white hover:bg-white/30'"
          >
            <img :src="shLogo" alt="上海地铁" class="w-6 h-6" />
            上海地铁
          </router-link>
        </div>
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

          <!-- Query Mode: 只展示路线查询结果 -->
          <section v-if="gameStore.gameStatus === 'query'">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">🔍 路线查询结果</h2>
            <QueryResult />
          </section>
        </div>
      </div>

      <!-- Footer -->
      <footer class="text-center mt-8 text-white/60">
        <p>{{ gameStore.currentCityConfig.name }}地铁寻路挑战 v1.4 | 使用 Vue 3 + FastAPI 构建</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useGameStore } from '@/stores/game'
import LineSelector from '@/components/LineSelector.vue'
import StationSelector from '@/components/StationSelector.vue'
import PathInput from '@/components/PathInput.vue'
import GameResult from '@/components/GameResult.vue'
import QueryResult from '@/components/QueryResult.vue'
import szLogo from '@/assets/sz-logo.svg'
import shLogo from '@/assets/sh-logo.svg'

// Props from router
const props = defineProps({
  city: {
    type: String,
    default: 'sz'
  }
})

const gameStore = useGameStore()

// Initialize or switch city
onMounted(() => {
  gameStore.setCity(props.city)
})

// Watch for city prop changes (when navigating between routes)
watch(() => props.city, (newCity) => {
  gameStore.setCity(newCity)
})
</script>

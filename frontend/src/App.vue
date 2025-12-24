<template>
  <div class="min-h-screen py-8 px-4">
    <!-- City Switcher Dropdown - Top Right -->
    <div class="fixed top-4 right-4 z-50" ref="dropdownRef">
      <div class="relative">
        <!-- Selected City Button -->
        <button
          @click="toggleDropdown"
          class="flex items-center gap-2 bg-white/20 text-white px-3 py-2 pr-8 rounded-lg text-sm font-medium cursor-pointer hover:bg-white/30 transition-colors focus:outline-none focus:ring-2 focus:ring-white/50"
        >
          <img :src="cityLogos[city]" :alt="cityNames[city]" class="w-5 h-5" />
          <span>{{ cityNames[city] }}</span>
          <!-- Dropdown Arrow -->
          <div class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <svg 
              class="w-4 h-4 text-white transition-transform" 
              :class="{ 'rotate-180': isDropdownOpen }"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
        </button>
        <!-- Dropdown Menu -->
        <div 
          v-show="isDropdownOpen"
          class="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-lg overflow-hidden"
        >
          <button
            v-for="cityKey in cityKeys"
            :key="cityKey"
            @click="selectCity(cityKey)"
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors whitespace-nowrap"
            :class="{ 'bg-blue-50 text-blue-600': city === cityKey }"
          >
            <img :src="cityLogos[cityKey]" :alt="cityNames[cityKey]" class="w-5 h-5" />
            <span>{{ cityNames[cityKey] }}</span>
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <header class="text-center mb-8">
        <h1 class="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
          <img :src="cityLogos[city]" :alt="cityNames[city]" class="w-10 h-10" />
          <span>{{ gameStore.currentCityConfig.title }}</span>
        </h1>
        <p class="text-white/80">{{ gameStore.currentCityConfig.subtitle }}</p>
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
        <p>地铁寻路挑战 v1.4 | 使用 Vue 3 + FastAPI 构建</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, watch, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '@/stores/game'
import LineSelector from '@/components/LineSelector.vue'
import StationSelector from '@/components/StationSelector.vue'
import PathInput from '@/components/PathInput.vue'
import GameResult from '@/components/GameResult.vue'
import QueryResult from '@/components/QueryResult.vue'
import szLogo from '@/assets/sz-logo.svg'
import shLogo from '@/assets/sh-logo.svg'
import bjLogo from '@/assets/bj-logo.svg'
import gzLogo from '@/assets/gz-logo.svg'
import csLogo from '@/assets/cs-logo.svg'

// Props from router
const props = defineProps({
  city: {
    type: String,
    default: 'sz'
  }
})

const gameStore = useGameStore()
const router = useRouter()

// Dropdown state
const isDropdownOpen = ref(false)
const dropdownRef = ref(null)

// City data
const cityKeys = ['sz', 'sh', 'bj', 'gz', 'cs']
const cityNames = {
  sz: '深圳',
  sh: '上海',
  bj: '北京',
  gz: '广州',
  cs: '长沙'
}
const cityLogos = {
  sz: szLogo,
  sh: shLogo,
  bj: bjLogo,
  gz: gzLogo,
  cs: csLogo
}

// Toggle dropdown
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

// Select city
const selectCity = (cityKey) => {
  isDropdownOpen.value = false
  if (cityKey !== props.city) {
    const path = cityKey === 'sz' ? '/' : `/${cityKey}`
    router.push(path)
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isDropdownOpen.value = false
  }
}

// Initialize or switch city
onMounted(() => {
  gameStore.setCity(props.city)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Watch for city prop changes (when navigating between routes)
watch(() => props.city, (newCity) => {
  gameStore.setCity(newCity)
})
</script>

<template>
  <div class="space-y-4">
    <!-- Metro Map Visualization (Question Mode) -->
    <div class="mb-4">
      <MetroMap
        :mode="gameStore.showAnswer ? 'answer' : 'question'"
        :startStation="gameStore.startStation"
        :endStation="gameStore.endStation"
        :path="mapPath"
      />
    </div>

    <!-- All Shortest Paths (查看答案后显示，紧跟在地图下方) -->
    <div v-if="gameStore.showAnswer && gameStore.systemPaths.length > 0" class="p-4 bg-blue-50 rounded-lg border-2 border-blue-300">
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

    <!-- Error Message (温和提示) -->
    <div v-if="gameStore.validationResult && !gameStore.validationResult.is_shortest" 
         class="p-4 rounded-lg border-2"
         :class="{
           'bg-orange-50 border-orange-300': !gameStore.validationResult.valid,
           'bg-yellow-50 border-yellow-300': gameStore.validationResult.valid
         }">
      <div class="flex items-start gap-3">
        <span class="text-2xl">💡</span>
        <div class="flex-1">
          <h4 class="font-semibold mb-1"
              :class="{
                'text-orange-700': !gameStore.validationResult.valid,
                'text-yellow-700': gameStore.validationResult.valid
              }">
            {{ gameStore.validationResult.valid ? '路径可以优化' : '路径有误' }}
          </h4>
          <p class="text-sm"
             :class="{
               'text-orange-600': !gameStore.validationResult.valid,
               'text-yellow-600': gameStore.validationResult.valid
             }">
            {{ gameStore.validationResult.error_reason || gameStore.validationResult.message }}
          </p>
          <p class="text-sm mt-2 font-medium"
             :class="{
               'text-orange-700': !gameStore.validationResult.valid,
               'text-yellow-700': gameStore.validationResult.valid
             }">
            💪 请在下方继续修改你的路径，然后重新提交
          </p>
          <!-- 显示用户路径的换乘信息（仅当路径合法但非最优时） -->
          <div v-if="gameStore.validationResult.valid && gameStore.validationResult.user_path_annotated" 
               class="mt-3 p-2 bg-white rounded border border-yellow-200">
            <p class="text-xs text-gray-500 mb-1">你的路径：</p>
            <p class="text-sm text-gray-600" v-html="formatPathWithTransfers(gameStore.validationResult.user_path_annotated)"></p>
          </div>
        </div>
        <button
          @click="gameStore.validationResult = null"
          class="text-gray-400 hover:text-gray-600"
          title="关闭提示"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Input Area -->
    <div class="flex gap-2 items-end">
      <div class="flex-1">
        <label class="block text-sm font-medium text-gray-700 mb-1">添加站点</label>
        <SearchableSelect
          :value="currentStation"
          :options="gameStore.availableStations"
          :disabled="gameStore.availableStations.length === 0"
          placeholder="搜索并选择站点"
          @update:value="handleStationSelect"
          @confirm="handleStationConfirm"
        />
      </div>
      <button
        @click="addStation"
        :disabled="!currentStation"
        class="px-6 py-2 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        添加
      </button>
      <button
        @click="gameStore.clearPath"
        class="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition"
      >
        清空
      </button>
    </div>

    <!-- Current Path Display -->
    <div v-if="gameStore.userPath.length > 0" class="p-4 bg-gray-50 rounded-lg">
      <h3 class="text-sm font-medium text-gray-700 mb-3">当前路径 ({{ gameStore.userPath.length }} 站):</h3>
      <p class="text-xs text-gray-500 mb-3">💡 点击站点之间的 <span class="text-green-600 font-bold">+</span> 可以插入新站点</p>
      <div class="flex flex-wrap items-center gap-1">
        <template v-for="(station, index) in gameStore.userPath" :key="index">
          <!-- 站点标签 -->
          <div 
            class="flex items-center gap-1 px-3 py-2 rounded-lg"
            :class="{
              'bg-blue-100 border-2 border-blue-400': index === 0 || index === gameStore.userPath.length - 1,
              'bg-white border border-gray-300': index !== 0 && index !== gameStore.userPath.length - 1
            }"
          >
            <span v-if="index === 0" class="text-xs text-blue-600 mr-1">起</span>
            <span v-if="index === gameStore.userPath.length - 1" class="text-xs text-blue-600 mr-1">终</span>
            <span class="text-sm font-medium">{{ station }}</span>
            <!-- 只有中间站点可以删除 -->
            <button
              v-if="index !== 0 && index !== gameStore.userPath.length - 1"
              @click="gameStore.removeStation(index)"
              class="text-red-500 hover:text-red-700 ml-1"
              title="删除此站"
            >
              ✕
            </button>
          </div>
          
          <!-- 站点后的插入按钮（在终点前的所有位置都可以插入） -->
          <template v-if="index < gameStore.userPath.length - 1">
            <!-- 插入按钮（只要不是最后一站，都显示插入按钮，允许在终点前插入） -->
            <button
              v-if="insertIndex !== index + 1"
              @click="startInsert(index + 1)"
              class="w-6 h-6 flex items-center justify-center text-green-500 hover:text-green-700 hover:bg-green-100 rounded-full transition text-lg font-bold"
              title="在此处插入站点"
            >
              +
            </button>
            <!-- 插入下拉选择框 -->
            <div v-if="insertIndex === index + 1" class="flex items-center gap-1">
              <div class="w-36">
                <SearchableSelect
                  :ref="el => setInsertSelectRef(el, index + 1)"
                  :value="insertStation"
                  :options="insertAvailableStations"
                  placeholder="搜索站点"
                  size="small"
                  @update:value="handleInsertSelect"
                  @confirm="handleInsertConfirm"
                  @cancel="cancelInsert"
                />
              </div>
            </div>
          </template>
        </template>
      </div>
      
      <!-- Path Visualization -->
      <div class="mt-4 p-3 bg-white rounded border border-gray-200">
        <p class="text-sm text-gray-600">
          {{ gameStore.userPath.join(' → ') }}
        </p>
      </div>
    </div>

    <!-- Submit Button -->
    <button
      @click="handleSubmit"
      :disabled="!gameStore.canSubmit"
      class="w-full px-6 py-3 bg-metro-accent text-white rounded-lg hover:bg-orange-600 transition font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
    >
      🚀 {{ gameStore.validationResult && !gameStore.validationResult.is_shortest ? '重新提交' : '提交答案' }}
    </button>

    <!-- Show Answer Button (出题后就显示，答对后隐藏) -->
    <div v-if="!gameStore.showAnswer" class="text-center">
      <button
        @click="handleShowAnswer"
        class="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium"
      >
        🔎 查看正确答案
      </button>
    </div>

    <!-- 再来一局按钮（查看答案后显示，放在框外） -->
    <div v-if="gameStore.showAnswer" class="text-center">
      <button
        @click="gameStore.resetGame()"
        class="px-8 py-3 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition font-medium"
      >
        🎮 再来一局
      </button>
    </div>

    <!-- Hint -->
    <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p class="text-sm text-yellow-800">
        💡 提示: 换乘会增加 2.5 站的成本。尽量减少换乘次数！
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useGameStore } from '@/stores/game'
import SearchableSelect from './SearchableSelect.vue'
import MetroMap from './MetroMap.vue'

const gameStore = useGameStore()

// Map path: when answer is shown, use the first system path; otherwise empty
const mapPath = computed(() => {
  if (gameStore.showAnswer && gameStore.systemPaths.length > 0) {
    // Extract station names from the first system path
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

const currentStation = ref('')

// 插入功能的状态
const insertIndex = ref(null)  // 当前插入位置，null 表示没有在插入
const insertStation = ref('')  // 要插入的站名
const insertSelectRefs = ref({})  // 存储各个插入位置的 SearchableSelect 引用
const insertJustStarted = ref(false)  // 防止刚开始插入就被取消

// 插入时可用的站点（排除已在路径中的站点）
const insertAvailableStations = computed(() => {
  return gameStore.availableStations.filter(station => !gameStore.userPath.includes(station))
})

// 设置插入选择框的引用
const setInsertSelectRef = (el, index) => {
  if (el) {
    insertSelectRefs.value[index] = el
  }
}

// 处理站点选择
const handleStationSelect = (station) => {
  currentStation.value = station
}

// 处理站点确认（回车直接添加）
const handleStationConfirm = (station) => {
  if (station && station.trim()) {
    gameStore.addStation(station.trim())
    currentStation.value = ''
  }
}

// 处理插入站点选择
const handleInsertSelect = (station) => {
  insertStation.value = station
}

// 处理插入站点确认（选中即插入，并自动进入下一个插入位置）
const handleInsertConfirm = async (station) => {
  if (station && station.trim() && insertIndex.value !== null) {
    const trimmedStation = station.trim()
    // Check if station already exists in path
    if (gameStore.userPath.includes(trimmedStation)) {
      return  // Station already in path, don't insert
    }
    
    const currentInsertIndex = insertIndex.value
    gameStore.insertStation(trimmedStation, currentInsertIndex)
    insertStation.value = ''
    
    // Auto-advance to next insert position (after the just-inserted station)
    // The new station is now at currentInsertIndex, so next insert position is currentInsertIndex + 1
    const nextInsertIndex = currentInsertIndex + 1
    
    // Check if next position is valid (not after the last station / end station)
    if (nextInsertIndex < gameStore.userPath.length) {
      insertIndex.value = nextInsertIndex
      // Wait for DOM update then focus the new input
      await nextTick()
      // Need to wait a bit more for the new SearchableSelect to be mounted
      await nextTick()
      const selectRef = insertSelectRefs.value[nextInsertIndex]
      if (selectRef && selectRef.focus) {
        selectRef.focus()
      }
    } else {
      cancelInsert()
    }
  }
}

const addStation = () => {
  if (currentStation.value.trim()) {
    gameStore.addStation(currentStation.value.trim())
    currentStation.value = ''
  }
}

// 开始在指定位置插入
const startInsert = async (index) => {
  // Set flag to prevent immediate cancellation from click outside event
  insertJustStarted.value = true
  insertIndex.value = index
  insertStation.value = ''
  // Wait for DOM update then focus the input
  await nextTick()
  await nextTick()  // Need extra tick for component to mount
  const selectRef = insertSelectRefs.value[index]
  if (selectRef && selectRef.focus) {
    selectRef.focus()
  }
  // Reset flag after a short delay to allow click event to complete
  setTimeout(() => {
    insertJustStarted.value = false
  }, 100)
}

// 取消插入
const cancelInsert = () => {
  // Ignore cancel if insert was just started (prevents immediate cancellation from click outside)
  if (insertJustStarted.value) {
    return
  }
  insertIndex.value = null
  insertStation.value = ''
  insertSelectRefs.value = {}
}

const handleSubmit = async () => {
  await gameStore.submitPath()
}

const handleShowAnswer = async () => {
  if (confirm('确定要查看正确答案吗？')) {
    await gameStore.fetchAndRevealAnswer()
  }
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

<template>
  <div class="space-y-4">
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
    <div class="flex gap-2">
      <input
        v-model="currentStation"
        @keyup.enter="addStation"
        type="text"
        placeholder="输入站名后按回车添加"
        class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-metro-primary focus:border-transparent"
      />
      <button
        @click="addStation"
        class="px-6 py-2 bg-metro-primary text-white rounded-lg hover:bg-blue-700 transition"
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
        <!-- 首站前的插入按钮 -->
        <button
          v-if="insertIndex !== 0"
          @click="startInsert(0)"
          class="w-6 h-6 flex items-center justify-center text-green-500 hover:text-green-700 hover:bg-green-100 rounded-full transition text-lg font-bold"
          title="在此处插入站点"
        >
          +
        </button>
        <!-- 首站前的插入输入框 -->
        <div v-if="insertIndex === 0" class="flex items-center gap-1">
          <input
            ref="insertInputRef"
            v-model="insertStation"
            @keyup.enter="confirmInsert"
            @keyup.escape="cancelInsert"
            type="text"
            placeholder="输入站名"
            class="w-24 px-2 py-1 text-sm border border-green-400 rounded focus:ring-2 focus:ring-green-400 focus:border-transparent"
          />
          <button @click="confirmInsert" class="text-green-600 hover:text-green-800 text-sm">✓</button>
          <button @click="cancelInsert" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
        </div>

        <template v-for="(station, index) in gameStore.userPath" :key="index">
          <!-- 站点标签 -->
          <div class="flex items-center gap-1 px-3 py-2 bg-white border border-gray-300 rounded-lg">
            <span class="text-sm font-medium">{{ station }}</span>
            <button
              @click="gameStore.removeStation(index)"
              class="text-red-500 hover:text-red-700 ml-1"
              title="删除此站"
            >
              ✕
            </button>
          </div>
          
          <!-- 站点后的插入按钮（非最后一站才显示） -->
          <template v-if="index < gameStore.userPath.length - 1">
            <!-- 插入按钮 -->
            <button
              v-if="insertIndex !== index + 1"
              @click="startInsert(index + 1)"
              class="w-6 h-6 flex items-center justify-center text-green-500 hover:text-green-700 hover:bg-green-100 rounded-full transition text-lg font-bold"
              title="在此处插入站点"
            >
              +
            </button>
            <!-- 插入输入框 -->
            <div v-if="insertIndex === index + 1" class="flex items-center gap-1">
              <input
                ref="insertInputRef"
                v-model="insertStation"
                @keyup.enter="confirmInsert"
                @keyup.escape="cancelInsert"
                type="text"
                placeholder="输入站名"
                class="w-24 px-2 py-1 text-sm border border-green-400 rounded focus:ring-2 focus:ring-green-400 focus:border-transparent"
              />
              <button @click="confirmInsert" class="text-green-600 hover:text-green-800 text-sm">✓</button>
              <button @click="cancelInsert" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
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

    <!-- All Shortest Paths (查看答案后显示) -->
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
      
      <!-- 再来一局按钮 -->
      <div class="mt-4 text-center">
        <button
          @click="gameStore.resetGame()"
          class="px-8 py-3 bg-metro-secondary text-white rounded-lg hover:bg-green-700 transition font-medium"
        >
          🎮 再来一局
        </button>
      </div>
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
import { ref, nextTick } from 'vue'
import { useGameStore } from '@/stores/game'

const gameStore = useGameStore()
const currentStation = ref('')

// 插入功能的状态
const insertIndex = ref(null)  // 当前插入位置，null 表示没有在插入
const insertStation = ref('')  // 要插入的站名
const insertInputRef = ref(null)  // 插入输入框的引用

const addStation = () => {
  if (currentStation.value.trim()) {
    gameStore.addStation(currentStation.value.trim())
    currentStation.value = ''
  }
}

// 开始在指定位置插入
const startInsert = async (index) => {
  insertIndex.value = index
  insertStation.value = ''
  await nextTick()
  // 自动聚焦到输入框
  if (insertInputRef.value) {
    const input = Array.isArray(insertInputRef.value) ? insertInputRef.value[0] : insertInputRef.value
    input?.focus()
  }
}

// 确认插入
const confirmInsert = () => {
  if (insertStation.value.trim() && insertIndex.value !== null) {
    gameStore.insertStation(insertStation.value.trim(), insertIndex.value)
  }
  cancelInsert()
}

// 取消插入
const cancelInsert = () => {
  insertIndex.value = null
  insertStation.value = ''
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

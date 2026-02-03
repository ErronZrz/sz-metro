<template>
  <div class="metro-map-container">
    <div class="map-header flex justify-between items-center mb-2">
      <h4 class="font-semibold text-gray-700 flex items-center gap-1">
        <MapPin v-if="mode === 'question'" class="w-5 h-5" />
        <Map v-else class="w-5 h-5" />
        {{ mode === 'question' ? '起终点位置' : '路径可视化' }}
      </h4>
      <div class="flex gap-2">
        <button 
          @click="zoomIn" 
          class="p-1.5 bg-gray-200 rounded hover:bg-gray-300"
          title="放大"
        ><ZoomIn class="w-4 h-4" /></button>
        <button 
          @click="zoomOut" 
          class="p-1.5 bg-gray-200 rounded hover:bg-gray-300"
          title="缩小"
        ><ZoomOut class="w-4 h-4" /></button>
        <button 
          @click="resetView" 
          class="p-1.5 bg-gray-200 rounded hover:bg-gray-300"
          title="重置视图"
        ><RotateCcw class="w-4 h-4" /></button>
      </div>
    </div>
    
    <div 
      ref="mapWrapper"
      class="map-wrapper border rounded-lg bg-gray-50 overflow-hidden"
      @mousedown="startPan"
      @mousemove="pan"
      @mouseup="endPan"
      @mouseleave="endPan"
      @wheel.prevent="handleWheel"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <svg 
        ref="svgElement"
        :viewBox="viewBox"
        class="metro-map"
        :style="{ cursor: isPanning ? 'grabbing' : 'grab' }"
      >
        <defs>
          <!-- Glow filter for highlighted stations -->
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          <!-- Arrow marker for path direction -->
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#3B82F6"/>
          </marker>
        </defs>

        <!-- Background grid (subtle) -->
        <g class="grid" opacity="0.1">
          <line v-for="x in gridLinesX" :key="'gx'+x" :x1="x" :y1="mapBounds.minY - 50" :x2="x" :y2="mapBounds.maxY + 50" stroke="#888" stroke-width="0.5"/>
          <line v-for="y in gridLinesY" :key="'gy'+y" :x1="mapBounds.minX - 50" :y1="y" :x2="mapBounds.maxX + 50" :y2="y" stroke="#888" stroke-width="0.5"/>
        </g>

        <!-- Answer Mode: Show path lines with smooth curves -->
        <g v-if="mode === 'answer' && pathStations.length > 1" class="path-lines">
          <g v-for="(segment, index) in smoothPathSegments" :key="'seg'+index">
            <!-- Main path curve -->
            <path
              :d="segment.path"
              :stroke="segment.color"
              stroke-width="6"
              stroke-linecap="round"
              fill="none"
              class="path-line-animated"
              :style="{ animationDelay: `${index * 0.1}s` }"
            />
          </g>
        </g>

        <!-- Answer Mode: Show path stations -->
        <g v-if="mode === 'answer'" class="path-stations">
          <g 
            v-for="(station, index) in pathStations" 
            :key="'path-'+station"
            class="station-group"
          >
            <!-- Station circle -->
            <circle
              :cx="getStationCoord(station)?.x"
              :cy="getStationCoord(station)?.y"
              :r="isEndpoint(station) ? 10 : 6"
              :fill="isEndpoint(station) ? (station === startStation ? '#22C55E' : '#EF4444') : 'white'"
              :stroke="isEndpoint(station) ? '#333' : (pathStationInfo[station]?.isTransfer ? '#666' : (pathStationInfo[station]?.lineColor || '#333'))"
              stroke-width="3"
              class="station-dot"
              :class="{ 'station-endpoint': isEndpoint(station) }"
            />
            <!-- Transfer station inner dot -->
            <circle
              v-if="!isEndpoint(station) && pathStationInfo[station]?.isTransfer"
              :cx="getStationCoord(station)?.x"
              :cy="getStationCoord(station)?.y"
              r="2"
              fill="#666"
              pointer-events="none"
            />
            <!-- Station label with smart positioning -->
            <text
              :x="getStationCoord(station)?.x + getLabelOffset(station).x"
              :y="getStationCoord(station)?.y + getLabelOffset(station).y"
              :text-anchor="getLabelOffset(station).anchor"
              class="station-label"
              :class="{ 'font-bold': isEndpoint(station) }"
              font-size="16"
              :fill="station === startStation ? '#166534' : (station === endStation ? '#991B1B' : '#374151')"
            >
              {{ station }}
            </text>
            <!-- Endpoint marker -->
            <text
              v-if="isEndpoint(station)"
              :x="getStationCoord(station)?.x"
              :y="getStationCoord(station)?.y + 4"
              text-anchor="middle"
              font-size="12"
              fill="white"
              font-weight="bold"
            >
              {{ station === startStation ? '起' : '终' }}
            </text>
          </g>
        </g>

        <!-- Question Mode: Only show start and end markers -->
        <g v-if="mode === 'question'" class="question-markers">
          <!-- Start station -->
          <g v-if="startStation && getStationCoord(startStation)" class="start-marker">
            <!-- Pulse animation background -->
            <circle
              :cx="getStationCoord(startStation)?.x"
              :cy="getStationCoord(startStation)?.y"
              r="14"
              fill="#22C55E"
              opacity="0.3"
              class="pulse-circle"
            />
            <circle
              :cx="getStationCoord(startStation)?.x"
              :cy="getStationCoord(startStation)?.y"
              r="10"
              fill="#22C55E"
              stroke="#333"
              stroke-width="2.5"
              class="station-endpoint"
            />
            <text
              :x="getStationCoord(startStation)?.x"
              :y="getStationCoord(startStation)?.y + 4"
              text-anchor="middle"
              font-size="12"
              fill="white"
              font-weight="bold"
            >起</text>
            <text
              :x="getStationCoord(startStation)?.x"
              :y="getStationCoord(startStation)?.y - 20"
              text-anchor="middle"
              font-size="16"
              fill="#166534"
              font-weight="bold"
            >{{ startStation }}</text>
          </g>

          <!-- End station -->
          <g v-if="endStation && getStationCoord(endStation)" class="end-marker">
            <!-- Pulse animation background -->
            <circle
              :cx="getStationCoord(endStation)?.x"
              :cy="getStationCoord(endStation)?.y"
              r="14"
              fill="#EF4444"
              opacity="0.3"
              class="pulse-circle"
            />
            <circle
              :cx="getStationCoord(endStation)?.x"
              :cy="getStationCoord(endStation)?.y"
              r="10"
              fill="#EF4444"
              stroke="#333"
              stroke-width="2.5"
              class="station-endpoint"
            />
            <text
              :x="getStationCoord(endStation)?.x"
              :y="getStationCoord(endStation)?.y + 4"
              text-anchor="middle"
              font-size="12"
              fill="white"
              font-weight="bold"
            >终</text>
            <text
              :x="getStationCoord(endStation)?.x"
              :y="getStationCoord(endStation)?.y - 20"
              text-anchor="middle"
              font-size="16"
              fill="#991B1B"
              font-weight="bold"
            >{{ endStation }}</text>
          </g>

          <!-- Dashed line connecting start and end (shows approximate distance) -->
          <line
            v-if="startStation && endStation && getStationCoord(startStation) && getStationCoord(endStation)"
            :x1="getDashedLineEndpoint(startStation, endStation).x1"
            :y1="getDashedLineEndpoint(startStation, endStation).y1"
            :x2="getDashedLineEndpoint(startStation, endStation).x2"
            :y2="getDashedLineEndpoint(startStation, endStation).y2"
            stroke="#9CA3AF"
            stroke-width="2"
            stroke-dasharray="8,4"
            opacity="0.5"
          />
        </g>
      </svg>
    </div>

    <!-- Legend -->
    <div class="map-legend mt-2 flex flex-wrap gap-4 text-xs text-gray-600">
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-green-500"></span>
        <span>起点</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-red-500"></span>
        <span>终点</span>
      </div>
      <div v-if="mode === 'answer'" class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full border-2 border-gray-400 bg-white"></span>
        <span>途经站点</span>
      </div>
      <div v-if="mode === 'answer'" class="flex items-center gap-1">
        <span class="transfer-station-legend"></span>
        <span>换乘站</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '@/services/api'
import { useGameStore } from '@/stores/game'
import { MapPin, Map, ZoomIn, ZoomOut, RotateCcw } from 'lucide-vue-next'

const props = defineProps({
  // 'question' - only show start/end, 'answer' - show full path
  mode: {
    type: String,
    default: 'question',
    validator: (value) => ['question', 'answer'].includes(value)
  },
  startStation: {
    type: String,
    default: ''
  },
  endStation: {
    type: String,
    default: ''
  },
  // Array of station names for the path (in order) - legacy prop, use pathData instead
  path: {
    type: Array,
    default: () => []
  },
  // Structured path data from backend: {stations, lines, transfers, annotated}
  pathData: {
    type: Object,
    default: () => null
  },
  // Line colors for path segments (optional)
  lineInfo: {
    type: Object,
    default: () => ({})
  }
})

// Map data
const coordinates = ref({})
const linesData = ref({})
const loading = ref(true)

// View control
const svgElement = ref(null)
const mapWrapper = ref(null)
const scale = ref(1)
const panOffset = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const lastPanPosition = ref({ x: 0, y: 0 })

// Touch handling
const lastTouchDistance = ref(0)

// Map bounds
const mapBounds = computed(() => {
  const stations = Object.values(coordinates.value)
  if (stations.length === 0) {
    return { minX: 0, maxX: 1000, minY: 0, maxY: 600 }
  }
  const xs = stations.map(s => s.x)
  const ys = stations.map(s => s.y)
  return {
    minX: Math.min(...xs) - 100,
    maxX: Math.max(...xs) + 100,
    minY: Math.min(...ys) - 100,
    maxY: Math.max(...ys) + 100
  }
})

// Viewbox calculation
const viewBox = computed(() => {
  const bounds = mapBounds.value
  const width = (bounds.maxX - bounds.minX) / scale.value
  const height = (bounds.maxY - bounds.minY) / scale.value
  const x = bounds.minX + panOffset.value.x
  const y = bounds.minY + panOffset.value.y
  return `${x} ${y} ${width} ${height}`
})

// Grid lines for subtle background
const gridLinesX = computed(() => {
  const lines = []
  const bounds = mapBounds.value
  for (let x = Math.floor(bounds.minX / 100) * 100; x <= bounds.maxX; x += 100) {
    lines.push(x)
  }
  return lines
})

const gridLinesY = computed(() => {
  const lines = []
  const bounds = mapBounds.value
  for (let y = Math.floor(bounds.minY / 100) * 100; y <= bounds.maxY; y += 100) {
    lines.push(y)
  }
  return lines
})

// Path stations (filtered to only include valid stations with coordinates)
const pathStations = computed(() => {
  // Prefer structured pathData from backend
  if (props.pathData && props.pathData.stations) {
    return props.pathData.stations.filter(station => coordinates.value[station])
  }
  // Fallback to path array prop
  return props.path.filter(station => coordinates.value[station])
})

// Helper function to get line color by name
const getLineColor = (lineName) => {
  if (!lineName) return '#3B82F6'
  const lineData = linesData.value[lineName]
  return lineData?.color || '#3B82F6'
}

// Path segments with colors - use backend data when available
const pathSegments = computed(() => {
  const segments = []
  const path = pathStations.value
  
  // If we have structured data from backend, use it directly
  if (props.pathData && props.pathData.lines && props.pathData.lines.length === path.length) {
    const lines = props.pathData.lines
    for (let i = 0; i < path.length - 1; i++) {
      const from = path[i]
      const to = path[i + 1]
      // lines[i+1] represents "which line to take to reach station i+1"
      // So for segment from i to i+1, use lines[i+1]
      const lineName = lines[i + 1] || lines[i] || ''
      const color = getLineColor(lineName)
      segments.push({ from, to, color, lineName })
    }
    return segments
  }
  
  // Fallback: compute segments locally (for legacy compatibility)
  for (let i = 0; i < path.length - 1; i++) {
    const from = path[i]
    const to = path[i + 1]
    
    let color = '#3B82F6' // Default blue
    let lineName = ''
    
    // Find the line that connects these two stations
    for (const [lineNameKey, lineData] of Object.entries(linesData.value)) {
      const stations = lineData.stations || []
      const branchStations = lineData.branch_stations || []
      const isLoop = lineData.is_loop || false  // Support loop lines
      const oneWayLoop = lineData.one_way_loop || []  // Support one-way loops
      
      // Check main line stations
      const fromIdx = stations.indexOf(from)
      const toIdx = stations.indexOf(to)
      
      if (fromIdx !== -1 && toIdx !== -1) {
        const diff = Math.abs(fromIdx - toIdx)
        // Check adjacent: diff == 1 OR (loop line and diff == len - 1)
        let isAdjacent = diff === 1 || (isLoop && diff === stations.length - 1)
        
        // Check one-way loop adjacency
        if (!isAdjacent && oneWayLoop.length >= 2) {
          const fromLoopIdx = oneWayLoop.indexOf(from)
          const toLoopIdx = oneWayLoop.indexOf(to)
          if (fromLoopIdx !== -1 && toLoopIdx !== -1) {
            // In one-way loop: from -> to is valid if toLoopIdx = (fromLoopIdx + 1) % len
            // OR: to -> from loop closure (last -> first)
            const forwardAdjacent = (fromLoopIdx + 1) % oneWayLoop.length === toLoopIdx
            const backwardAdjacent = (toLoopIdx + 1) % oneWayLoop.length === fromLoopIdx
            isAdjacent = forwardAdjacent || backwardAdjacent
          }
        }
        
        if (isAdjacent) {
          color = lineData.color || color
          lineName = lineNameKey
          break
        }
      }
      
      // Check branch stations (Y-branch lines)
      if (branchStations.length > 0) {
        const fromBranchIdx = branchStations.indexOf(from)
        const toBranchIdx = branchStations.indexOf(to)
        
        if (fromBranchIdx !== -1 && toBranchIdx !== -1) {
          const diff = Math.abs(fromBranchIdx - toBranchIdx)
          if (diff === 1) {
            color = lineData.color || color
            lineName = lineNameKey
            break
          }
        }
      }
    }
    
    segments.push({ from, to, color, lineName })
  }
  
  return segments
})

// Compute station info for path display (transfer status and line color)
const pathStationInfo = computed(() => {
  const path = pathStations.value
  const segments = pathSegments.value
  const result = {}
  
  // Get transfer indices from backend data
  const transferIndices = new Set(props.pathData?.transfers || [])
  
  for (let i = 0; i < path.length; i++) {
    const station = path[i]
    
    // Skip endpoints - they have their own styling
    if (station === props.startStation || station === props.endStation) {
      result[station] = { isTransfer: false, lineColor: '#333' }
      continue
    }
    
    // Use backend transfer data if available
    const isTransfer = transferIndices.has(i)
    
    // Get line color from segment
    const prevSegment = i > 0 ? segments[i - 1] : null
    const nextSegment = i < path.length - 1 ? segments[i] : null
    const lineColor = nextSegment?.color || prevSegment?.color || '#333'
    
    result[station] = { isTransfer, lineColor }
  }
  
  return result
})

// Generate smooth path using Catmull-Rom spline converted to cubic Bezier
const smoothPathSegments = computed(() => {
  const segments = []
  const path = pathStations.value
  const points = path.map(station => getStationCoord(station)).filter(p => p)
  
  if (points.length < 2) return segments
  
  // Catmull-Rom to Cubic Bezier conversion
  // tension: 0.5 is the default Catmull-Rom tension (can adjust for tighter/looser curves)
  const tension = 0.5
  
  for (let i = 0; i < points.length - 1; i++) {
    // Get four points for Catmull-Rom (p0, p1, p2, p3)
    // p1 and p2 are the actual segment endpoints
    const p0 = i > 0 ? points[i - 1] : points[i]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = i < points.length - 2 ? points[i + 2] : points[i + 1]
    
    // Convert Catmull-Rom to cubic Bezier control points
    // The formula converts the Catmull-Rom spline to equivalent Bezier curve
    const cp1x = p1.x + (p2.x - p0.x) * tension / 3
    const cp1y = p1.y + (p2.y - p0.y) * tension / 3
    const cp2x = p2.x - (p3.x - p1.x) * tension / 3
    const cp2y = p2.y - (p3.y - p1.y) * tension / 3
    
    // Create SVG path command: M = move to, C = cubic Bezier curve
    const pathData = `M ${p1.x} ${p1.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`
    
    // Get color from original segments
    const color = pathSegments.value[i]?.color || '#3B82F6'
    
    segments.push({ path: pathData, color })
  }
  
  return segments
})

// Helper functions
const getStationCoord = (stationName) => {
  return coordinates.value[stationName]
}

const isEndpoint = (station) => {
  return station === props.startStation || station === props.endStation
}

// Calculate dashed line endpoints to stop at circle border (not inside)
const getDashedLineEndpoint = (startSt, endSt) => {
  const startCoord = coordinates.value[startSt]
  const endCoord = coordinates.value[endSt]
  
  if (!startCoord || !endCoord) {
    return { x1: 0, y1: 0, x2: 0, y2: 0 }
  }
  
  // Calculate direction vector
  const dx = endCoord.x - startCoord.x
  const dy = endCoord.y - startCoord.y
  const distance = Math.sqrt(dx * dx + dy * dy)
  
  if (distance === 0) {
    return { x1: startCoord.x, y1: startCoord.y, x2: endCoord.x, y2: endCoord.y }
  }
  
  // Normalize direction
  const nx = dx / distance
  const ny = dy / distance
  
  // Circle radius + stroke-width/2 = 10 + 1.25 ≈ 11.5
  const offset = 11.5
  
  return {
    x1: startCoord.x + nx * offset,
    y1: startCoord.y + ny * offset,
    x2: endCoord.x - nx * offset,
    y2: endCoord.y - ny * offset
  }
}

// 使用改进算法计算标签位置：
// 1. 将所有线段标记为占用区域
// 2. 对于每个站点 D，根据附近线段对方向进行惩罚：
//    - 直接惩罚相邻站点（C 和 E）的方向
//    - 向前（BC, AB, ...）和向后（EF, FG, ...）遍历，惩罚经过 D 附近的线段方向（距离 < 阈值）
//    - 当线段距离 D 足够远时停止遍历
// 3. 惩罚前一个站点标签使用的方向以避免重叠
// 4. 优先选择角平分线的反方向
// 5. 两趟择优：正向和反向各计算一次，选择最低分更高的结果
const labelPositions = computed(() => {
  const path = pathStations.value
  
  // === 调试：指定要调试的站点名称 ===
  const DEBUG_STATION = '新塘围'
  
  // === 配置：所有评分参数 ===
  const CONFIG = {
    // 文本渲染
    TEXT_CHAR_WIDTH: 15,              // 每个字符的估计宽度
    TEXT_HEIGHT: 16,                  // 文本高度（像素）
    
    // 标签位置偏移（普通站点）
    LABEL_TOP_Y: -10,
    LABEL_BOTTOM_Y: 22,
    LABEL_SIDE_X: 8,
    LABEL_CORNER_X: 4,
    LABEL_CORNER_TOP_Y: -6,
    LABEL_CORNER_BOTTOM_Y: 18,
    LABEL_SIDE_Y: 6,
    
    // 标签位置偏移（端点站点）
    ENDPOINT_LABEL_TOP_Y: -15,
    ENDPOINT_LABEL_BOTTOM_Y: 27,
    ENDPOINT_LABEL_SIDE_X: 13,
    ENDPOINT_LABEL_CORNER_X: 8,
    ENDPOINT_LABEL_CORNER_TOP_Y: -10,
    ENDPOINT_LABEL_CORNER_BOTTOM_Y: 22,
    
    // 角度阈值
    PREFERRED_BONUS_ANGLE_THRESHOLD: 90,    // 优选方向奖励：0° = 满奖励，90° = 0
    INWARD_BONUS_ANGLE_MAX: 165,            // 内向奖励：此角度及以上获得满奖励
    INWARD_BONUS_ANGLE_MIN: 90,             // 内向奖励：此角度及以下无奖励
    
    // 碰撞检测
    BOXES_OVERLAP_PADDING: 4,               // 盒子重叠检测的默认内边距
    SEGMENT_BOX_OVERLAP_PADDING: 4,         // 线段-盒子重叠检测的内边距
    LABEL_COLLISION_PADDING: 3,             // 标签碰撞检测的内边距
    SEGMENT_COLLISION_PADDING: 3,           // 线段碰撞检测的内边距
    OVERLAP_RATIO_DIVISOR: 15,              // 重叠比例计算的除数
    
    // 惩罚值
    SEGMENT_INTERSECTION_PENALTY_MIN: 120,  // 线段相交的最小惩罚
    SEGMENT_INTERSECTION_PENALTY_MAX: 320,  // 线段相交的最大惩罚
    SEGMENT_INTERSECTION_LENGTH_THRESHOLD: 14, // 触发惩罚的最小重叠长度（像素）
    PREV_LABEL_SAME_DIR_PENALTY_MAIN: 10,   // 与前站标签同方向的惩罚（上/下）
    PREV_LABEL_SAME_DIR_PENALTY_DIAGONAL: 5, // 与前站标签同方向的惩罚（对角）
    LABEL_COLLISION_BASE_PENALTY: 400,      // 标签碰撞的基础惩罚
    LABEL_COLLISION_MIN_RATIO: 0.1,         // 标签碰撞最小惩罚比例
    LABEL_COLLISION_MIN_OVERLAP_LENGTH: 5,  // 任意维度重叠小于此值不认为碰撞（像素）
    
    // 奖励值
    PREFERRED_DIRECTION_BASE_BONUS: 40,     // 优选方向的基础奖励
    CARDINAL_DIRECTION_BONUS: 2,            // 主方向（上/下/左/右）的奖励
    AWAY_FROM_NEXT_BONUS: [5, 2],           // 远离下一站奖励
  }
  
  // === 工具函数 ===
  
  // 估计文本宽度
  const estimateTextWidth = (text) => text.length * CONFIG.TEXT_CHAR_WIDTH
  
  // 根据位置偏移和锚点获取标签边界框
  const getLabelBox = (coord, offset, anchor, text) => {
    const textWidth = estimateTextWidth(text)
    const x = coord.x + offset.x
    const y = coord.y + offset.y
    
    let left, right
    if (anchor === 'middle') {
      left = x - textWidth / 2
      right = x + textWidth / 2
    } else if (anchor === 'end') {
      left = x - textWidth
      right = x
    } else {
      left = x
      right = x + textWidth
    }
    
    return { left, right, top: y - CONFIG.TEXT_HEIGHT, bottom: y }
  }
  
  // 归一化向量
  const normalize = (v) => {
    const len = Math.sqrt(v.x * v.x + v.y * v.y)
    if (len === 0) return { x: 0, y: 0 }
    return { x: v.x / len, y: v.y / len }
  }
  
  // 获取与向量方向最匹配的方向名称
  const getDirectionFromVector = (v) => {
    const angle = Math.atan2(v.y, v.x) * 180 / Math.PI
    // angle: -180 到 180，其中 0 是右，90 是下，-90 是上
    if (angle >= -22.5 && angle < 22.5) return 'right'
    if (angle >= 22.5 && angle < 67.5) return 'bottom-right'
    if (angle >= 67.5 && angle < 112.5) return 'bottom'
    if (angle >= 112.5 && angle < 157.5) return 'bottom-left'
    if (angle >= 157.5 || angle < -157.5) return 'left'
    if (angle >= -157.5 && angle < -112.5) return 'top-left'
    if (angle >= -112.5 && angle < -67.5) return 'top'
    if (angle >= -67.5 && angle < -22.5) return 'top-right'
    return 'top'
  }
  
  // 获取与线段向量垂直的方向
  const getPerpendicularDirections = (lineVec) => {
    const perp1 = normalize({ x: -lineVec.y, y: lineVec.x })
    const perp2 = normalize({ x: lineVec.y, y: -lineVec.x })
    return [getDirectionFromVector(perp1), getDirectionFromVector(perp2)]
  }
  
  // 检查线段是否与矩形（盒子）相交
  // 使用 Liang-Barsky 算法进行线段-盒子相交检测
  // padding: 盒子周围的额外边距，用于更敏感的检测
  // 返回值: 重叠长度（像素），表示线段在盒子内的实际长度
  const getSegmentBoxOverlapLength = (A, B, box, padding = CONFIG.SEGMENT_BOX_OVERLAP_PADDING) => {
    const dx = B.x - A.x
    const dy = B.y - A.y
    const segmentLength = Math.sqrt(dx * dx + dy * dy)
    
    if (segmentLength === 0) return 0
    
    // 通过 padding 扩展盒子以进行更敏感的检测
    const expandedBox = {
      left: box.left - padding,
      right: box.right + padding,
      top: box.top - padding,
      bottom: box.bottom + padding
    }
    
    // 使用扩展盒子的 Liang-Barsky 算法
    const p = [-dx, dx, -dy, dy]
    const q = [A.x - expandedBox.left, expandedBox.right - A.x, A.y - expandedBox.top, expandedBox.bottom - A.y]
    
    let t0 = 0
    let t1 = 1
    
    for (let i = 0; i < 4; i++) {
      if (p[i] === 0) {
        // 线段与此边平行
        if (q[i] < 0) return 0 // 线段在外部
      } else {
        const t = q[i] / p[i]
        if (p[i] < 0) {
          t0 = Math.max(t0, t) // 入口点
        } else {
          t1 = Math.min(t1, t) // 出口点
        }
      }
    }
    
    if (t0 > t1) return 0 // 无相交
    
    // 计算重叠长度（线段在盒子内的实际像素长度）
    return (t1 - t0) * segmentLength
  }
  
  // 根据方向名称获取方向向量
  const getVectorFromDirection = (dir) => {
    const vectors = {
      'top': { x: 0, y: -1 },
      'bottom': { x: 0, y: 1 },
      'left': { x: -1, y: 0 },
      'right': { x: 1, y: 0 },
      'top-left': { x: -Math.SQRT1_2, y: -Math.SQRT1_2 },
      'top-right': { x: Math.SQRT1_2, y: -Math.SQRT1_2 },
      'bottom-left': { x: -Math.SQRT1_2, y: Math.SQRT1_2 },
      'bottom-right': { x: Math.SQRT1_2, y: Math.SQRT1_2 }
    }
    return vectors[dir] || { x: 0, y: -1 }
  }
  
  // 计算优选方向奖励的角度比例：向量同向时为 1，角度 >= 阈值时为 0
  // 使用基于角度的线性插值：0° = 1，阈值° = 0
  // 返回值范围 [0, 1]，用于奖励计算（已截断）
  const getAngleRatio = (v1, v2) => {
    const dot = v1.x * v2.x + v1.y * v2.y
    // 将点积截断到 [-1, 1] 以处理浮点误差
    const clampedDot = Math.max(-1, Math.min(1, dot))
    // 计算弧度角，然后转换为度数
    const angleRad = Math.acos(clampedDot)
    const angleDeg = angleRad * 180 / Math.PI
    // 线性插值：0° = 1，阈值° = 0
    return Math.max(0, 1 - angleDeg / CONFIG.PREFERRED_BONUS_ANGLE_THRESHOLD)
  }
  
  // 计算两个盒子之间的实际重叠比例
  // 返回重叠面积占较小盒子面积的比例 (0-1)
  const getOverlapRatio = (box1, box2, padding = 0) => {
    // 计算实际重叠区域
    const overlapLeft = Math.max(box1.left, box2.left)
    const overlapRight = Math.min(box1.right, box2.right)
    const overlapTop = Math.max(box1.top, box2.top)
    const overlapBottom = Math.min(box1.bottom, box2.bottom)
    
    const overlapWidth = overlapRight - overlapLeft + padding * 2
    const overlapHeight = overlapBottom - overlapTop + padding * 2
    
    // 如果没有重叠，返回 0
    if (overlapWidth <= 0 || overlapHeight <= 0) return 0
    
    // 如果任意维度重叠小于阈值，不认为是碰撞
    if (overlapWidth < CONFIG.LABEL_COLLISION_MIN_OVERLAP_LENGTH || 
        overlapHeight < CONFIG.LABEL_COLLISION_MIN_OVERLAP_LENGTH) return 0
    
    const overlapRatio = Math.min(1, (overlapWidth * overlapHeight) / (CONFIG.OVERLAP_RATIO_DIVISOR * CONFIG.OVERLAP_RATIO_DIVISOR))
    return overlapRatio
  }
  
  // === 步骤1：收集所有线段及其索引 ===
  const allLineSegments = []
  for (let i = 0; i < path.length - 1; i++) {
    const fromCoord = coordinates.value[path[i]]
    const toCoord = coordinates.value[path[i + 1]]
    if (fromCoord && toCoord) {
      allLineSegments.push({
        x1: fromCoord.x, y1: fromCoord.y,
        x2: toCoord.x, y2: toCoord.y,
        fromIndex: i, toIndex: i + 1
      })
    }
  }
  
  // === 检查 DEBUG_STATION 是否在路径中 ===
  const debugStationInPath = path.includes(DEBUG_STATION)
  
  // === 核心函数：计算给定路径顺序的标签位置 ===
  // orderedPath: 按处理顺序排列的站点数组
  // isReverse: 是否是反向处理（用于调试输出）
  // 返回: { result: 标签位置映射, lowestScore: 最低分, lowestStation: 最低分站点 }
  const computeLabelPositionsForPath = (orderedPath, isReverse = false) => {
    const result = {}
    const placedLabels = [] // 记录已放置的标签边界框
    let lowestScore = Infinity
    let lowestStationInfo = null
    
    // 记录每个站点的调试信息（用于找最低分站点）
    const stationDebugInfo = []
    
    for (let i = 0; i < orderedPath.length; i++) {
      const station = orderedPath[i]
      // 在原始路径中的索引（用于获取正确的相邻站点）
      const originalIndex = path.indexOf(station)
      const coord = coordinates.value[station]
      const isEndpointStation = isEndpoint(station)
      const isDebugStation = station === DEBUG_STATION
      
      if (!coord) {
        result[station] = { x: 0, y: -16, anchor: 'middle', name: 'top' }
        continue
      }
      
      // 定义候选位置
      const topY = isEndpointStation ? CONFIG.ENDPOINT_LABEL_TOP_Y : CONFIG.LABEL_TOP_Y
      const bottomY = isEndpointStation ? CONFIG.ENDPOINT_LABEL_BOTTOM_Y : CONFIG.LABEL_BOTTOM_Y
      const sideX = isEndpointStation ? CONFIG.ENDPOINT_LABEL_SIDE_X : CONFIG.LABEL_SIDE_X
      const cornerX = isEndpointStation ? CONFIG.ENDPOINT_LABEL_CORNER_X : CONFIG.LABEL_CORNER_X
      const cornerTopY = isEndpointStation ? CONFIG.ENDPOINT_LABEL_CORNER_TOP_Y : CONFIG.LABEL_CORNER_TOP_Y
      const cornerBottomY = isEndpointStation ? CONFIG.ENDPOINT_LABEL_CORNER_BOTTOM_Y : CONFIG.LABEL_CORNER_BOTTOM_Y
      
      const positions = {
        'top': { x: 0, y: topY, anchor: 'middle', name: 'top' },
        'bottom': { x: 0, y: bottomY, anchor: 'middle', name: 'bottom' },
        'left': { x: -sideX, y: CONFIG.LABEL_SIDE_Y, anchor: 'end', name: 'left' },
        'right': { x: sideX, y: CONFIG.LABEL_SIDE_Y, anchor: 'start', name: 'right' },
        'top-left': { x: -cornerX, y: cornerTopY, anchor: 'end', name: 'top-left' },
        'top-right': { x: cornerX, y: cornerTopY, anchor: 'start', name: 'top-right' },
        'bottom-left': { x: -cornerX, y: cornerBottomY, anchor: 'end', name: 'bottom-left' },
        'bottom-right': { x: cornerX, y: cornerBottomY, anchor: 'start', name: 'bottom-right' }
      }
      
      const allDirections = ['top', 'bottom', 'left', 'right', 'top-left', 'top-right', 'bottom-left', 'bottom-right']
      
      // 获取相邻站点坐标（基于原始路径顺序）
      const prevCoord = originalIndex > 0 ? coordinates.value[path[originalIndex - 1]] : null
      const nextCoord = originalIndex < path.length - 1 ? coordinates.value[path[originalIndex + 1]] : null
      
      // 获取处理顺序中的前一个站点（用于前站标签惩罚）
      const prevProcessedStation = i > 0 ? orderedPath[i - 1] : null
      
      // === 检查标签框与所有线段的相交 ===
      
      // 单独跟踪线段相交惩罚，用于调试
      const segmentPenalty = {}
      const segmentMaxRatio = {} // Track max overlap ratio for debugging
      for (const dir of allDirections) {
        segmentPenalty[dir] = 0
        segmentMaxRatio[dir] = 0
      }
      
      for (const dir of allDirections) {
        const pos = positions[dir]
        const labelBox = getLabelBox(coord, pos, pos.anchor, station)
        
        let maxOverlapLength = 0
        
        // 检查所有线段（包括相邻线段）
        for (const seg of allLineSegments) {
          const A = { x: seg.x1, y: seg.y1 }
          const B = { x: seg.x2, y: seg.y2 }
          
          const overlapLength = getSegmentBoxOverlapLength(A, B, labelBox, CONFIG.SEGMENT_COLLISION_PADDING)
          if (overlapLength > maxOverlapLength) {
            maxOverlapLength = overlapLength
          }
        }
        
        // 根据最大重叠长度计算惩罚（200-400）
        // 仅当重叠长度 >= 阈值时才应用惩罚
        if (maxOverlapLength >= CONFIG.SEGMENT_INTERSECTION_LENGTH_THRESHOLD) {
          // 使用重叠长度计算惩罚，假设最大重叠长度为标签宽度（约42像素）
          const maxExpectedLength = estimateTextWidth(station)
          const lengthRatio = Math.min(1, maxOverlapLength / maxExpectedLength)
          const penalty = CONFIG.SEGMENT_INTERSECTION_PENALTY_MIN + 
            (CONFIG.SEGMENT_INTERSECTION_PENALTY_MAX - CONFIG.SEGMENT_INTERSECTION_PENALTY_MIN) * lengthRatio
          segmentPenalty[dir] = penalty
          segmentMaxRatio[dir] = maxOverlapLength // Now stores length instead of ratio
        }
      }
      
      // === 惩罚前一站标签使用的方向 ===
      // 仅惩罚完全相同的方向，且仅针对上/下或对角方向
      // 左/右标签不产生惩罚
      const prevLabelPos = prevProcessedStation ? result[prevProcessedStation] : null
      // 前站标签惩罚将在评分循环中直接应用
      
      // === 检查与已放置标签的碰撞 ===
      const labelCollisionPenalty = {}
      for (const dir of allDirections) {
        labelCollisionPenalty[dir] = 0
        const pos = positions[dir]
        const labelBox = getLabelBox(coord, pos, pos.anchor, station)
        for (const placed of placedLabels) {
          const overlapRatio = getOverlapRatio(labelBox, placed.box, CONFIG.LABEL_COLLISION_PADDING)
          if (overlapRatio > 0) {
            labelCollisionPenalty[dir] += CONFIG.LABEL_COLLISION_BASE_PENALTY * Math.max(overlapRatio, CONFIG.LABEL_COLLISION_MIN_RATIO)
          }
        }
      }
      
      // === 计算远离下一站奖励 ===
      // 计算每个方向的标签中心点到下一站的距离，距离越远奖励越高
      const awayFromNextBonus = {}
      for (const dir of allDirections) {
        awayFromNextBonus[dir] = 0
      }
      
      if (nextCoord) {
        // 计算每个方向标签中心点到下一站的距离
        const dirDistances = []
        for (const dir of allDirections) {
          const pos = positions[dir]
          const labelBox = getLabelBox(coord, pos, pos.anchor, station)
          // 标签几何中心点
          const labelCenterX = (labelBox.left + labelBox.right) / 2
          const labelCenterY = (labelBox.top + labelBox.bottom) / 2
          // 到下一站的距离（勾股定理）
          const dx = labelCenterX - nextCoord.x
          const dy = labelCenterY - nextCoord.y
          const distance = Math.sqrt(dx * dx + dy * dy)
          dirDistances.push({ dir, distance })
        }
        
        // 按距离降序排序（距离最远的排在前面）
        dirDistances.sort((a, b) => b.distance - a.distance)
        
        // 给前5名分配奖励
        const bonusValues = CONFIG.AWAY_FROM_NEXT_BONUS
        for (let rank = 0; rank < Math.min(bonusValues.length, dirDistances.length); rank++) {
          awayFromNextBonus[dirDistances[rank].dir] = bonusValues[rank]
        }
      }
      
      // === 根据几何形状确定优选方向 ===
      // 存储实际的理想外向向量，用于基于角度的奖励计算
      let idealOutwardVec = null
      let idealInwardVec = null  // 角平分线方向（在前后站之间）
      let inwardBonusRatio = 0   // 内向方向奖励比例（基于前后站之间的夹角）
      let preferredDirections = []
      
      if (prevCoord && nextCoord) {
        const toW = normalize({ x: prevCoord.x - coord.x, y: prevCoord.y - coord.y })
        const toY = normalize({ x: nextCoord.x - coord.x, y: nextCoord.y - coord.y })
        // 拐角处：优先选择角平分线的反方向
        const bisector = normalize({ x: toW.x + toY.x, y: toW.y + toY.y })
        idealOutwardVec = { x: -bisector.x, y: -bisector.y }
        idealInwardVec = bisector
        
        // 计算前后站方向之间的夹角（以度为单位）
        // 这是该站点的
        const dot = toW.x * toY.x + toW.y * toY.y
        const clampedDot = Math.max(-1, Math.min(1, dot))
        const angleBetweenRad = Math.acos(clampedDot)
        const angleBetweenDeg = angleBetweenRad * 180 / Math.PI
        
        // 根据 CONFIG 中的角度阈值计算内向奖励比例
        // angleBetweenDeg 是指向相邻站的两个向量之间的夹角
        // 角度越大表示越接近直线，角度越小表示越急的拐弯
        if (angleBetweenDeg >= CONFIG.INWARD_BONUS_ANGLE_MAX) {
          inwardBonusRatio = 1  // 在最大角度及以上获得满奖励
        } else if (angleBetweenDeg > CONFIG.INWARD_BONUS_ANGLE_MIN) {
          const range = CONFIG.INWARD_BONUS_ANGLE_MAX - CONFIG.INWARD_BONUS_ANGLE_MIN
          inwardBonusRatio = (angleBetweenDeg - CONFIG.INWARD_BONUS_ANGLE_MIN) / range
        } else {
          inwardBonusRatio = 0
        }
        
        const preferredDir = getDirectionFromVector(idealOutwardVec)
        preferredDirections = [preferredDir]
        const adjacentDirs = {
          'top': ['top-left', 'top-right'],
          'bottom': ['bottom-left', 'bottom-right'],
          'left': ['top-left', 'bottom-left'],
          'right': ['top-right', 'bottom-right'],
          'top-left': ['top', 'left'],
          'top-right': ['top', 'right'],
          'bottom-left': ['bottom', 'left'],
          'bottom-right': ['bottom', 'right']
        }
        preferredDirections = preferredDirections.concat(adjacentDirs[preferredDir] || [])
      } else if (prevCoord) {
        const toPrev = normalize({ x: prevCoord.x - coord.x, y: prevCoord.y - coord.y })
        idealOutwardVec = { x: -toPrev.x, y: -toPrev.y }
        preferredDirections = getPerpendicularDirections(toPrev)
        const awayDir = getDirectionFromVector(idealOutwardVec)
        preferredDirections.unshift(awayDir)
      } else if (nextCoord) {
        const toNext = normalize({ x: nextCoord.x - coord.x, y: nextCoord.y - coord.y })
        idealOutwardVec = { x: -toNext.x, y: -toNext.y }
        preferredDirections = getPerpendicularDirections(toNext)
        const awayDir = getDirectionFromVector(idealOutwardVec)
        preferredDirections.unshift(awayDir)
      } else {
        preferredDirections = ['top', 'bottom', 'left', 'right']
      }
      
      // === 评分并选择最佳位置 ===
      let bestPos = positions['top']
      let bestScore = -Infinity
      
      if (isDebugStation) {
        const direction = isReverse ? '反向' : '正向'
        console.log(`[${direction}] 站点：${station} | 上一站：${path[originalIndex - 1] || '无'} | 下一站：${path[originalIndex + 1] || '无'}`)
      }
      
      for (const dirName of allDirections) {
        let score = 0
        const scoreDetails = { segmentPenalty: 0, labelCollision: 0, preferredBonus: 0, cardinalBonus: 0 }
        
        // 应用线段碰撞惩罚
        score -= segmentPenalty[dirName]
        scoreDetails.segmentPenalty = -segmentPenalty[dirName]
        
        // 应用前站标签方向惩罚
        if (prevLabelPos && prevLabelPos.name === dirName) {
          if (dirName === 'top' || dirName === 'bottom') {
            score -= CONFIG.PREV_LABEL_SAME_DIR_PENALTY_MAIN
          } else if (dirName.includes('-')) {
            score -= CONFIG.PREV_LABEL_SAME_DIR_PENALTY_DIAGONAL
          }
        }
        
        // 应用标签碰撞惩罚
        score -= labelCollisionPenalty[dirName]
        scoreDetails.labelCollision = -labelCollisionPenalty[dirName]
        
        // 基于与理想外向方向的角度比例给予优选方向奖励
        // 使用 90° 范围：0° = 满奖励，90° = 无奖励
        // 使用实际的 idealOutwardVec 进行精确的角度计算
        // 奖励总和始终为 2 倍基础奖励：
        //   - 当夹角 > 120°：外向获得 (1 + (1 - inwardBonusRatio))，内向获得 inwardBonusRatio
        //   - 当夹角 <= 120°：外向获得 2 倍，内向获得 0
        if (idealOutwardVec) {
          const dirVec = getVectorFromDirection(dirName)
          const angleRatioOutward = getAngleRatio(dirVec, idealOutwardVec)
          let bonus = 0
          
          // 计算外向乘数：当存在 inwardBonusRatio 时，外向获得内向
          const outwardMultiplier = 1 + (1 - inwardBonusRatio)
          
          if (angleRatioOutward > 0) {
            bonus = CONFIG.PREFERRED_DIRECTION_BASE_BONUS * angleRatioOutward * outwardMultiplier
          }
          
          // 内向方向（角平分线）也获得奖励，按 inwardBonusRatio 缩放
          // 当轨道相对平直时（夹角 > 120°）生效
          if (idealInwardVec && inwardBonusRatio > 0) {
            const angleRatioInward = getAngleRatio(dirVec, idealInwardVec)
            if (angleRatioInward > 0) {
              const inwardBonus = CONFIG.PREFERRED_DIRECTION_BASE_BONUS * angleRatioInward * inwardBonusRatio
              bonus = Math.max(bonus, inwardBonus)  // 取较高的奖励
            }
          }
          
          if (bonus > 0) {
            score += bonus
            scoreDetails.preferredBonus = bonus
          }
        }
        
        // 主方向相比对角方向略有优势
        if (['top', 'bottom', 'left', 'right'].includes(dirName)) {
          score += CONFIG.CARDINAL_DIRECTION_BONUS
          scoreDetails.cardinalBonus = CONFIG.CARDINAL_DIRECTION_BONUS
        }
        
        // 应用远离下一站奖励
        if (awayFromNextBonus[dirName] > 0) {
          score += awayFromNextBonus[dirName]
          scoreDetails.awayFromNextBonus = awayFromNextBonus[dirName]
        }
        
        // 收集调试信息
        if (!debugStationInPath || isDebugStation) {
          const prevLabelPenalty = (prevLabelPos && prevLabelPos.name === dirName) ? 
            ((dirName === 'top' || dirName === 'bottom') ? CONFIG.PREV_LABEL_SAME_DIR_PENALTY_MAIN : 
             (dirName.includes('-') ? CONFIG.PREV_LABEL_SAME_DIR_PENALTY_DIAGONAL : 0)) : 0
          
          const debugLine = `${dirName} = ${score.toFixed(0)} = ` +
            `${(-segmentPenalty[dirName]).toFixed(0)}(线段碰撞) ` +
            `${scoreDetails.labelCollision.toFixed(0)}(标签碰撞) ` +
            `+${scoreDetails.preferredBonus.toFixed(0)}(优选方向) ` +
            `${(-prevLabelPenalty).toFixed(0)}(前站标签) ` +
            `+${scoreDetails.awayFromNextBonus || 0}(远离下站) ` +
            `+${scoreDetails.cardinalBonus}(主方向)`
          
          if (isDebugStation) {
            console.log(debugLine)
          }
          
          // 记录当前方向的调试信息
          if (!debugStationInPath) {
            if (!stationDebugInfo[i]) {
              stationDebugInfo[i] = {
                station,
                prevStation: path[originalIndex - 1] || '无',
                nextStation: path[originalIndex + 1] || '无',
                directions: [],
                bestScore: -Infinity,
                bestDir: ''
              }
            }
            stationDebugInfo[i].directions.push(debugLine)
          }
        }
        
        if (score > bestScore) {
          bestScore = score
          bestPos = positions[dirName]
        }
      }
      
      // 记录最终选择
      if (!debugStationInPath) {
        if (stationDebugInfo[i]) {
          stationDebugInfo[i].bestScore = bestScore
          stationDebugInfo[i].bestDir = bestPos.name
        }
      }
      
      // 更新最低分
      if (bestScore < lowestScore) {
        lowestScore = bestScore
        lowestStationInfo = stationDebugInfo[i]
      }
      
      if (isDebugStation) {
        console.log(`>>> 最终选择: ${bestPos.name} (${bestScore.toFixed(0)})`)
      }
      
      result[station] = bestPos
      placedLabels.push({
        station,
        box: getLabelBox(coord, bestPos, bestPos.anchor, station)
      })
    }
    
    return {
      result,
      lowestScore,
      lowestStationInfo,
      stationDebugInfo
    }
  }
  
  // === 步骤2：两趟择优 - 正向和反向各计算一次 ===
  const forwardResult = computeLabelPositionsForPath(path, false)
  const reversedPath = [...path].reverse()
  const reverseResult = computeLabelPositionsForPath(reversedPath, true)
  
  // === 步骤3：比较最低分，选择更优的结果 ===
  const useForward = forwardResult.lowestScore >= reverseResult.lowestScore
  const finalResult = useForward ? forwardResult : reverseResult
  
  // === 输出调试信息 ===
  if (!debugStationInPath && finalResult.lowestStationInfo) {
    const direction = useForward ? '正向' : '反向'
    console.log(`[两趟择优] 选择${direction}结果 | 正向最低分: ${forwardResult.lowestScore.toFixed(0)} | 反向最低分: ${reverseResult.lowestScore.toFixed(0)}`)
    console.log(`[最低分站点] 站点：${finalResult.lowestStationInfo.station} | 上一站：${finalResult.lowestStationInfo.prevStation} | 下一站：${finalResult.lowestStationInfo.nextStation}`)
    for (const line of finalResult.lowestStationInfo.directions) {
      console.log(line)
    }
    console.log(`>>> 最终选择: ${finalResult.lowestStationInfo.bestDir} (${finalResult.lowestScore.toFixed(0)})`)
  }
  
  return finalResult.result
})

// 获取站点标签偏移的辅助函数
const getLabelOffset = (station) => {
  return labelPositions.value[station] || { x: 0, y: -16, anchor: 'middle' }
}

// Zoom controls
const zoomIn = () => {
  scale.value = Math.min(scale.value * 1.3, 10)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value / 1.3, 0.3)
}

const resetView = () => {
  scale.value = 1
  panOffset.value = { x: 0, y: 0 }
  // Auto-center on start/end stations if available
  if (props.startStation || props.endStation) {
    centerOnStations()
  }
}

const centerOnStations = () => {
  const targetStations = []
  if (props.startStation && coordinates.value[props.startStation]) {
    targetStations.push(coordinates.value[props.startStation])
  }
  if (props.endStation && coordinates.value[props.endStation]) {
    targetStations.push(coordinates.value[props.endStation])
  }
  
  if (targetStations.length === 0) return
  
  // Calculate center of target stations
  const centerX = targetStations.reduce((sum, s) => sum + s.x, 0) / targetStations.length
  const centerY = targetStations.reduce((sum, s) => sum + s.y, 0) / targetStations.length
  
  // Calculate map center
  const bounds = mapBounds.value
  const mapCenterX = (bounds.minX + bounds.maxX) / 2
  const mapCenterY = (bounds.minY + bounds.maxY) / 2
  
  // Set pan offset to center on target stations
  panOffset.value = {
    x: centerX - mapCenterX,
    y: centerY - mapCenterY
  }
  
  // Adjust zoom based on distance between stations
  if (targetStations.length === 2) {
    const dx = targetStations[1].x - targetStations[0].x
    const dy = targetStations[1].y - targetStations[0].y
    const distance = Math.sqrt(dx * dx + dy * dy)
    
    // Adjust scale based on distance (closer stations = more zoom)
    const mapWidth = bounds.maxX - bounds.minX
    scale.value = Math.min(Math.max(mapWidth / (distance * 3), 0.8), 2.5)
  } else {
    scale.value = 1.5
  }
}

// Pan controls
const startPan = (e) => {
  isPanning.value = true
  lastPanPosition.value = { x: e.clientX, y: e.clientY }
}

const pan = (e) => {
  if (!isPanning.value) return
  
  const bounds = mapBounds.value
  const viewWidth = (bounds.maxX - bounds.minX) / scale.value
  const viewHeight = (bounds.maxY - bounds.minY) / scale.value
  
  // Convert pixel movement to SVG coordinate movement
  const wrapper = mapWrapper.value
  if (!wrapper) return
  
  const rect = wrapper.getBoundingClientRect()
  const scaleX = viewWidth / rect.width
  const scaleY = viewHeight / rect.height
  
  const dx = (e.clientX - lastPanPosition.value.x) * scaleX
  const dy = (e.clientY - lastPanPosition.value.y) * scaleY
  
  panOffset.value = {
    x: panOffset.value.x - dx,
    y: panOffset.value.y - dy
  }
  
  lastPanPosition.value = { x: e.clientX, y: e.clientY }
}

const endPan = () => {
  isPanning.value = false
}

const handleWheel = (e) => {
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  scale.value = Math.min(Math.max(scale.value * delta, 0.3), 10)
}

// Touch handlers for mobile
const handleTouchStart = (e) => {
  if (e.touches.length === 1) {
    isPanning.value = true
    lastPanPosition.value = { x: e.touches[0].clientX, y: e.touches[0].clientY }
  } else if (e.touches.length === 2) {
    // Pinch zoom start
    const dx = e.touches[0].clientX - e.touches[1].clientX
    const dy = e.touches[0].clientY - e.touches[1].clientY
    lastTouchDistance.value = Math.sqrt(dx * dx + dy * dy)
  }
}

const handleTouchMove = (e) => {
  if (e.touches.length === 1 && isPanning.value) {
    const bounds = mapBounds.value
    const viewWidth = (bounds.maxX - bounds.minX) / scale.value
    const viewHeight = (bounds.maxY - bounds.minY) / scale.value
    
    const wrapper = mapWrapper.value
    if (!wrapper) return
    
    const rect = wrapper.getBoundingClientRect()
    const scaleX = viewWidth / rect.width
    const scaleY = viewHeight / rect.height
    
    const dx = (e.touches[0].clientX - lastPanPosition.value.x) * scaleX
    const dy = (e.touches[0].clientY - lastPanPosition.value.y) * scaleY
    
    panOffset.value = {
      x: panOffset.value.x - dx,
      y: panOffset.value.y - dy
    }
    
    lastPanPosition.value = { x: e.touches[0].clientX, y: e.touches[0].clientY }
  } else if (e.touches.length === 2) {
    // Pinch zoom
    const dx = e.touches[0].clientX - e.touches[1].clientX
    const dy = e.touches[0].clientY - e.touches[1].clientY
    const distance = Math.sqrt(dx * dx + dy * dy)
    
    if (lastTouchDistance.value > 0) {
      const delta = distance / lastTouchDistance.value
      scale.value = Math.min(Math.max(scale.value * delta, 0.3), 10)
    }
    
    lastTouchDistance.value = distance
  }
}

const handleTouchEnd = () => {
  isPanning.value = false
  lastTouchDistance.value = 0
}

// Game store for city
const gameStore = useGameStore()

// Load map data
const loadMapData = async () => {
  try {
    loading.value = true
    const response = await api.getMapCoordinates(gameStore.city)
    coordinates.value = response.data.stations || {}
    linesData.value = response.data.lines || {}
  } catch (error) {
    console.error('Failed to load map coordinates:', error)
  } finally {
    loading.value = false
  }
}

// Watch for station changes to auto-center
watch(() => [props.startStation, props.endStation], () => {
  if (Object.keys(coordinates.value).length > 0) {
    nextTick(() => {
      centerOnStations()
    })
  }
}, { immediate: false })

// Watch for city changes to reload map data
watch(() => gameStore.city, async () => {
  await loadMapData()
  resetView()
})

// Initial load
onMounted(async () => {
  await loadMapData()
  if (props.startStation || props.endStation) {
    centerOnStations()
  }
})
</script>

<style scoped>
.metro-map-container {
  width: 100%;
}

.map-wrapper {
  width: 100%;
  height: 300px;
  min-height: 150px;
  max-height: 750px;
  touch-action: none;
  resize: vertical;
  overflow: auto;
  user-select: none;
  -webkit-user-select: none;
}

.metro-map {
  width: 100%;
  height: 100%;
}

.station-dot {
  transition: r 0.2s ease;
}

/* Normal station (r=6) hover: slightly larger */
.station-dot:hover {
  r: 8;
}

/* Endpoint station (r=10) hover: slightly larger */
.station-dot.station-endpoint:hover {
  r: 12;
}

.station-endpoint {
  filter: url(#glow);
}

.station-label {
  pointer-events: none;
  user-select: none;
}

.pulse-circle {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    r: 8;
    opacity: 0.3;
  }
  50% {
    r: 14;
    opacity: 0.1;
  }
  100% {
    r: 8;
    opacity: 0.3;
  }
}

.path-line-animated {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: drawLine 0.5s ease forwards;
}

@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}

/* Transfer station legend style */
.transfer-station-legend {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2.4px solid #666;
  background-color: white;
  position: relative;
}

.transfer-station-legend::after {
  content: '';
  position: absolute;
  width: 3.2px;
  height: 3.2px;
  border-radius: 50%;
  background-color: #666;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>

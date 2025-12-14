<template>
  <div class="metro-map-container">
    <div class="map-header flex justify-between items-center mb-2">
      <h4 class="font-semibold text-gray-700">
        🗺️ 选中线路预览
      </h4>
      <div class="flex gap-2">
        <button 
          @click="zoomIn" 
          class="px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
          title="放大"
        >+</button>
        <button 
          @click="zoomOut" 
          class="px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
          title="缩小"
        >-</button>
        <button 
          @click="resetView" 
          class="px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
          title="重置视图"
        >⟲</button>
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
        <!-- Background grid (subtle) -->
        <g class="grid" opacity="0.1">
          <line v-for="x in gridLinesX" :key="'gx'+x" :x1="x" :y1="mapBounds.minY - 50" :x2="x" :y2="mapBounds.maxY + 50" stroke="#888" stroke-width="0.5"/>
          <line v-for="y in gridLinesY" :key="'gy'+y" :x1="mapBounds.minX - 50" :y1="y" :x2="mapBounds.maxX + 50" :y2="y" stroke="#888" stroke-width="0.5"/>
        </g>

        <!-- Draw lines with their colors -->
        <g class="line-paths">
          <g v-for="lineData in selectedLinesData" :key="lineData.name">
            <!-- Line segments -->
            <path
              v-for="(segment, idx) in lineData.segments"
              :key="lineData.name + '-seg-' + idx"
              :d="segment.path"
              :stroke="lineData.color"
              stroke-width="6"
              stroke-linecap="round"
              fill="none"
            />
          </g>
        </g>

        <!-- Draw stations (no labels) -->
        <g class="stations">
          <!-- Transfer stations (multiple lines) - concentric circles -->
          <g v-for="station in transferStations" :key="'transfer-' + station.name">
            <!-- Outer ring -->
            <circle
              :cx="station.x"
              :cy="station.y"
              r="4"
              fill="white"
              stroke="#666"
              stroke-width="2"
              class="station-transfer"
              @mouseenter="showTooltip($event, station)"
              @mouseleave="hideTooltip"
            />
            <!-- Inner dot -->
            <circle
              :cx="station.x"
              :cy="station.y"
              r="1.2"
              fill="#666"
              class="station-transfer-inner"
              pointer-events="none"
            />
          </g>
          <!-- Single-line stations -->
          <g v-for="station in singleLineStations" :key="'single-' + station.name">
            <circle
              :cx="station.x"
              :cy="station.y"
              r="4"
              fill="white"
              :stroke="station.lineColor"
              stroke-width="2"
              class="station-dot"
              @mouseenter="showTooltip($event, station)"
              @mouseleave="hideTooltip"
            />
          </g>
        </g>
      </svg>

      <!-- Custom Tooltip (inside map-wrapper for correct positioning) -->
      <Transition name="tooltip-fade">
        <div
          v-if="tooltipVisible"
          class="station-tooltip"
          :style="tooltipStyle"
        >
        <div class="tooltip-content">
          <span class="station-name">{{ tooltipStation?.name }}</span>
          <div class="line-tags">
            <span
              v-for="line in tooltipStation?.lines"
              :key="line.name"
              class="line-tag"
              :style="{ backgroundColor: line.color }"
            >{{ line.name }}</span>
          </div>
        </div>
        </div>
      </Transition>
    </div>

    <!-- Legend showing selected lines -->
    <div v-if="selectedLines.length > 0" class="map-legend mt-2 flex flex-wrap gap-3 text-xs text-gray-600">
      <div 
        v-for="lineData in selectedLinesData" 
        :key="lineData.name"
        class="flex items-center gap-1"
      >
        <span 
          class="w-4 h-1 rounded"
          :style="{ backgroundColor: lineData.color }"
        ></span>
        <span>{{ lineData.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useGameStore } from '@/stores/game'
import api from '@/services/api'

const props = defineProps({
  selectedLines: {
    type: Array,
    default: () => []
  }
})

const gameStore = useGameStore()

// Map data
const coordinates = ref({})
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

// Tooltip state
const tooltipVisible = ref(false)
const tooltipStation = ref(null)
const tooltipPosition = ref({ x: 0, y: 0 })

const tooltipStyle = computed(() => ({
  left: `${tooltipPosition.value.x}px`,
  top: `${tooltipPosition.value.y}px`
}))

const showTooltip = (event, station) => {
  tooltipStation.value = station
  const rect = mapWrapper.value?.getBoundingClientRect()
  if (rect) {
    tooltipPosition.value = {
      x: event.clientX - rect.left + 10,
      y: event.clientY - rect.top - 10
    }
  }
  tooltipVisible.value = true
}

const hideTooltip = () => {
  tooltipVisible.value = false
  tooltipStation.value = null
}

// Get station coordinate
const getStationCoord = (stationName) => {
  return coordinates.value[stationName]
}

// Calculate selected lines data with segments
const selectedLinesData = computed(() => {
  const result = []
  
  for (const lineName of props.selectedLines) {
    const lineInfo = gameStore.linesData[lineName]
    if (!lineInfo || !lineInfo.stations) continue
    
    const color = lineInfo.color || '#6B7280'
    const stations = lineInfo.stations
    const segments = []
    
    // Create smooth path segments for each pair of adjacent stations
    for (let i = 0; i < stations.length - 1; i++) {
      const fromCoord = getStationCoord(stations[i])
      const toCoord = getStationCoord(stations[i + 1])
      
      if (!fromCoord || !toCoord) continue
      
      // Get coordinates for smooth curve calculation
      const points = []
      const prevCoord = i > 0 ? getStationCoord(stations[i - 1]) : null
      const nextNextCoord = i < stations.length - 2 ? getStationCoord(stations[i + 2]) : null
      
      const p0 = prevCoord || fromCoord
      const p1 = fromCoord
      const p2 = toCoord
      const p3 = nextNextCoord || toCoord
      
      // Catmull-Rom to Cubic Bezier conversion
      const tension = 0.5
      const cp1x = p1.x + (p2.x - p0.x) * tension / 3
      const cp1y = p1.y + (p2.y - p0.y) * tension / 3
      const cp2x = p2.x - (p3.x - p1.x) * tension / 3
      const cp2y = p2.y - (p3.y - p1.y) * tension / 3
      
      const pathData = `M ${p1.x} ${p1.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`
      segments.push({ path: pathData })
    }
    
    result.push({
      name: lineName,
      color,
      segments
    })
  }
  
  return result
})

// Get station to lines mapping for selected lines only
const stationToLinesMap = computed(() => {
  const map = {}
  
  for (const lineName of props.selectedLines) {
    const lineInfo = gameStore.linesData[lineName]
    if (!lineInfo || !lineInfo.stations) continue
    
    for (const stationName of lineInfo.stations) {
      if (!map[stationName]) {
        map[stationName] = []
      }
      map[stationName].push({
        name: lineName,
        color: lineInfo.color || '#6B7280'
      })
    }
  }
  
  return map
})

// Get all unique stations from selected lines with their coordinates
const allStationsWithCoords = computed(() => {
  const stationSet = new Set()
  const result = []
  
  for (const lineName of props.selectedLines) {
    const lineInfo = gameStore.linesData[lineName]
    if (!lineInfo || !lineInfo.stations) continue
    
    for (const stationName of lineInfo.stations) {
      if (!stationSet.has(stationName)) {
        const coord = getStationCoord(stationName)
        if (coord) {
          stationSet.add(stationName)
          const lines = stationToLinesMap.value[stationName] || []
          result.push({
            name: stationName,
            x: coord.x,
            y: coord.y,
            lines: lines,
            isTransfer: lines.length > 1,
            lineColor: lines.length === 1 ? lines[0].color : '#333'
          })
        }
      }
    }
  }
  
  return result
})

// Separate transfer stations and single-line stations
const transferStations = computed(() => {
  return allStationsWithCoords.value.filter(s => s.isTransfer)
})

const singleLineStations = computed(() => {
  return allStationsWithCoords.value.filter(s => !s.isTransfer)
})

// Map bounds - only include selected stations
const mapBounds = computed(() => {
  const stations = allStationsWithCoords.value
  if (stations.length === 0) {
    // Default bounds if no stations
    const allStations = Object.values(coordinates.value)
    if (allStations.length === 0) {
      return { minX: 0, maxX: 1000, minY: 0, maxY: 600 }
    }
    const xs = allStations.map(s => s.x)
    const ys = allStations.map(s => s.y)
    return {
      minX: Math.min(...xs) - 100,
      maxX: Math.max(...xs) + 100,
      minY: Math.min(...ys) - 100,
      maxY: Math.max(...ys) + 100
    }
  }
  
  const xs = stations.map(s => s.x)
  const ys = stations.map(s => s.y)
  return {
    minX: Math.min(...xs) - 50,
    maxX: Math.max(...xs) + 50,
    minY: Math.min(...ys) - 50,
    maxY: Math.max(...ys) + 50
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

// Load map data
const loadMapData = async () => {
  try {
    loading.value = true
    const response = await api.getMapCoordinates()
    coordinates.value = response.data.stations || {}
  } catch (error) {
    console.error('Failed to load map coordinates:', error)
  } finally {
    loading.value = false
  }
}

// Watch for selected lines changes to reset view
watch(() => props.selectedLines, () => {
  if (props.selectedLines.length > 0) {
    nextTick(() => {
      resetView()
    })
  }
}, { deep: true })

// Initial load
onMounted(async () => {
  await loadMapData()
})
</script>

<style scoped>
.metro-map-container {
  width: 100%;
}

.map-wrapper {
  position: relative;
  width: 100%;
  height: 300px;
  min-height: 150px;
  max-height: 750px;
  touch-action: none;
  resize: vertical;
  overflow: auto;
}

.metro-map {
  width: 100%;
  height: 100%;
}

.station-dot {
  transition: r 0.2s ease;
  cursor: pointer;
}

.station-dot:hover {
  r: 6;
}

.station-transfer {
  cursor: pointer;
}

.station-transfer-inner {
  pointer-events: none;
}

/* Custom Tooltip */
.station-tooltip {
  position: absolute;
  z-index: 100;
  pointer-events: none;
  user-select: none;
  -webkit-user-select: none;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-width: 250px;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.station-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
  text-align: center;
}

.line-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 3px;
}

.line-tag {
  font-size: 11px;
  color: white;
  padding: 2px 6px;
  border-radius: 9999px;
  white-space: nowrap;
}

/* Tooltip fade transition */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>

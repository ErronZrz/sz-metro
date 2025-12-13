<template>
  <div class="metro-map-container">
    <div class="map-header flex justify-between items-center mb-2">
      <h4 class="font-semibold text-gray-700">
        {{ mode === 'question' ? '📍 起终点位置' : '🗺️ 路径可视化' }}
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
              stroke="#333"
              stroke-width="2.5"
              class="station-dot"
              :class="{ 'station-endpoint': isEndpoint(station) }"
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
        <span class="w-3 h-3 rounded-full bg-blue-500"></span>
        <span>途经站点</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '@/services/api'

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
  // Array of station names for the path (in order)
  path: {
    type: Array,
    default: () => []
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
  return props.path.filter(station => coordinates.value[station])
})

// Path segments with colors
const pathSegments = computed(() => {
  const segments = []
  const path = pathStations.value
  
  for (let i = 0; i < path.length - 1; i++) {
    const from = path[i]
    const to = path[i + 1]
    
    // Try to find the line color for this segment
    let color = '#3B82F6' // Default blue
    
    // Check which line connects these two stations
    for (const [lineName, lineData] of Object.entries(linesData.value)) {
      const stations = lineData.stations || []
      const fromIdx = stations.indexOf(from)
      const toIdx = stations.indexOf(to)
      if (fromIdx !== -1 && toIdx !== -1 && Math.abs(fromIdx - toIdx) === 1) {
        color = lineData.color || color
        break
      }
    }
    
    segments.push({ from, to, color })
  }
  
  return segments
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

// Calculate label positions using improved algorithm:
// 1. Mark all line segments as occupied regions
// 2. For each station D, penalize directions based on nearby line segments:
//    - Directly penalize the direction of adjacent stations (C and E)
//    - Traverse backwards (BC, AB, ...) and forwards (EF, FG, ...) to penalize directions
//      of segments that pass close to D (distance < threshold)
//    - Stop traversal when a segment is far enough from D
// 3. Penalize directions used by previous station's label to avoid overlap
// 4. For straight lines (angle > 150°): prefer perpendicular direction
// 5. For corners (angle <= 150°): prefer angle bisector's reverse direction
const labelPositions = computed(() => {
  const path = pathStations.value
  const result = {}
  const placedLabels = [] // Track placed label bounding boxes
  
  // === Utility functions ===
  
  // Estimate text dimensions
  const estimateTextWidth = (text) => text.length * 14
  const textHeight = 16
  
  // Get label bounding box based on position offset and anchor
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
    
    return { left, right, top: y - textHeight, bottom: y }
  }
  
  // Check if two boxes overlap
  const boxesOverlap = (box1, box2, margin = 0) => {
    return !(box1.right + margin < box2.left || 
             box1.left - margin > box2.right || 
             box1.bottom + margin < box2.top || 
             box1.top - margin > box2.bottom)
  }
  
  // Normalize a vector
  const normalize = (v) => {
    const len = Math.sqrt(v.x * v.x + v.y * v.y)
    if (len === 0) return { x: 0, y: 0 }
    return { x: v.x / len, y: v.y / len }
  }
  
  // Calculate angle between two vectors (in radians)
  const angleBetween = (v1, v2) => {
    const dot = v1.x * v2.x + v1.y * v2.y
    return Math.acos(Math.max(-1, Math.min(1, dot)))
  }
  
  // Get direction name that best matches a vector direction
  const getDirectionFromVector = (v) => {
    const angle = Math.atan2(v.y, v.x) * 180 / Math.PI
    // angle: -180 to 180, where 0 is right, 90 is down, -90 is up
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
  
  // Get perpendicular directions to a line vector
  const getPerpendicularDirections = (lineVec) => {
    const perp1 = normalize({ x: -lineVec.y, y: lineVec.x })
    const perp2 = normalize({ x: lineVec.y, y: -lineVec.x })
    return [getDirectionFromVector(perp1), getDirectionFromVector(perp2)]
  }
  
  // Calculate distance from point P to line segment AB
  // Returns { distance, closestPoint }
  const pointToSegmentDistance = (P, A, B) => {
    const dx = B.x - A.x
    const dy = B.y - A.y
    const segLenSq = dx * dx + dy * dy
    
    if (segLenSq === 0) {
      // Segment is a point
      const dist = Math.sqrt((P.x - A.x) ** 2 + (P.y - A.y) ** 2)
      return { distance: dist, closestPoint: A, isOnSegment: true }
    }
    
    // Project P onto line AB, clamped to segment
    const t = Math.max(0, Math.min(1, ((P.x - A.x) * dx + (P.y - A.y) * dy) / segLenSq))
    const closestPoint = { x: A.x + t * dx, y: A.y + t * dy }
    const distance = Math.sqrt((P.x - closestPoint.x) ** 2 + (P.y - closestPoint.y) ** 2)
    const isOnSegment = t > 0 && t < 1 // true if perpendicular foot is on segment
    
    return { distance, closestPoint, isOnSegment }
  }
  
  // Get the direction from point P to point Q
  const getDirectionFromPoints = (P, Q) => {
    const v = { x: Q.x - P.x, y: Q.y - P.y }
    return getDirectionFromVector(normalize(v))
  }
  
  // Get related directions (e.g., 'top' relates to 'top-left' and 'top-right')
  const getRelatedDirections = (dir) => {
    const related = {
      'top': ['top', 'top-left', 'top-right'],
      'bottom': ['bottom', 'bottom-left', 'bottom-right'],
      'left': ['left', 'top-left', 'bottom-left'],
      'right': ['right', 'top-right', 'bottom-right'],
      'top-left': ['top-left', 'top', 'left'],
      'top-right': ['top-right', 'top', 'right'],
      'bottom-left': ['bottom-left', 'bottom', 'left'],
      'bottom-right': ['bottom-right', 'bottom', 'right']
    }
    return related[dir] || [dir]
  }
  
  // === Step 1: Collect all line segments with indices ===
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
  
  // Distance threshold for penalizing nearby segments
  const DISTANCE_THRESHOLD_PER_CHAR = 25
  
  // === Step 2: Process each station in order ===
  for (let index = 0; index < path.length; index++) {
    const station = path[index]
    const coord = coordinates.value[station]
    const isEndpointStation = isEndpoint(station)
    
    if (!coord) {
      result[station] = { x: 0, y: -16, anchor: 'middle', name: 'top' }
      continue
    }
    
    // Define candidate positions
    const topY = isEndpointStation ? -15 : -10
    const bottomY = isEndpointStation ? 27 : 22
    const sideX = isEndpointStation ? 13 : 8
    const cornerX = isEndpointStation ? 8 : 4
    const cornerTopY = isEndpointStation ? -10 : -6
    const cornerBottomY = isEndpointStation ? 22 : 18
    
    const positions = {
      'top': { x: 0, y: topY, anchor: 'middle', name: 'top' },
      'bottom': { x: 0, y: bottomY, anchor: 'middle', name: 'bottom' },
      'left': { x: -sideX, y: 6, anchor: 'end', name: 'left' },
      'right': { x: sideX, y: 6, anchor: 'start', name: 'right' },
      'top-left': { x: -cornerX, y: cornerTopY, anchor: 'end', name: 'top-left' },
      'top-right': { x: cornerX, y: cornerTopY, anchor: 'start', name: 'top-right' },
      'bottom-left': { x: -cornerX, y: cornerBottomY, anchor: 'end', name: 'bottom-left' },
      'bottom-right': { x: cornerX, y: cornerBottomY, anchor: 'start', name: 'bottom-right' }
    }
    
    const allDirections = ['top', 'bottom', 'left', 'right', 'top-left', 'top-right', 'bottom-left', 'bottom-right']
    
    // Initialize direction penalties
    const directionPenalty = {}
    for (const dir of allDirections) {
      directionPenalty[dir] = 0
    }
    
    // Get adjacent station coordinates
    const prevCoord = index > 0 ? coordinates.value[path[index - 1]] : null
    const nextCoord = index < path.length - 1 ? coordinates.value[path[index + 1]] : null
    const prevStation = index > 0 ? path[index - 1] : null
    
    // === Penalize directions based on adjacent stations ===
    // Direct connection to prev station (C)
    if (prevCoord) {
      const dirToPrev = getDirectionFromPoints(coord, prevCoord)
      for (const relDir of getRelatedDirections(dirToPrev)) {
        directionPenalty[relDir] += 30 // Heavy penalty for direction towards adjacent station
      }
    }
    
    // Direct connection to next station (E)
    if (nextCoord) {
      const dirToNext = getDirectionFromPoints(coord, nextCoord)
      for (const relDir of getRelatedDirections(dirToNext)) {
        directionPenalty[relDir] += 30
      }
    }
    
    // === Traverse backwards to penalize nearby segments (BC, AB, ...) ===
    // Start from segment ending at prev station (i.e., segment index-2 to index-1)
    for (let segIdx = index - 2; segIdx >= 0; segIdx--) {
      const seg = allLineSegments[segIdx]
      if (!seg) continue
      
      const A = { x: seg.x1, y: seg.y1 }
      const B = { x: seg.x2, y: seg.y2 }
      const { distance, closestPoint } = pointToSegmentDistance(coord, A, B)
      
      if (distance < DISTANCE_THRESHOLD_PER_CHAR * station.length) {
        // Penalize the direction towards the closest point
        const dirToClosest = getDirectionFromPoints(coord, closestPoint)
        const penalty = 800 / (distance + 20) // Closer = higher penalty
        for (const relDir of getRelatedDirections(dirToClosest)) {
          directionPenalty[relDir] += penalty
        }
      }
    }
    
    // === Traverse forwards to penalize nearby segments (EF, FG, ...) ===
    // Start from segment starting at next station (i.e., segment index+1 to index+2)
    for (let segIdx = index + 1; segIdx < allLineSegments.length; segIdx++) {
      const seg = allLineSegments[segIdx]
      if (!seg) continue
      
      const A = { x: seg.x1, y: seg.y1 }
      const B = { x: seg.x2, y: seg.y2 }
      const { distance, closestPoint } = pointToSegmentDistance(coord, A, B)
      
      if (distance < DISTANCE_THRESHOLD_PER_CHAR * station.length) {
        const dirToClosest = getDirectionFromPoints(coord, closestPoint)
        const penalty = 800 / (distance + 20)
        for (const relDir of getRelatedDirections(dirToClosest)) {
          directionPenalty[relDir] += penalty
        }
      }
    }
    
    // === Penalize directions used by previous station's label ===
    const prevLabelPos = prevStation ? result[prevStation] : null
    if (prevLabelPos) {
      const prevDir = prevLabelPos.name
      // Exact match penalty
      directionPenalty[prevDir] += 15
      // Related directions penalty
      for (const relDir of getRelatedDirections(prevDir)) {
        if (relDir !== prevDir) {
          directionPenalty[relDir] += 8
        }
      }
    }
    
    // === Check collision with already placed labels ===
    const labelCollisionPenalty = {}
    for (const dir of allDirections) {
      labelCollisionPenalty[dir] = 0
      const pos = positions[dir]
      const labelBox = getLabelBox(coord, pos, pos.anchor, station)
      for (const placed of placedLabels) {
        if (boxesOverlap(labelBox, placed.box, 4)) {
          labelCollisionPenalty[dir] += 50 // Heavy penalty for label overlap
        }
      }
    }
    
    // === Determine preferred direction based on geometry ===
    let preferredDirections = []
    
    if (prevCoord && nextCoord) {
      const toW = normalize({ x: prevCoord.x - coord.x, y: prevCoord.y - coord.y })
      const toY = normalize({ x: nextCoord.x - coord.x, y: nextCoord.y - coord.y })
      // Corner: prefer angle bisector's reverse direction
      const bisector = normalize({ x: toW.x + toY.x, y: toW.y + toY.y })
      const outward = { x: -bisector.x, y: -bisector.y }
      const preferredDir = getDirectionFromVector(outward)
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
      preferredDirections = getPerpendicularDirections(toPrev)
      const awayDir = getDirectionFromVector({ x: -toPrev.x, y: -toPrev.y })
      preferredDirections.unshift(awayDir)
    } else if (nextCoord) {
      const toNext = normalize({ x: nextCoord.x - coord.x, y: nextCoord.y - coord.y })
      preferredDirections = getPerpendicularDirections(toNext)
      const awayDir = getDirectionFromVector({ x: -toNext.x, y: -toNext.y })
      preferredDirections.unshift(awayDir)
    } else {
      preferredDirections = ['top', 'bottom', 'left', 'right']
    }
    
    // === Score and select best position ===
    let bestPos = positions['top']
    let bestScore = -Infinity
    
    for (const dirName of allDirections) {
      let score = 0
      
      // Apply segment proximity penalty
      score -= directionPenalty[dirName]
      
      // Apply label collision penalty
      score -= labelCollisionPenalty[dirName]
      
      // Bonus for preferred directions
      const preferredIndex = preferredDirections.indexOf(dirName)
      if (preferredIndex !== -1) {
        score += 20 - preferredIndex * 3
      }
      
      // Slight preference for cardinal directions over corners
      if (['top', 'bottom', 'left', 'right'].includes(dirName)) {
        score += 2
      }
      
      if (score > bestScore) {
        bestScore = score
        bestPos = positions[dirName]
      }
    }
    
    result[station] = bestPos
    placedLabels.push({
      station,
      box: getLabelBox(coord, bestPos, bestPos.anchor, station)
    })
  }
  
  return result
})

// Helper to get label offset for a station
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

// Load map data
const loadMapData = async () => {
  try {
    loading.value = true
    const response = await api.getMapCoordinates()
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
  touch-action: none;
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
</style>

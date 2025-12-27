import { defineStore } from 'pinia'
import api from '@/services/api'

// City configuration
const CITY_CONFIG = {
  sz: {
    name: '深圳',
    title: '深圳地铁寻路挑战',
    subtitle: '找出两个站点之间的最短路径',
  },
  sh: {
    name: '上海',
    title: '上海地铁寻路挑战',
    subtitle: '找出两个站点之间的最短路径',
  },
  bj: {
    name: '北京',
    title: '北京地铁寻路挑战',
    subtitle: '找出两个站点之间的最短路径',
  },
  gz: {
    name: '广州',
    title: '广州地铁寻路挑战',
    subtitle: '找出两个站点之间的最短路径',
  },
  wh: {
    name: '武汉',
    title: '武汉地铁寻路挑战',
    subtitle: '找出两个站点之间的最短路径',
  },
  cs: {
    name: '长沙',
    title: '长沙地铁寻路挑战',
    subtitle: '找出两个站点之间的最短路径',
  }
}

export const useGameStore = defineStore('game', {
  state: () => ({
    // City selection
    city: 'sz',  // Default to Shenzhen
    cityConfig: CITY_CONFIG,
    
    // Available lines
    allLines: [],
    selectedLines: [],
    linesData: {},  // Line details with color and stations
    
    // Station selection
    availableStations: [],  // All stations in selected lines
    reachableStations: [],  // Stations reachable from start station
    
    // Game state
    startStation: '',
    endStation: '',
    userPath: [],
    
    // Results
    systemPaths: [],
    shortestCost: 0,
    validationResult: null,
    showAnswer: false, // 是否显示答案
    
    // UI state
    gameStatus: 'setup', // setup, playing, result, query
    loading: false,
    error: null,
  }),

  getters: {
    hasSelectedLines: (state) => state.selectedLines.length > 0,
    hasStations: (state) => state.startStation && state.endStation,
    canSubmit: (state) => state.userPath.length >= 2,
    isPlaying: (state) => state.gameStatus === 'playing' || state.gameStatus === 'result' || state.gameStatus === 'query',
    // Selected lines sorted by the order in allLines (JSON order)
    sortedSelectedLines: (state) => {
      return state.allLines.filter(line => state.selectedLines.includes(line))
    },
    displayCost: (state) => {
      if (!state.shortestCost) return 0
      // 精确到整数，.5 则进 1
      return Math.ceil(state.shortestCost)
    },
    // Get current city display info
    currentCityConfig: (state) => {
      return state.cityConfig[state.city] || state.cityConfig.sz
    },
    // Get station to lines mapping (only for selected lines)
    stationLinesMap: (state) => {
      // Helper function to extract line number for sorting
      const getLineNumber = (lineName) => {
        const match = lineName.match(/(\d+)/)
        return match ? parseInt(match[1], 10) : Infinity
      }
      
      const map = {}
      for (const lineName of state.selectedLines) {
        const lineData = state.linesData[lineName]
        if (lineData && lineData.stations) {
          // Add main line stations
          for (const station of lineData.stations) {
            if (!map[station]) {
              map[station] = []
            }
            map[station].push({
              name: lineName,
              color: lineData.color || '#3B82F6'
            })
          }
          // Also add branch stations (Y-branch lines like 5号线+)
          if (lineData.branch_stations && lineData.branch_stations.length > 0) {
            for (const station of lineData.branch_stations) {
              if (!map[station]) {
                map[station] = []
              }
              // Avoid duplicate entries for the same line
              if (!map[station].some(l => l.name === lineName)) {
                map[station].push({
                  name: lineName,
                  color: lineData.color || '#3B82F6'
                })
              }
            }
          }
        }
      }
      // Sort lines by line number for each station
      for (const station in map) {
        map[station].sort((a, b) => getLineNumber(a.name) - getLineNumber(b.name))
      }
      return map
    },
  },

  actions: {
    setCity(city) {
      if (!this.cityConfig[city]) return
      
      const isNewCity = this.city !== city
      const needsLoad = this.allLines.length === 0
      
      if (isNewCity) {
        this.city = city
        // Reset all game state when city changes
        this.allLines = []
        this.selectedLines = []
        this.linesData = {}
        this.availableStations = []
        this.reachableStations = []
        this.startStation = ''
        this.endStation = ''
        this.userPath = []
        this.systemPaths = []
        this.shortestCost = 0
        this.validationResult = null
        this.showAnswer = false
        this.gameStatus = 'setup'
        this.error = null
      }
      
      // Load data if city changed or no data loaded yet
      if (isNewCity || needsLoad) {
        this.loadLines()
      }
    },

    async loadLines() {
      try {
        this.loading = true
        this.error = null
        const response = await api.getLines(this.city)
        this.allLines = response.data
        // Also load lines data for colors and stations
        await this.loadLinesData()
      } catch (error) {
        this.error = 'Failed to load metro lines'
        console.error(error)
      } finally {
        this.loading = false
      }
    },

    async loadLinesData() {
      try {
        const response = await api.getMapCoordinates(this.city)
        this.linesData = response.data.lines || {}
      } catch (error) {
        console.error('Failed to load lines data:', error)
      }
    },

    toggleLine(lineName) {
      const index = this.selectedLines.indexOf(lineName)
      if (index > -1) {
        this.selectedLines.splice(index, 1)
      } else {
        this.selectedLines.push(lineName)
      }
      // Validate and clear stations if needed
      this.validateAndClearStations()
    },

    selectAllLines() {
      this.selectedLines = [...this.allLines]
      // Validate and clear stations if needed
      this.validateAndClearStations()
    },

    clearLines() {
      this.selectedLines = []
      // Clear stations when lines are cleared
      this.clearStationSelection()
    },

    clearStationSelection() {
      this.startStation = ''
      this.endStation = ''
      this.availableStations = []
      this.reachableStations = []
    },

    async validateAndClearStations() {
      // If no lines selected, clear everything
      if (this.selectedLines.length === 0) {
        this.clearStationSelection()
        return
      }

      // Load available stations for current lines
      await this.loadAvailableStations()

      // Check if start station is still valid
      if (this.startStation && !this.availableStations.includes(this.startStation)) {
        this.startStation = ''
        this.endStation = ''
        this.reachableStations = []
        return
      }

      // If start station is valid, reload reachable stations
      if (this.startStation) {
        await this.loadReachableStations()
        
        // Check if end station is still reachable
        if (this.endStation && !this.reachableStations.includes(this.endStation)) {
          this.endStation = ''
        }
      }
    },

    async loadAvailableStations() {
      if (!this.hasSelectedLines) {
        this.availableStations = []
        return
      }

      try {
        const response = await api.getStations(this.city, this.selectedLines)
        this.availableStations = response.data.stations
      } catch (error) {
        console.error('Failed to load available stations:', error)
        this.availableStations = []
      }
    },

    async loadReachableStations() {
      if (!this.hasSelectedLines || !this.startStation) {
        this.reachableStations = []
        return
      }

      try {
        const response = await api.getReachableStations(this.city, this.selectedLines, this.startStation)
        this.reachableStations = response.data.stations
      } catch (error) {
        console.error('Failed to load reachable stations:', error)
        this.reachableStations = []
      }
    },

    async setStartStation(station) {
      this.startStation = station
      this.endStation = ''  // Clear end station when start changes
      if (station) {
        await this.loadReachableStations()
      } else {
        this.reachableStations = []
      }
    },

    setEndStation(station) {
      this.endStation = station
    },

    async generateRandomStations() {
      if (!this.hasSelectedLines) {
        this.error = 'Please select at least one line'
        return
      }

      try {
        this.loading = true
        this.error = null
        
        // 清除之前的答案状态
        this.userPath = []
        this.validationResult = null
        this.showAnswer = false
        
        const response = await api.randomStations(this.city, this.selectedLines)
        this.startStation = response.data.start
        this.endStation = response.data.end
        // 同时获取最短路径的 cost
        const pathResponse = await api.calculatePath(
          this.city,
          this.selectedLines,
          response.data.start,
          response.data.end
        )
        this.shortestCost = pathResponse.data.shortest_cost
        this.systemPaths = pathResponse.data.paths
        // 自动填写起点和终点
        this.userPath = [this.startStation, this.endStation]
        this.gameStatus = 'playing'
      } catch (error) {
        this.error = 'Failed to generate random stations'
        console.error(error)
      } finally {
        this.loading = false
      }
    },

    async setStations(start, end) {
      this.startStation = start
      this.endStation = end
      if (start && end) {
        try {
          this.loading = true
          this.error = null
          
          // 清除之前的答案状态
          this.userPath = []
          this.validationResult = null
          this.showAnswer = false
          
          // 获取最短路径的 cost
          const pathResponse = await api.calculatePath(
            this.city,
            this.selectedLines,
            start,
            end
          )
          this.shortestCost = pathResponse.data.shortest_cost
          this.systemPaths = pathResponse.data.paths
          // 自动填写起点和终点
          this.userPath = [this.startStation, this.endStation]
          this.gameStatus = 'playing'
        } catch (error) {
          this.error = 'Failed to calculate path'
          console.error(error)
        } finally {
          this.loading = false
        }
      }
    },

    addStation(station) {
      if (station && !this.userPath.includes(station)) {
        // 游戏进行中时，插入到终点之前；否则直接添加到末尾
        if (this.gameStatus === 'playing' && this.userPath.length >= 2) {
          // 插入到倒数第二的位置（终点之前）
          this.userPath.splice(this.userPath.length - 1, 0, station)
        } else {
          this.userPath.push(station)
        }
      }
    },

    insertStation(station, index) {
      // 在指定位置插入站点
      if (station && !this.userPath.includes(station)) {
        this.userPath.splice(index, 0, station)
      }
    },

    removeStation(index) {
      // 禁止删除起点（第一站）和终点（最后一站）
      if (index === 0 || index === this.userPath.length - 1) {
        return
      }
      this.userPath.splice(index, 1)
    },

    clearPath() {
      // 保留起点和终点，只清空中间站点
      if (this.startStation && this.endStation) {
        this.userPath = [this.startStation, this.endStation]
      } else {
        this.userPath = []
      }
    },

    async submitPath() {
      if (!this.canSubmit) {
        this.error = 'Path must have at least 2 stations'
        return
      }

      try {
        this.loading = true
        this.error = null
        const response = await api.validatePath(
          this.city,
          this.selectedLines,
          this.startStation,
          this.endStation,
          this.userPath
        )
        this.validationResult = response.data
        this.shortestCost = response.data.shortest_cost
        this.systemPaths = response.data.all_shortest_paths
        // 只有答对时才显示答案
        this.showAnswer = response.data.is_shortest
        // 答对时才切换到 result 状态，答错时保持 playing 状态允许继续修改
        if (response.data.is_shortest) {
          this.gameStatus = 'result'
        }
        // 答错时保持 playing 状态，不清空用户路径
      } catch (error) {
        this.error = 'Failed to validate path'
        console.error(error)
      } finally {
        this.loading = false
      }
    },

    revealAnswer() {
      this.showAnswer = true
    },

    async fetchAndRevealAnswer() {
      try {
        this.loading = true
        this.error = null
        // 如果还没有获取过答案，先获取
        if (this.systemPaths.length === 0) {
          const pathResponse = await api.calculatePath(
            this.city,
            this.selectedLines,
            this.startStation,
            this.endStation
          )
          this.shortestCost = pathResponse.data.shortest_cost
          this.systemPaths = pathResponse.data.paths
        }
        this.showAnswer = true
      } catch (error) {
        this.error = 'Failed to fetch answer'
        console.error(error)
      } finally {
        this.loading = false
      }
    },

    async resetGame() {
      this.startStation = ''
      this.endStation = ''
      this.reachableStations = []
      this.userPath = []
      this.systemPaths = []
      this.shortestCost = 0
      this.validationResult = null
      this.showAnswer = false
      this.gameStatus = 'setup'
      this.error = null
      // Reload available stations to ensure search works properly
      if (this.hasSelectedLines) {
        await this.loadAvailableStations()
      }
    },

    async newGame() {
      this.startStation = ''
      this.endStation = ''
      this.reachableStations = []
      this.userPath = []
      this.systemPaths = []
      this.shortestCost = 0
      this.validationResult = null
      this.showAnswer = false
      this.gameStatus = 'setup'
      this.error = null
      // Reload available stations to ensure search works properly
      if (this.hasSelectedLines) {
        await this.loadAvailableStations()
      }
    },

    async queryRoute() {
      if (!this.startStation || !this.endStation) {
        this.error = 'Please select start and end stations'
        return
      }

      try {
        this.loading = true
        this.error = null
        
        // Get shortest path
        const pathResponse = await api.calculatePath(
          this.city,
          this.selectedLines,
          this.startStation,
          this.endStation
        )
        this.shortestCost = pathResponse.data.shortest_cost
        this.systemPaths = pathResponse.data.paths
        this.showAnswer = true
        this.gameStatus = 'query'  // New status for query mode
      } catch (error) {
        this.error = 'Failed to query route'
        console.error(error)
      } finally {
        this.loading = false
      }
    }
  }
})

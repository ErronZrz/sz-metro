import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  // Get all metro lines
  getLines(city) {
    return api.get(`/${city}/lines`)
  },

  // Get stations for a specific line
  getLineStations(city, lineName) {
    return api.get(`/${city}/lines/${lineName}/stations`)
  },

  // Get all stations (optionally filtered by lines)
  getStations(city, lines = null) {
    const params = lines ? { lines: lines.join(',') } : {}
    return api.get(`/${city}/stations`, { params })
  },

  // Get reachable stations from start station
  getReachableStations(city, lines, start) {
    return api.post(`/${city}/game/reachable-stations`, { lines, start })
  },

  // Generate random start and end stations
  randomStations(city, lines) {
    return api.post(`/${city}/game/random-stations`, { lines })
  },

  // Calculate shortest path
  calculatePath(city, lines, start, end) {
    return api.post(`/${city}/game/calculate-path`, { lines, start, end })
  },

  // Validate user's path
  validatePath(city, lines, start, end, userPath) {
    return api.post(`/${city}/game/validate-path`, {
      lines,
      start,
      end,
      user_path: userPath
    })
  },

  // Get map coordinates for visualization
  getMapCoordinates(city) {
    return api.get(`/${city}/map/coordinates`)
  }
}

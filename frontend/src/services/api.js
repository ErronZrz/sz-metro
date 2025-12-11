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
  getLines() {
    return api.get('/lines')
  },

  // Get stations for a specific line
  getLineStations(lineName) {
    return api.get(`/lines/${lineName}/stations`)
  },

  // Get all stations (optionally filtered by lines)
  getStations(lines = null) {
    const params = lines ? { lines: lines.join(',') } : {}
    return api.get('/stations', { params })
  },

  // Get reachable stations from start station
  getReachableStations(lines, start) {
    return api.post('/game/reachable-stations', { lines, start })
  },

  // Generate random start and end stations
  randomStations(lines) {
    return api.post('/game/random-stations', { lines })
  },

  // Calculate shortest path
  calculatePath(lines, start, end) {
    return api.post('/game/calculate-path', { lines, start, end })
  },

  // Validate user's path
  validatePath(lines, start, end, userPath) {
    return api.post('/game/validate-path', {
      lines,
      start,
      end,
      user_path: userPath
    })
  },

  // Get map coordinates for visualization
  getMapCoordinates() {
    return api.get('/map/coordinates')
  }
}

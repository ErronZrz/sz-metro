<template>
  <div class="relative" ref="containerRef">
    <!-- Input Field -->
    <div class="relative">
      <input
        ref="inputRef"
        type="text"
        :value="displayValue"
        @input="handleInput"
        @focus="handleFocus"
        @keydown="handleKeydown"
        :disabled="disabled"
        :placeholder="placeholder"
        :class="[
          'w-full border rounded-lg',
          size === 'small' ? 'px-2 py-1 pr-6 text-sm' : 'px-4 py-2 pr-8',
          disabled
            ? 'border-gray-200 bg-gray-100 text-gray-500 cursor-not-allowed'
            : 'border-gray-300 focus:ring-2 focus:ring-metro-primary focus:border-transparent bg-white'
        ]"
      />
      <!-- Dropdown Arrow -->
      <div
        class="absolute inset-y-0 right-0 flex items-center pointer-events-none"
        :class="[disabled ? 'text-gray-400' : 'text-gray-600', size === 'small' ? 'pr-1' : 'pr-3']"
      >
        <svg :class="size === 'small' ? 'w-3 h-3' : 'w-4 h-4'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      <!-- Clear Button -->
      <button
        v-if="value && !disabled"
        @click.stop="clearSelection"
        :class="['absolute inset-y-0 flex items-center text-gray-400 hover:text-gray-600', size === 'small' ? 'right-4 pr-1' : 'right-8 pr-2']"
      >
        <svg :class="size === 'small' ? 'w-3 h-3' : 'w-4 h-4'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Dropdown List -->
    <div
      v-show="isOpen && !disabled && searchQuery"
      class="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto"
    >
      <!-- No Results -->
      <div v-if="filteredOptions.length === 0" class="px-4 py-3 text-gray-500 text-center">
        {{ searchQuery ? '没有匹配的站点' : '暂无可选站点' }}
      </div>
      
      <!-- Options List -->
      <div
        v-for="(option, index) in filteredOptions"
        :key="option"
        @click="selectOption(option)"
        @mouseenter="highlightedIndex = index"
        :class="[
          'cursor-pointer transition-colors',
          size === 'small' ? 'px-2 py-1 text-sm' : 'px-4 py-2',
          index === highlightedIndex ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100',
          option === value ? 'font-medium text-metro-primary' : ''
        ]"
      >
        <span v-html="highlightMatch(option)"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  value: {
    type: String,
    default: ''
  },
  options: {
    type: Array,
    default: () => []
  },
  disabled: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: '请选择'
  },
  size: {
    type: String,
    default: 'normal',  // 'normal' or 'small'
    validator: (value) => ['normal', 'small'].includes(value)
  }
})

const emit = defineEmits(['update:value', 'confirm', 'cancel'])

const containerRef = ref(null)
const inputRef = ref(null)
const isOpen = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(0)

// Display value: show selected value or search query
const displayValue = computed(() => {
  if (isOpen.value) {
    return searchQuery.value
  }
  return props.value || ''
})

// Filtered options based on search query, with exact match prioritized
const filteredOptions = computed(() => {
  if (!searchQuery.value) {
    return props.options
  }
  const query = searchQuery.value.toLowerCase()
  const matched = props.options.filter(option => 
    option.toLowerCase().includes(query)
  )
  
  // Sort to prioritize exact match first, then prefix match, then others
  return matched.sort((a, b) => {
    const aLower = a.toLowerCase()
    const bLower = b.toLowerCase()
    
    // Exact match first
    const aExact = aLower === query
    const bExact = bLower === query
    if (aExact && !bExact) return -1
    if (!aExact && bExact) return 1
    
    // Then prefix match
    const aPrefix = aLower.startsWith(query)
    const bPrefix = bLower.startsWith(query)
    if (aPrefix && !bPrefix) return -1
    if (!aPrefix && bPrefix) return 1
    
    // Keep original order for others
    return 0
  })
})

// Highlight matching text
const highlightMatch = (text) => {
  if (!searchQuery.value) return text
  const regex = new RegExp(`(${escapeRegExp(searchQuery.value)})`, 'gi')
  return text.replace(regex, '<span class="bg-yellow-200">$1</span>')
}

// Escape special regex characters
const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const handleInput = (event) => {
  searchQuery.value = event.target.value
  highlightedIndex.value = 0
  if (!isOpen.value) {
    isOpen.value = true
  }
}

const handleFocus = () => {
  isOpen.value = true
  searchQuery.value = ''
}

const handleKeydown = (event) => {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      // Only navigate if dropdown is showing (has search query)
      if (searchQuery.value && highlightedIndex.value < filteredOptions.value.length - 1) {
        highlightedIndex.value++
      }
      break
    case 'ArrowUp':
      event.preventDefault()
      if (searchQuery.value && highlightedIndex.value > 0) {
        highlightedIndex.value--
      }
      break
    case 'Enter':
      event.preventDefault()
      if (!searchQuery.value) {
        // Empty input, do nothing
        return
      }
      
      // Directly add the highlighted option
      if (filteredOptions.value.length > 0) {
        const selectedOption = filteredOptions.value[highlightedIndex.value]
        confirmSelection(selectedOption)
      }
      break
    case 'Escape':
      closeDropdown()
      break
  }
}

// Confirm selection and close dropdown, emit confirm event for direct add
const confirmSelection = (option) => {
  emit('update:value', option)
  emit('confirm', option)
  closeDropdown()
}

// Click also directly confirms the selection
const selectOption = (option) => {
  confirmSelection(option)
}

const clearSelection = () => {
  emit('update:value', '')
  searchQuery.value = ''
}

const closeDropdown = () => {
  isOpen.value = false
  searchQuery.value = ''
  highlightedIndex.value = 0
}

// Click outside to close dropdown
const handleClickOutside = (event) => {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    closeDropdown()
    emit('cancel')  // Notify parent that selection was cancelled
  }
}

// Expose focus method for parent component
const focus = () => {
  if (inputRef.value) {
    inputRef.value.focus()
  }
}

defineExpose({ focus })

// Reset highlighted index when filtered options change
watch(filteredOptions, () => {
  highlightedIndex.value = 0
})

// Reset search query when value changes externally
watch(() => props.value, () => {
  if (!isOpen.value) {
    searchQuery.value = ''
  }
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

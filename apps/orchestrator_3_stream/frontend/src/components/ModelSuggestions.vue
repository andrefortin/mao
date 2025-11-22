<template>
  <teleport to="body">
    <div
      v-if="isOpen"
      class="model-suggestions-overlay"
      @click="handleBackdropClick"
    >
      <div class="model-suggestions-popover" @click.stop>
        <div class="suggestions-header">
          <h4>Suggested Models</h4>
          <button
            type="button"
            class="suggestions-close"
            @click="$emit('close')"
          >
            ✕
          </button>
        </div>
        <div class="suggestions-list">
          <button
            v-for="model in suggestions"
            :key="model"
            type="button"
            class="suggestion-item"
            @click="$emit('select', model)"
          >
            <div class="suggestion-content">
              <div class="model-info">
                <span class="model-name">{{ getModelDisplayName(model) }}</span>
                <span class="model-id">{{ model }}</span>
              </div>
              <div class="model-description">{{ getModelDescription(model) }}</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Props
interface Props {
  suggestions: string[]
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'select', modelId: string): void
  (e: 'close'): void
}

const emit = defineEmits<Emits>()

// State
const isOpen = ref(true)

// Methods
const getModelDisplayName = (modelId: string): string => {
  const parts = modelId.split('/')
  return parts.length > 1 ? parts[1] : modelId
}

const getModelDescription = (modelId: string): string => {
  const descriptions: Record<string, string> = {
    'anthropic/claude-3.5-sonnet': 'Most balanced model for general tasks, reasoning, and coding',
    'anthropic/claude-3-opus': 'Most capable model for complex reasoning and creative tasks',
    'anthropic/claude-3-haiku': 'Fast and affordable model for simple tasks',
    'x-ai/grok-4': 'Large language model with good reasoning capabilities',
    'x-ai/grok-4-mini': 'Lightweight version of Grok 4 for quick tasks',
    'openai/gpt-4o': 'Multimodal model with strong performance across tasks',
    'openai/gpt-4o-mini': 'Smaller, faster version of GPT-4o',
    'google/gemini-2.0-flash-exp': 'Fast experimental model with good reasoning',
    'google/gemini-1.5-pro': 'Large model with excellent reasoning capabilities',
    'google/gemini-1.5-flash': 'Fast model for quick responses',
    'meta-llama/llama-3.1-70b-instruct': 'Large open-source model for complex tasks',
    'meta-llama/llama-3.1-8b-instruct': 'Efficient open-source model for general use'
  }
  return descriptions[modelId] || 'High-quality language model'
}

const handleBackdropClick = () => {
  emit('close')
}

// Close on escape key
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.model-suggestions-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 60;
  padding: var(--spacing-lg);
  backdrop-filter: blur(1px);
}

.model-suggestions-popover {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  max-width: 480px;
  width: 100%;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.suggestions-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suggestions-header h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.suggestions-close {
  width: 24px;
  height: 24px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestions-close:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.suggestions-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.suggestion-item {
  width: 100%;
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  margin-bottom: var(--spacing-sm);
}

.suggestion-item:last-child {
  margin-bottom: 0;
}

.suggestion-item:hover {
  background: var(--bg-tertiary);
  border-color: var(--accent-primary);
  transform: translateY(-1px);
}

.suggestion-item:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

.suggestion-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.model-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.model-id {
  font-size: 0.75rem;
  font-family: var(--font-mono);
  color: var(--text-muted);
  opacity: 0.8;
}

.model-description {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Scrollbar styling */
.suggestions-list::-webkit-scrollbar {
  width: 6px;
}

.suggestions-list::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

.suggestions-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.suggestions-list::-webkit-scrollbar-thumb:hover {
  background: var(--border-light);
}

/* Responsive design */
@media (max-width: 640px) {
  .model-suggestions-overlay {
    padding: var(--spacing-md);
  }

  .suggestions-header {
    padding: var(--spacing-sm) var(--spacing-md);
  }

  .suggestions-list {
    padding: var(--spacing-xs);
  }

  .suggestion-item {
    padding: var(--spacing-sm);
  }
}
</style>
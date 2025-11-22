<template>
  <teleport to="body">
    <div v-if="isOpen" class="openrouter-config-backdrop" @click="handleBackdropClick">
      <div class="openrouter-config-modal" @click.stop>
        <!-- Modal Header -->
        <div class="modal-header">
          <div class="header-content">
            <div class="title-section">
              <img
                src="../assets/llm-providers/openrouter.svg"
                alt="OpenRouter Logo"
                class="provider-logo"
                loading="lazy"
                decoding="async"
              />
              <div>
                <h2>OpenRouter Configuration</h2>
                <p class="modal-subtitle">Configure models for different agent types</p>
              </div>
            </div>
            <button
              type="button"
              class="close-button"
              @click="handleClose"
              title="Close configuration"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Modal Body -->
        <div class="modal-body">
          <!-- Configuration Description -->
          <div class="config-description">
            <p>
              Select which OpenRouter models to use for different types of agents.
              You can use any valid OpenRouter model ID (e.g., <code>anthropic/claude-3.5-sonnet</code>,
              <code>x-ai/grok-4</code>, <code>google/gemini-2.0-flash-exp</code>).
            </p>
          </div>

          <!-- Model Configuration Sections -->
          <div class="config-sections">
            <!-- Orchestrator Model -->
            <div class="config-section">
              <div class="section-header">
                <div class="section-title">
                  <span class="section-icon">🧠</span>
                  <div>
                    <h3>Orchestrator Model</h3>
                    <p class="section-description">
                      Main model for coordination and complex reasoning tasks
                    </p>
                  </div>
                </div>
                <div class="model-badge" v-if="config.orchestrator_model">
                  {{ getModelDisplayName(config.orchestrator_model) }}
                </div>
              </div>
              <div class="model-input-group">
                <div class="input-wrapper">
                  <input
                    v-model="config.orchestrator_model"
                    type="text"
                    placeholder="e.g., anthropic/claude-3.5-sonnet"
                    class="model-input"
                    @input="handleOrchestratorInput"
                  />
                  <div class="input-actions">
                    <button
                      type="button"
                      class="action-button"
                      @click="showOrchestratorSuggestions = !showOrchestratorSuggestions"
                      title="Show suggested models"
                    >
                      💡
                    </button>
                  </div>
                </div>
                <ModelSuggestions
                  v-if="showOrchestratorSuggestions"
                  :suggestions="orchestratorSuggestions"
                  @select="selectOrchestratorModel"
                  @close="showOrchestratorSuggestions = false"
                />
              </div>
            </div>

            <!-- Default Agent Model -->
            <div class="config-section">
              <div class="section-header">
                <div class="section-title">
                  <span class="section-icon">🤖</span>
                  <div>
                    <h3>Default Agent Model</h3>
                    <p class="section-description">
                      Standard model for most agent tasks and operations
                    </p>
                  </div>
                </div>
                <div class="model-badge" v-if="config.default_agent_model">
                  {{ getModelDisplayName(config.default_agent_model) }}
                </div>
              </div>
              <div class="model-input-group">
                <div class="input-wrapper">
                  <input
                    v-model="config.default_agent_model"
                    type="text"
                    placeholder="e.g., x-ai/grok-4"
                    class="model-input"
                    @input="handleDefaultAgentInput"
                  />
                  <div class="input-actions">
                    <button
                      type="button"
                      class="action-button"
                      @click="showDefaultAgentSuggestions = !showDefaultAgentSuggestions"
                      title="Show suggested models"
                    >
                      💡
                    </button>
                  </div>
                </div>
                <ModelSuggestions
                  v-if="showDefaultAgentSuggestions"
                  :suggestions="defaultAgentSuggestions"
                  @select="selectDefaultAgentModel"
                  @close="showDefaultAgentSuggestions = false"
                />
              </div>
            </div>

            <!-- Fast Model -->
            <div class="config-section">
              <div class="section-header">
                <div class="section-title">
                  <span class="section-icon">⚡</span>
                  <div>
                    <h3>Fast Model</h3>
                    <p class="section-description">
                      Lightweight model for quick tasks and simple operations
                    </p>
                  </div>
                </div>
                <div class="model-badge" v-if="config.fast_model">
                  {{ getModelDisplayName(config.fast_model) }}
                </div>
              </div>
              <div class="model-input-group">
                <div class="input-wrapper">
                  <input
                    v-model="config.fast_model"
                    type="text"
                    placeholder="e.g., x-ai/grok-4-mini"
                    class="model-input"
                    @input="handleFastModelInput"
                  />
                  <div class="input-actions">
                    <button
                      type="button"
                      class="action-button"
                      @click="showFastModelSuggestions = !showFastModelSuggestions"
                      title="Show suggested models"
                    >
                      💡
                    </button>
                  </div>
                </div>
                <ModelSuggestions
                  v-if="showFastModelSuggestions"
                  :suggestions="fastModelSuggestions"
                  @select="selectFastModel"
                  @close="showFastModelSuggestions = false"
                />
              </div>
            </div>
          </div>

          <!-- Model Information Display -->
          <div class="model-info-section" v-if="selectedModelInfo">
            <div class="info-header">
              <h4>{{ selectedModelInfo.name }}</h4>
              <button
                type="button"
                class="info-close"
                @click="selectedModelInfo = null"
              >
                ✕
              </button>
            </div>
            <div class="info-content">
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Provider:</span>
                  <span class="info-value">{{ selectedModelInfo.provider }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Context Window:</span>
                  <span class="info-value">{{ formatNumber(selectedModelInfo.contextLength) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Input Cost:</span>
                  <span class="info-value">${{ selectedModelInfo.pricing.prompt }}/1M tokens</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Output Cost:</span>
                  <span class="info-value">${{ selectedModelInfo.pricing.completion }}/1M tokens</span>
                </div>
              </div>
              <p class="info-description">{{ selectedModelInfo.description }}</p>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="modal-footer">
          <div class="footer-left">
            <button
              type="button"
              class="reset-button"
              @click="handleReset"
              title="Reset to default values"
            >
              Reset to Defaults
            </button>
          </div>
          <div class="footer-right">
            <button
              type="button"
              class="cancel-button"
              @click="handleClose"
            >
              Cancel
            </button>
            <button
              type="button"
              class="apply-button"
              @click="handleApply"
              :disabled="!hasChanges || !isValid"
            >
              Apply Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { LlmProviderOption, LlmProviderState } from '../types'
import ModelSuggestions from './ModelSuggestions.vue'

// Props
interface Props {
  isOpen: boolean
  provider?: LlmProviderOption | null
  currentConfig?: Partial<LlmProviderState> | null
}

const props = withDefaults(defineProps<Props>(), {
  provider: null,
  currentConfig: null
})

// Emits
interface Emits {
  (e: 'close'): void
  (e: 'apply', config: OpenRouterConfig): void
}

const emit = defineEmits<Emits>()

// Types
interface OpenRouterConfig {
  orchestrator_model: string
  default_agent_model: string
  fast_model: string
}

interface ModelInfo {
  id: string
  name: string
  provider: string
  description: string
  contextLength: number
  pricing: {
    prompt: number
    completion: number
  }
}

// Reactive state
const config = ref<OpenRouterConfig>({
  orchestrator_model: '',
  default_agent_model: '',
  fast_model: ''
})

const originalConfig = ref<OpenRouterConfig>({
  orchestrator_model: '',
  default_agent_model: '',
  fast_model: ''
})

// UI state
const showOrchestratorSuggestions = ref(false)
const showDefaultAgentSuggestions = ref(false)
const showFastModelSuggestions = ref(false)
const selectedModelInfo = ref<ModelInfo | null>(null)

// Model suggestions (this would typically come from an API)
const orchestratorSuggestions = computed(() => [
  'anthropic/claude-3.5-sonnet',
  'anthropic/claude-3-opus',
  'x-ai/grok-4',
  'google/gemini-2.0-flash-exp',
  'openai/gpt-4o'
])

const defaultAgentSuggestions = computed(() => [
  'anthropic/claude-3.5-sonnet',
  'x-ai/grok-4',
  'google/gemini-1.5-pro',
  'openai/gpt-4o',
  'meta-llama/llama-3.1-70b-instruct'
])

const fastModelSuggestions = computed(() => [
  'anthropic/claude-3-haiku',
  'x-ai/grok-4-mini',
  'google/gemini-1.5-flash',
  'openai/gpt-4o-mini',
  'meta-llama/llama-3.1-8b-instruct'
])

// Computed
const hasChanges = computed(() => {
  return (
    config.value.orchestrator_model !== originalConfig.value.orchestrator_model ||
    config.value.default_agent_model !== originalConfig.value.default_agent_model ||
    config.value.fast_model !== originalConfig.value.fast_model
  )
})

const isValid = computed(() => {
  // Basic validation - at least one model should be configured
  return (
    config.value.orchestrator_model.trim() !== '' ||
    config.value.default_agent_model.trim() !== '' ||
    config.value.fast_model.trim() !== ''
  )
})

// Watchers
watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    await nextTick()
    initializeConfig()
  }
})

// Methods
const initializeConfig = () => {
  const initialConfig = props.currentConfig || props.provider || {}

  config.value = {
    orchestrator_model: initialConfig.orchestrator_model || '',
    default_agent_model: initialConfig.default_agent_model || '',
    fast_model: initialConfig.fast_model || ''
  }

  originalConfig.value = { ...config.value }
}

const getModelDisplayName = (modelId: string): string => {
  // Extract the model name from the ID for display
  const parts = modelId.split('/')
  return parts.length > 1 ? parts[1] : modelId
}

const selectOrchestratorModel = (modelId: string) => {
  config.value.orchestrator_model = modelId
  showOrchestratorSuggestions.value = false
  fetchModelInfo(modelId)
}

const selectDefaultAgentModel = (modelId: string) => {
  config.value.default_agent_model = modelId
  showDefaultAgentSuggestions.value = false
  fetchModelInfo(modelId)
}

const selectFastModel = (modelId: string) => {
  config.value.fast_model = modelId
  showFastModelSuggestions.value = false
  fetchModelInfo(modelId)
}

const handleOrchestratorInput = () => {
  showOrchestratorSuggestions.value = false
  if (config.value.orchestrator_model) {
    fetchModelInfo(config.value.orchestrator_model)
  }
}

const handleDefaultAgentInput = () => {
  showDefaultAgentSuggestions.value = false
  if (config.value.default_agent_model) {
    fetchModelInfo(config.value.default_agent_model)
  }
}

const handleFastModelInput = () => {
  showFastModelSuggestions.value = false
  if (config.value.fast_model) {
    fetchModelInfo(config.value.fast_model)
  }
}

const fetchModelInfo = async (modelId: string) => {
  // This would typically make an API call to OpenRouter
  // For now, we'll provide mock data based on known models
  const mockModelInfo: Record<string, ModelInfo> = {
    'anthropic/claude-3.5-sonnet': {
      id: 'anthropic/claude-3.5-sonnet',
      name: 'Claude 3.5 Sonnet',
      provider: 'Anthropic',
      description: 'Most balanced model for general tasks, reasoning, and coding.',
      contextLength: 200000,
      pricing: { prompt: 3.0, completion: 15.0 }
    },
    'anthropic/claude-3-opus': {
      id: 'anthropic/claude-3-opus',
      name: 'Claude 3 Opus',
      provider: 'Anthropic',
      description: 'Most capable model for complex reasoning and creative tasks.',
      contextLength: 200000,
      pricing: { prompt: 15.0, completion: 75.0 }
    },
    'anthropic/claude-3-haiku': {
      id: 'anthropic/claude-3-haiku',
      name: 'Claude 3 Haiku',
      provider: 'Anthropic',
      description: 'Fast and affordable model for simple tasks.',
      contextLength: 200000,
      pricing: { prompt: 0.25, completion: 1.25 }
    },
    'x-ai/grok-4': {
      id: 'x-ai/grok-4',
      name: 'Grok 4',
      provider: 'xAI',
      description: 'Large language model with good reasoning capabilities.',
      contextLength: 131072,
      pricing: { prompt: 5.0, completion: 15.0 }
    },
    'openai/gpt-4o': {
      id: 'openai/gpt-4o',
      name: 'GPT-4o',
      provider: 'OpenAI',
      description: 'Multimodal model with strong performance across tasks.',
      contextLength: 128000,
      pricing: { prompt: 2.5, completion: 10.0 }
    },
    'google/gemini-2.0-flash-exp': {
      id: 'google/gemini-2.0-flash-exp',
      name: 'Gemini 2.0 Flash (Experimental)',
      provider: 'Google',
      description: 'Fast experimental model with good reasoning.',
      contextLength: 1048576,
      pricing: { prompt: 0.075, completion: 0.3 }
    }
  }

  selectedModelInfo.value = mockModelInfo[modelId] || null
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(0)}K`
  }
  return num.toString()
}

const handleReset = () => {
  config.value = {
    orchestrator_model: props.provider?.default_model || '',
    default_agent_model: props.provider?.default_model || '',
    fast_model: props.provider?.fast_model || ''
  }
}

const handleClose = () => {
  emit('close')
}

const handleApply = () => {
  if (isValid.value) {
    emit('apply', { ...config.value })
  }
}

const handleBackdropClick = () => {
  handleClose()
}
</script>

<style scoped>
/* Modal Backdrop */
.openrouter-config-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 10, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: var(--spacing-lg);
  backdrop-filter: blur(2px);
}

/* Modal Container */
.openrouter-config-modal {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  max-width: 720px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow:
    0 20px 45px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

/* Modal Header */
.modal-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-lg);
}

.title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.provider-logo {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--bg-primary);
  padding: 0.5rem;
}

.title-section h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.modal-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0 0;
}

.close-button {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-button:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

/* Modal Body */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.config-description {
  padding: var(--spacing-md);
  background: rgba(6, 182, 212, 0.05);
  border: 1px solid rgba(6, 182, 212, 0.1);
  border-radius: 8px;
  border-left: 4px solid var(--accent-primary);
}

.config-description p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.config-description code {
  font-family: var(--font-mono);
  background: var(--bg-tertiary);
  color: var(--accent-primary);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.8em;
}

/* Configuration Sections */
.config-sections {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.config-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.section-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
}

.section-icon {
  font-size: 1.5rem;
  line-height: 1;
  margin-top: 0.125rem;
}

.section-title h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-description {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0 0;
  line-height: 1.4;
}

.model-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.375rem 0.75rem;
  background: var(--accent-primary);
  color: white;
  border-radius: 999px;
  white-space: nowrap;
}

/* Model Input Groups */
.model-input-group {
  padding: var(--spacing-lg);
  position: relative;
}

.input-wrapper {
  display: flex;
  gap: var(--spacing-sm);
}

.model-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-family: var(--font-mono);
  outline: none;
  transition: all 0.2s ease;
}

.model-input:focus {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

.model-input::placeholder {
  color: var(--text-muted);
  opacity: 0.7;
}

.input-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.action-button {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-tertiary);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-button:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  background: var(--bg-quaternary);
}

/* Model Information Display */
.model-info-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.info-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-header h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.info-close {
  width: 24px;
  height: 24px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.info-close:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.info-content {
  padding: var(--spacing-lg);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
}

.info-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* Modal Footer */
.modal-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-lg);
}

.footer-left,
.footer-right {
  display: flex;
  gap: var(--spacing-sm);
}

.reset-button,
.cancel-button,
.apply-button {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.reset-button {
  background: var(--bg-tertiary);
  color: var(--text-muted);
  border-color: var(--border-color);
}

.reset-button:hover {
  background: var(--bg-quaternary);
  color: var(--text-primary);
  border-color: var(--border-light);
}

.cancel-button {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.cancel-button:hover {
  background: var(--bg-quaternary);
  border-color: var(--border-light);
}

.apply-button {
  background: var(--accent-primary);
  color: white;
  border-color: var(--accent-primary);
}

.apply-button:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.apply-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Responsive Design */
@media (max-width: 768px) {
  .openrouter-config-backdrop {
    padding: var(--spacing-md);
  }

  .openrouter-config-modal {
    max-height: 95vh;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-md);
  }

  .title-section {
    width: 100%;
  }

  .modal-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .footer-left,
  .footer-right {
    justify-content: center;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}

/* Scrollbar Styling */
.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

.modal-body::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: var(--border-light);
}
</style>
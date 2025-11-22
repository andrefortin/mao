<template>
  <header class="app-header">
    <div class="header-content">
      <div class="header-title">
        <h1>MULTI-AGENT ORCHESTRATION</h1>
        <div class="header-subtitle-group">
          <span class="header-subtitle">LIVE LOG STREAM</span>
          <div class="connection-status">
            <span class="status-indicator" :class="{ online: store.isConnected }"></span>
            <span class="status-text">{{
              store.isConnected ? "Connected" : "Disconnected"
            }}</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <LlmProviderSwitcher
          class="provider-switcher"
          :providers="store.llmProviders"
          :active-provider="store.activeLlmProvider"
          :loading="store.llmProviderLoading"
          :disabled="store.isSwitchingProvider"
          @select="handleProviderSelect"
          @edit="handleProviderEdit"
        />
        <div class="header-stats">
          <div class="stat-item stat-pill">
            <span class="stat-label">Active:</span>
            <span class="stat-value">{{ headerBar.activeAgentCount }}</span>
          </div>
          <div class="stat-item stat-pill">
            <span class="stat-label">Running:</span>
            <span class="stat-value">{{ headerBar.runningAgentCount }}</span>
          </div>
          <div class="stat-item stat-pill">
            <span class="stat-label">Logs:</span>
            <span class="stat-value">{{ headerBar.logCount }}</span>
          </div>
          <div class="stat-item stat-pill">
            <span class="stat-label">Cost:</span>
            <span class="stat-value">${{ headerBar.formattedCost }}</span>
          </div>
        </div>

        <div class="header-actions">
          <button class="btn-clear" @click="headerBar.clearEventStream">
            CLEAR ALL
          </button>
          <button
            class="btn-prompt"
            :class="{ active: store.commandInputVisible }"
            @click="store.toggleCommandInput"
            title="Toggle command input (Cmd+K / Ctrl+K)"
          >
            PROMPT <span class="btn-hint">(Cmd+K)</span>
          </button>
        </div>
      </div>
    </div>
  </header>
  <div v-if="showProviderModal" class="provider-modal-backdrop">
    <div class="provider-modal">
      <h3>Configure OpenRouter Models</h3>
      <p class="provider-modal-description">
        Specify the models OpenRouter should use for the orchestrator, managed agents, and fast
        helper tasks. You can paste any OpenRouter model ID (e.g. <code>anthropic/claude-3.5-sonnet</code> or <code>x-ai/grok-4</code>).
      </p>
      <label class="provider-modal-field">
        <span>Orchestrator Model</span>
        <input v-model="providerForm.orchestrator_model" placeholder="x-ai/grok-4" />
      </label>
      <label class="provider-modal-field">
        <span>Default Agent Model</span>
        <input v-model="providerForm.default_agent_model" placeholder="x-ai/grok-4" />
      </label>
      <label class="provider-modal-field">
        <span>Fast Model</span>
        <input v-model="providerForm.fast_model" placeholder="x-ai/grok-4.1-fast" />
      </label>
      <div class="provider-modal-actions">
        <button class="btn-secondary" type="button" @click="handleProviderModalCancel">
          Cancel
        </button>
        <button class="btn-primary" type="button" @click="submitProviderModal">
          Apply
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { LlmProviderOption } from '../types'
import { useHeaderBar } from "../composables/useHeaderBar";
import { useOrchestratorStore } from '../stores/orchestratorStore';
import LlmProviderSwitcher from './LlmProviderSwitcher.vue'

// Use header bar composable for state management
const headerBar = useHeaderBar();

// Use store for command input visibility
const store = useOrchestratorStore();

const showProviderModal = ref(false)
const pendingProvider = ref<LlmProviderOption | null>(null)
const providerForm = ref({
  orchestrator_model: '',
  default_agent_model: '',
  fast_model: ''
})
const OPENROUTER_FORM_KEY = 'mao-openrouter-models'

const loadSavedOpenRouterModels = () => {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(OPENROUTER_FORM_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const saveOpenRouterModels = (values: typeof providerForm.value) => {
  if (typeof window === 'undefined') return
  localStorage.setItem(OPENROUTER_FORM_KEY, JSON.stringify(values))
}

const resetProviderModal = () => {
  showProviderModal.value = false
  pendingProvider.value = null
  providerForm.value = {
    orchestrator_model: '',
    default_agent_model: '',
    fast_model: ''
  }
}

const openProviderModal = (provider: LlmProviderOption) => {
  pendingProvider.value = provider
  const saved = loadSavedOpenRouterModels()
  if (saved) {
    providerForm.value = saved
  } else if (store.activeLlmProvider?.provider_id === 'openrouter') {
    providerForm.value = {
      orchestrator_model: store.activeLlmProvider.orchestrator_model,
      default_agent_model: store.activeLlmProvider.default_agent_model,
      fast_model: store.activeLlmProvider.fast_model
    }
  } else {
    providerForm.value = {
      orchestrator_model: provider.default_model ?? '',
      default_agent_model: provider.default_model ?? '',
      fast_model: provider.fast_model ?? ''
    }
  }
  showProviderModal.value = true
}

const submitProviderModal = async () => {
  if (!pendingProvider.value) return
  try {
    await store.selectLlmProvider(pendingProvider.value.id, { ...providerForm.value })
    saveOpenRouterModels(providerForm.value)
  } finally {
    resetProviderModal()
  }
}

const handleProviderSelect = async (providerId: string) => {
  try {
    await store.selectLlmProvider(providerId)
  } catch (error) {
    console.error('Failed to switch provider:', error)
  }
}

const handleProviderEdit = (providerId: string) => {
  const provider = store.llmProviders.find(p => p.id === providerId)
  if (provider && provider.id === 'openrouter') {
    openProviderModal(provider)
  }
}

const handleProviderModalCancel = () => {
  resetProviderModal()
}

watch(
  () => store.activeLlmProvider,
  value => {
    if (value?.provider_id === 'openrouter') {
      saveOpenRouterModels({
        orchestrator_model: value.orchestrator_model,
        default_agent_model: value.default_agent_model,
        fast_model: value.fast_model
      })
    }
  },
  { immediate: true }
)
</script>

<style scoped>
/* Header */
.app-header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: var(--spacing-md) var(--spacing-lg);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
}

.header-title {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

.header-subtitle-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xxs, 0.125rem);
}

.header-title h1 {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-primary);
  margin: 0;
}

.header-subtitle {
  font-size: 0.875rem;
  color: var(--accent-primary);
  font-weight: 600;
  letter-spacing: 0.025em;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  padding-left: var(--spacing-sm);
  margin-left: var(--spacing-sm);
  border-left: 1px solid var(--border-color);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-indicator.online {
  background: var(--status-success);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.status-text {
  font-weight: 500;
}

.header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-end;
  gap: var(--spacing-lg);
  flex: 1;
}

.provider-switcher {
  flex: 1 1 280px;
  min-width: 220px;
}

.header-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  padding-left: var(--spacing-xl);
  border-left: 1px solid var(--border-color);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.875rem;
}

.stat-label {
  color: var(--text-muted);
  font-weight: 500;
}

.stat-value {
  color: var(--text-primary);
  font-weight: 700;
  font-family: var(--font-mono);
}

/* Stat Pills - Flat Gray Badge Style */
.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 0.375rem 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 12px;
  font-size: 0.875rem;
  border: 1px solid var(--border-light);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.stat-pill:hover {
  background: var(--bg-quaternary);
  border-color: var(--border-color);
}

.stat-pill .stat-label {
  color: var(--text-muted);
  font-weight: 500;
  font-size: 0.8125rem;
}

.stat-pill .stat-value {
  color: var(--text-primary);
  font-weight: 700;
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

.provider-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
}

.provider-modal {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.5rem;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.25);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.provider-modal h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.provider-modal-description {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.provider-modal-description code {
  font-family: var(--font-mono);
  background: var(--bg-quaternary);
  padding: 0 0.25rem;
  border-radius: 4px;
}

.provider-modal-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.provider-modal-field input {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.9rem;
}

.provider-modal-field input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.provider-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.5rem 1rem;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-secondary {
  background: transparent;
  border-color: var(--border-color);
  color: var(--text-primary);
}

.btn-secondary:hover {
  border-color: var(--accent-primary);
}

.btn-primary {
  background: var(--accent-primary);
  color: #fff;
  border-color: var(--accent-primary);
}

.btn-primary:hover {
  opacity: 0.9;
}

/* Action Buttons */
.btn-prompt,
.btn-clear {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-hint {
  font-size: 0.65rem;
  font-weight: 500;
  opacity: 0.7;
  margin-left: 0.25rem;
}

.btn-prompt:hover,
.btn-clear:hover {
  background: var(--bg-quaternary);
  color: var(--text-primary);
  border-color: var(--accent-primary);
  transform: translateY(-1px);
}

.btn-prompt.active {
  background: var(--accent-primary);
  color: white;
  border-color: var(--accent-primary);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

/* Responsive */
@media (max-width: 1200px) {
  .header-stats {
    gap: var(--spacing-md);
  }
}

@media (max-width: 1024px) {
  .header-title h1 {
    font-size: 0.875rem;
  }

  .header-subtitle {
    font-size: 0.75rem;
  }
}
</style>

<template>
  <div class="llm-switcher">
    <div class="switcher-header">
      <span class="label">LLM Provider</span>
      <span v-if="activeProvider" class="active-label">
        {{ activeProvider.provider_label }}
      </span>
    </div>
    <div class="switcher-body">
      <button
        v-for="provider in providers"
        :key="provider.id"
        class="provider-chip"
        :class="{
          active: provider.id === activeProvider?.provider_id,
          disabled: loading || !provider.is_ready || disabled
        }"
        :disabled="loading || !provider.is_ready || disabled"
        @click="$emit('select', provider.id)"
        :title="formatProviderTooltip(provider)"
      >
        <span class="icon" :class="{ 'icon--image': providerIcons[provider.id] }">
          <img
            v-if="providerIcons[provider.id]"
            :src="providerIcons[provider.id]"
            :alt="`${provider.label} logo`"
            loading="lazy"
            decoding="async"
          />
          <span v-else>{{ provider.icon }}</span>
        </span>
        <div class="chip-content">
          <span class="name">{{ provider.label }}</span>
          <span class="meta" v-if="!provider.is_ready">
            Missing {{ provider.missing_keys.join(', ') }}
          </span>
        </div>
        <button
          v-if="provider.id === 'openrouter'"
          type="button"
          class="edit-button"
          :disabled="loading || !provider.is_ready || disabled"
          @click.stop="$emit('edit', provider.id)"
          title="Configure OpenRouter models"
        >
          ✎
        </button>
      </button>
      <div v-if="!providers.length" class="empty-state">
        <span v-if="loading">Loading providers…</span>
        <span v-else>No providers configured</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import iconAnthropic from '../assets/llm-providers/anthropic.svg'
import iconOpenai from '../assets/llm-providers/openai.svg'
import iconOpenrouter from '../assets/llm-providers/openrouter.svg'
import iconXai from '../assets/llm-providers/xai.svg'
import iconZai from '../assets/llm-providers/zai.svg'
import type { LlmProviderOption, LlmProviderState } from '../types'

defineProps<{
  providers: LlmProviderOption[]
  activeProvider: LlmProviderState | null
  loading?: boolean
  disabled?: boolean
}>()

defineEmits<{
  (e: 'select', providerId: string): void
  (e: 'edit', providerId: string): void
}>()

const providerIcons: Partial<Record<string, string>> = {
  anthropic: iconAnthropic,
  openai: iconOpenai,
  openrouter: iconOpenrouter,
  xai: iconXai,
  zai: iconZai,
}

const formatProviderTooltip = (provider: LlmProviderOption): string => {
  const lines: string[] = [provider.label]
  if (provider.fast_model) {
    lines.push(`Fast: ${provider.fast_model}`)
  }
  if (provider.default_model) {
    lines.push(`Default: ${provider.default_model}`)
  }
  if (provider.available_models?.length) {
    lines.push(`Models: ${provider.available_models.join(', ')}`)
  }
  if (!provider.is_ready && provider.missing_keys?.length) {
    lines.push(`Missing: ${provider.missing_keys.join(', ')}`)
  }
  return lines.join('\n')
}
</script>

<style scoped>
.llm-switcher {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.switcher-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.switcher-body {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.provider-chip {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  border-radius: 12px;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.provider-chip:hover:not(.disabled) {
  border-color: var(--accent-primary);
  background: var(--bg-quaternary);
}

.provider-chip.active {
  border-color: var(--accent-primary);
  background: rgba(59, 130, 246, 0.1);
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.provider-chip.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1rem;
}

.icon--image {
  background: var(--bg-primary);
  padding: 0.25rem;
}

.icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.chip-content {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  flex: 1;
}

.name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.meta {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.edit-button {
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-muted);
  border-radius: 50%;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.edit-button:hover:not(:disabled) {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.edit-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-state {
  font-size: 0.85rem;
  color: var(--text-muted);
}
</style>

import { apiClient } from './api'
import type { GetLlmProvidersResponse, LlmProviderState } from '../types'

export async function fetchLlmProviders(): Promise<GetLlmProvidersResponse> {
  const response = await apiClient.get<GetLlmProvidersResponse>('/api/llm/providers')
  return response.data
}

export interface SelectLlmProviderPayload {
  provider_id: string
  orchestrator_model?: string
  default_agent_model?: string
  fast_model?: string
}

export async function selectLlmProvider(
  payload: SelectLlmProviderPayload
): Promise<{ active: LlmProviderState }> {
  const response = await apiClient.post<{ active: LlmProviderState }>(
    '/api/llm/providers/select',
    payload
  )
  return response.data
}

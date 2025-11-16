import type {
  Bag,
  Flight,
  MishandledBag,
  AgentInsight,
  PredictionInsight,
  RootCauseInsight,
  InfrastructureIssue,
  DemandForecast,
  Approval,
  KPIMetrics,
  ChartData,
} from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

class APIClient {
  private baseURL: string
  private apiKey: string | null = null

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  setApiKey(key: string) {
    this.apiKey = key
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Bag Operations
  async getBags(filters?: {
    status?: string
    airline?: string
    flight_id?: string
    risk_level?: string
  }): Promise<Bag[]> {
    const params = new URLSearchParams(filters as Record<string, string>)
    return this.request<Bag[]>(`/bags?${params}`)
  }

  async getBag(id: string): Promise<Bag> {
    return this.request<Bag>(`/bags/${id}`)
  }

  async searchBags(query: string): Promise<Bag[]> {
    return this.request<Bag[]>(`/bags/search?q=${encodeURIComponent(query)}`)
  }

  async updateBagStatus(id: string, status: string, location?: string): Promise<Bag> {
    return this.request<Bag>(`/bags/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, location }),
    })
  }

  // Flight Operations
  async getFlights(filters?: {
    status?: string
    airport?: string
    hours_ahead?: number
  }): Promise<Flight[]> {
    const params = new URLSearchParams(filters as Record<string, string>)
    return this.request<Flight[]>(`/flights?${params}`)
  }

  async getFlight(id: string): Promise<Flight> {
    return this.request<Flight>(`/flights/${id}`)
  }

  async getFlightBags(flightId: string): Promise<Bag[]> {
    return this.request<Bag[]>(`/flights/${flightId}/bags`)
  }

  // Mishandled Bags
  async getMishandledBags(filters?: {
    status?: string
    type?: string
    handler?: string
  }): Promise<MishandledBag[]> {
    const params = new URLSearchParams(filters as Record<string, string>)
    return this.request<MishandledBag[]>(`/mishandled?${params}`)
  }

  async getMishandledBag(id: string): Promise<MishandledBag> {
    return this.request<MishandledBag>(`/mishandled/${id}`)
  }

  async updateMishandledBag(
    id: string,
    updates: Partial<MishandledBag>
  ): Promise<MishandledBag> {
    return this.request<MishandledBag>(`/mishandled/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  }

  async assignHandler(bagId: string, handlerId: string): Promise<MishandledBag> {
    return this.request<MishandledBag>(`/mishandled/${bagId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ handler_id: handlerId }),
    })
  }

  // AI Agents
  async getAgentsStatus(): Promise<AgentInsight[]> {
    return this.request<AgentInsight[]>('/agents/status')
  }

  async invokeAgent(agentName: string, inputData: any): Promise<any> {
    return this.request(`/agents/invoke`, {
      method: 'POST',
      body: JSON.stringify({ agent_name: agentName, input_data: inputData }),
    })
  }

  async getPredictions(): Promise<PredictionInsight[]> {
    return this.request<PredictionInsight[]>('/agents/prediction/insights')
  }

  async getRootCauses(period: 'day' | 'week' | 'month' = 'week'): Promise<RootCauseInsight[]> {
    return this.request<RootCauseInsight[]>(`/agents/root-cause/insights?period=${period}`)
  }

  async getInfrastructureIssues(): Promise<InfrastructureIssue[]> {
    return this.request<InfrastructureIssue[]>('/agents/infrastructure/issues')
  }

  async getDemandForecast(hours: number = 24): Promise<DemandForecast[]> {
    return this.request<DemandForecast[]>(`/agents/demand/forecast?hours=${hours}`)
  }

  // Approvals
  async getApprovals(filters?: {
    status?: string
    urgency?: string
    type?: string
  }): Promise<Approval[]> {
    const params = new URLSearchParams(filters as Record<string, string>)
    return this.request<Approval[]>(`/approvals?${params}`)
  }

  async approveRequest(id: string, comments?: string): Promise<Approval> {
    return this.request<Approval>(`/approvals/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    })
  }

  async denyRequest(id: string, reason: string): Promise<Approval> {
    return this.request<Approval>(`/approvals/${id}/deny`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    })
  }

  async bulkApprove(ids: string[]): Promise<Approval[]> {
    return this.request<Approval[]>('/approvals/bulk-approve', {
      method: 'POST',
      body: JSON.stringify({ approval_ids: ids }),
    })
  }

  // Analytics
  async getKPIMetrics(): Promise<KPIMetrics> {
    return this.request<KPIMetrics>('/analytics/kpis')
  }

  async getBagsOverTime(
    period: 'hour' | 'day' | 'week' | 'month',
    days: number = 7
  ): Promise<ChartData[]> {
    return this.request<ChartData[]>(`/analytics/bags-over-time?period=${period}&days=${days}`)
  }

  async getMishandlingByCause(days: number = 7): Promise<ChartData[]> {
    return this.request<ChartData[]>(`/analytics/mishandling-by-cause?days=${days}`)
  }

  async getHandlerPerformance(): Promise<ChartData[]> {
    return this.request<ChartData[]>('/analytics/handler-performance')
  }

  async exportReport(
    reportType: 'bags' | 'flights' | 'mishandled' | 'analytics',
    format: 'csv' | 'pdf',
    filters?: any
  ): Promise<Blob> {
    const params = new URLSearchParams({ format, ...filters })
    const response = await fetch(`${this.baseURL}/analytics/export/${reportType}?${params}`, {
      headers: this.apiKey ? { 'X-API-Key': this.apiKey } : {},
    })

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`)
    }

    return response.blob()
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health')
  }
}

export const apiClient = new APIClient()
export default apiClient

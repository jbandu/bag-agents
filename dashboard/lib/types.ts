// Baggage Types
export type BagStatus = 'checked' | 'loaded' | 'in_transit' | 'transferred' | 'delivered' | 'delayed' | 'lost' | 'damaged'
export type BagRiskLevel = 'low' | 'medium' | 'high' | 'critical'

export interface Bag {
  id: string
  tag_number: string
  passenger_id: string
  passenger_name: string
  flight_id: string
  status: BagStatus
  risk_level: BagRiskLevel
  current_location: string
  destination: string
  weight: number
  checked_at: string
  last_scan_at: string
  position?: {
    x: number
    y: number
    z: number
  }
  connection_time_minutes?: number
  predicted_issues?: string[]
}

// Flight Types
export type FlightStatus = 'scheduled' | 'boarding' | 'departed' | 'arrived' | 'delayed' | 'cancelled'

export interface Flight {
  id: string
  flight_number: string
  airline: string
  departure_airport: string
  arrival_airport: string
  scheduled_departure: string
  actual_departure?: string
  scheduled_arrival: string
  status: FlightStatus
  gate?: string
  bags_checked: number
  bags_loaded: number
  bags_missing: number
  at_risk_connections: number
}

// Mishandled Bag Types
export type MishandledStatus = 'investigating' | 'located' | 'in_transit' | 'delivered' | 'compensated'
export type MishandledType = 'delayed' | 'lost' | 'damaged' | 'pilfered'

export interface MishandledBag {
  id: string
  bag_id: string
  bag_tag: string
  passenger_name: string
  passenger_contact: string
  type: MishandledType
  status: MishandledStatus
  reported_at: string
  resolved_at?: string
  assigned_handler?: string
  last_known_location?: string
  destination: string
  compensation_amount?: number
  notes?: string
}

// AI Agent Types
export type AgentType = 'prediction' | 'root_cause' | 'demand_forecast' | 'customer_service' | 'compensation' | 'infrastructure_health' | 'route_optimization'

export interface AgentInsight {
  agent_type: AgentType
  status: 'active' | 'idle' | 'error'
  last_run: string
  insights_count: number
  summary: string
}

export interface PredictionInsight {
  bag_id: string
  bag_tag: string
  flight_id: string
  risk_score: number
  risk_factors: string[]
  suggested_interventions: string[]
  confidence: number
}

export interface RootCauseInsight {
  cause: string
  frequency: number
  affected_bags: number
  recommendation: string
  trend: 'increasing' | 'stable' | 'decreasing'
}

export interface InfrastructureIssue {
  equipment_id: string
  equipment_type: string
  location: string
  issue: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  recommended_action: string
  estimated_cost?: number
}

export interface DemandForecast {
  timestamp: string
  predicted_volume: number
  confidence_interval: [number, number]
  recommended_staff: number
  peak_hours: string[]
}

// Approval Types
export type ApprovalType = 'compensation' | 'route_change' | 'flight_hold' | 'resource_allocation'
export type ApprovalStatus = 'pending' | 'approved' | 'denied'
export type ApprovalUrgency = 'low' | 'medium' | 'high' | 'critical'

export interface Approval {
  id: string
  type: ApprovalType
  urgency: ApprovalUrgency
  status: ApprovalStatus
  requested_by: string
  requested_at: string
  description: string
  estimated_value?: number
  additional_info: Record<string, any>
  reviewed_by?: string
  reviewed_at?: string
}

// Analytics Types
export interface KPIMetrics {
  mishandling_rate: number
  mishandling_rate_change: number
  on_time_delivery_rate: number
  on_time_delivery_change: number
  avg_resolution_time_hours: number
  resolution_time_change: number
  total_bags_today: number
  bags_at_risk: number
  active_incidents: number
}

export interface ChartData {
  date: string
  value: number
  category?: string
}

// WebSocket Event Types
export interface WSBagUpdate {
  type: 'bag_update'
  data: Bag
}

export interface WSFlightUpdate {
  type: 'flight_update'
  data: Flight
}

export interface WSAlert {
  type: 'alert'
  severity: 'info' | 'warning' | 'error' | 'critical'
  message: string
  bag_id?: string
  flight_id?: string
}

export type WSMessage = WSBagUpdate | WSFlightUpdate | WSAlert

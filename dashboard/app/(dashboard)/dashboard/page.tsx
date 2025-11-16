'use client'

import { useQuery } from '@tanstack/react-query'
import { KPICard } from '@/components/dashboard/kpi-card'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import apiClient from '@/lib/api-client'
import { Package, AlertTriangle, Clock, TrendingUp, Plane, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function DashboardPage() {
  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['kpis'],
    queryFn: () => apiClient.getKPIMetrics(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: predictions, isLoading: predictionsLoading } = useQuery({
    queryKey: ['predictions'],
    queryFn: () => apiClient.getPredictions(),
  })

  const { data: agentsStatus, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents-status'],
    queryFn: () => apiClient.getAgentsStatus(),
  })

  const { data: approvals, isLoading: approvalsLoading } = useQuery({
    queryKey: ['approvals', 'pending'],
    queryFn: () => apiClient.getApprovals({ status: 'pending' }),
  })

  const pendingApprovals = approvals?.filter((a) => a.status === 'pending').length || 0

  if (kpisLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Operations Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time visibility into baggage operations
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/bags">
            <Button>Track Bag</Button>
          </Link>
          <Link href="/approvals">
            <Button variant="outline">
              Approvals {pendingApprovals > 0 && `(${pendingApprovals})`}
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Mishandling Rate"
          value={`${kpis?.mishandling_rate.toFixed(2)}%` || '0%'}
          change={kpis?.mishandling_rate_change}
          trend={kpis?.mishandling_rate_change && kpis.mishandling_rate_change > 0 ? 'down' : 'up'}
          icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
          description="vs last week"
        />
        <KPICard
          title="On-Time Delivery"
          value={`${kpis?.on_time_delivery_rate.toFixed(1)}%` || '0%'}
          change={kpis?.on_time_delivery_change}
          trend={kpis?.on_time_delivery_change && kpis.on_time_delivery_change > 0 ? 'up' : 'down'}
          icon={<CheckCircle2 className="h-4 w-4 text-muted-foreground" />}
          description="vs last week"
        />
        <KPICard
          title="Avg Resolution Time"
          value={`${kpis?.avg_resolution_time_hours.toFixed(1)}h` || '0h'}
          change={kpis?.resolution_time_change}
          trend={kpis?.resolution_time_change && kpis.resolution_time_change > 0 ? 'down' : 'up'}
          icon={<Clock className="h-4 w-4 text-muted-foreground" />}
          description="vs last week"
        />
        <KPICard
          title="Total Bags Today"
          value={kpis?.total_bags_today.toLocaleString() || '0'}
          icon={<Package className="h-4 w-4 text-muted-foreground" />}
          description={`${kpis?.bags_at_risk || 0} at risk`}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* At-Risk Bags */}
        <Card>
          <CardHeader>
            <CardTitle>At-Risk Bags</CardTitle>
            <CardDescription>
              Bags predicted to have issues - AI-powered predictions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {predictionsLoading ? (
                <p className="text-sm text-muted-foreground">Loading predictions...</p>
              ) : predictions && predictions.length > 0 ? (
                predictions.slice(0, 5).map((prediction) => (
                  <div
                    key={prediction.bag_id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{prediction.bag_tag}</p>
                        <Badge
                          variant={
                            prediction.risk_score > 0.8
                              ? 'destructive'
                              : prediction.risk_score > 0.6
                              ? 'warning'
                              : 'secondary'
                          }
                        >
                          Risk: {(prediction.risk_score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {prediction.risk_factors.slice(0, 2).join(', ')}
                      </p>
                    </div>
                    <Link href={`/bags/${prediction.bag_id}`}>
                      <Button size="sm" variant="ghost">View</Button>
                    </Link>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No at-risk bags found</p>
              )}
            </div>
            <Link href="/agents" className="mt-4 block">
              <Button variant="outline" size="sm" className="w-full">
                View All Predictions
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* AI Agents Status */}
        <Card>
          <CardHeader>
            <CardTitle>AI Agents Status</CardTitle>
            <CardDescription>Real-time agent monitoring</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {agentsLoading ? (
                <p className="text-sm text-muted-foreground">Loading agents...</p>
              ) : agentsStatus && agentsStatus.length > 0 ? (
                agentsStatus.slice(0, 6).map((agent) => (
                  <div
                    key={agent.agent_type}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium capitalize">
                          {agent.agent_type.replace('_', ' ')}
                        </p>
                        <Badge
                          variant={
                            agent.status === 'active'
                              ? 'success'
                              : agent.status === 'error'
                              ? 'destructive'
                              : 'secondary'
                          }
                        >
                          {agent.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {agent.insights_count} insights
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No agents data available</p>
              )}
            </div>
            <Link href="/agents" className="mt-4 block">
              <Button variant="outline" size="sm" className="w-full">
                View All Agents
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Active Incidents */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Incidents</CardTitle>
              <CardDescription>
                {kpis?.active_incidents || 0} incidents requiring attention
              </CardDescription>
            </div>
            <Link href="/mishandled">
              <Button variant="outline" size="sm">View All</Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Connect to backend API to view active incidents</p>
            <p className="text-sm mt-1">
              Configure NEXT_PUBLIC_API_BASE_URL in .env.local
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

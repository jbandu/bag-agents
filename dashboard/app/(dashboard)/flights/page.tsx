'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import apiClient from '@/lib/api-client'
import { Plane, Package, AlertTriangle, Clock, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'

export default function FlightsPage() {
  const { data: flights, isLoading, refetch } = useQuery({
    queryKey: ['flights', 'active'],
    queryFn: () => apiClient.getFlights({ hours_ahead: 6 }),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'warning' | 'success'> = {
      scheduled: 'secondary',
      boarding: 'info',
      departed: 'success',
      arrived: 'default',
      delayed: 'warning',
      cancelled: 'destructive',
    }

    return (
      <Badge variant={variants[status] || 'default'}>
        {status.toUpperCase()}
      </Badge>
    )
  }

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-sm text-muted-foreground">Loading flights...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Flight Operations</h1>
          <p className="text-muted-foreground">
            Active flights departing in the next 6 hours
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => refetch()} variant="outline">
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Active Flights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold">{flights?.length || 0}</span>
              <Plane className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Bags</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold">
                {flights?.reduce((sum, f) => sum + f.bags_checked, 0) || 0}
              </span>
              <Package className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">At-Risk Connections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-yellow-600 dark:text-yellow-500">
                {flights?.reduce((sum, f) => sum + f.at_risk_connections, 0) || 0}
              </span>
              <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Flights List */}
      <Card>
        <CardHeader>
          <CardTitle>Active Flights</CardTitle>
          <CardDescription>
            Departing flights and their baggage status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {flights && flights.length > 0 ? (
            <div className="space-y-4">
              {flights.map((flight) => (
                <div
                  key={flight.id}
                  className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <Plane className="h-5 w-5 text-primary" />
                        <span className="text-lg font-semibold">{flight.flight_number}</span>
                      </div>
                      {getStatusBadge(flight.status)}
                      {flight.status === 'delayed' && (
                        <Badge variant="warning">
                          <Clock className="h-3 w-3 mr-1" />
                          Delayed
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{flight.departure_airport}</span>
                        <ArrowRight className="h-3 w-3" />
                        <span className="font-medium">{flight.arrival_airport}</span>
                      </div>
                      <span>•</span>
                      <span>{flight.airline}</span>
                      {flight.gate && (
                        <>
                          <span>•</span>
                          <span>Gate {flight.gate}</span>
                        </>
                      )}
                      <span>•</span>
                      <span>
                        Departs{' '}
                        {formatDistanceToNow(new Date(flight.scheduled_departure), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>

                    <div className="flex items-center gap-6 text-sm">
                      <div className="flex items-center gap-2">
                        <Package className="h-4 w-4" />
                        <span className="font-medium">{flight.bags_checked}</span>
                        <span className="text-muted-foreground">checked</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-green-600 dark:text-green-500">
                          {flight.bags_loaded}
                        </span>
                        <span className="text-muted-foreground">loaded</span>
                      </div>
                      {flight.bags_missing > 0 && (
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-500" />
                          <span className="font-medium text-red-600 dark:text-red-500">
                            {flight.bags_missing}
                          </span>
                          <span className="text-muted-foreground">missing</span>
                        </div>
                      )}
                      {flight.at_risk_connections > 0 && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-yellow-600 dark:text-yellow-500" />
                          <span className="font-medium text-yellow-600 dark:text-yellow-500">
                            {flight.at_risk_connections}
                          </span>
                          <span className="text-muted-foreground">at-risk connections</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Link href={`/flights/${flight.id}`}>
                      <Button size="sm" variant="outline">
                        View Details
                      </Button>
                    </Link>
                    {flight.bags_missing > 0 && (
                      <Button size="sm" variant="destructive">
                        Expedite
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Plane className="h-12 w-12 mx-auto mb-4 opacity-50 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No Active Flights</h3>
              <p className="text-muted-foreground">
                Connect to backend API to view flight operations
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Configure NEXT_PUBLIC_API_BASE_URL in .env.local
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import apiClient from '@/lib/api-client'
import { AlertTriangle, Clock, MapPin, User, CheckCircle2, Package } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { toast } from 'sonner'
import { useState } from 'react'

export default function MishandledPage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<string>('all')

  const { data: bags, isLoading } = useQuery({
    queryKey: ['mishandled-bags', filter],
    queryFn: () =>
      apiClient.getMishandledBags(
        filter !== 'all' ? { status: filter } : undefined
      ),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  const assignHandlerMutation = useMutation({
    mutationFn: ({ bagId, handlerId }: { bagId: string; handlerId: string }) =>
      apiClient.assignHandler(bagId, handlerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mishandled-bags'] })
      toast.success('Handler assigned successfully')
    },
    onError: () => {
      toast.error('Failed to assign handler')
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) =>
      apiClient.updateMishandledBag(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mishandled-bags'] })
      toast.success('Status updated successfully')
    },
    onError: () => {
      toast.error('Failed to update status')
    },
  })

  const getTypeBadge = (type: string) => {
    const variants: Record<string, 'default' | 'destructive' | 'warning' | 'info'> = {
      delayed: 'warning',
      lost: 'destructive',
      damaged: 'destructive',
      pilfered: 'destructive',
    }

    return <Badge variant={variants[type] || 'default'}>{type.toUpperCase()}</Badge>
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'success' | 'info'> = {
      investigating: 'secondary',
      located: 'info',
      in_transit: 'info',
      delivered: 'success',
      compensated: 'default',
    }

    return (
      <Badge variant={variants[status] || 'default'}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    )
  }

  const getPriorityColor = (reportedAt: string) => {
    const hoursAgo = (Date.now() - new Date(reportedAt).getTime()) / (1000 * 60 * 60)

    if (hoursAgo > 24) return 'text-red-600 dark:text-red-500'
    if (hoursAgo > 12) return 'text-yellow-600 dark:text-yellow-500'
    return 'text-muted-foreground'
  }

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-sm text-muted-foreground">Loading mishandled bags...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mishandled Bags</h1>
          <p className="text-muted-foreground">
            Track and manage delayed, lost, and damaged baggage
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-sm">
            Auto-refresh: 30s
          </Badge>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['all', 'investigating', 'located', 'in_transit', 'delivered'].map((status) => (
          <Button
            key={status}
            variant={filter === status ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(status)}
          >
            {status.replace('_', ' ').charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
          </Button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{bags?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Investigating</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-500">
              {bags?.filter((b) => b.status === 'investigating').length || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">In Transit</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-500">
              {bags?.filter((b) => b.status === 'in_transit').length || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600 dark:text-green-500">
              {bags?.filter((b) => b.status === 'delivered' || b.status === 'compensated').length || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Mishandled Bags Table */}
      <Card>
        <CardHeader>
          <CardTitle>Active Cases</CardTitle>
          <CardDescription>
            Cases requiring attention - sorted by priority
          </CardDescription>
        </CardHeader>
        <CardContent>
          {bags && bags.length > 0 ? (
            <div className="space-y-3">
              {bags.map((bag) => (
                <div
                  key={bag.id}
                  className="rounded-lg border p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-center gap-3">
                        <Package className="h-5 w-5 text-primary" />
                        <span className="text-lg font-semibold">{bag.bag_tag}</span>
                        {getTypeBadge(bag.type)}
                        {getStatusBadge(bag.status)}
                      </div>

                      <div className="grid gap-2 text-sm">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{bag.passenger_name}</span>
                          <span className="text-muted-foreground">•</span>
                          <span className="text-muted-foreground">{bag.passenger_contact}</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-muted-foreground" />
                          {bag.last_known_location && (
                            <span className="text-muted-foreground">
                              Last seen: {bag.last_known_location}
                            </span>
                          )}
                          <span className="text-muted-foreground">→</span>
                          <span className="font-medium">Destination: {bag.destination}</span>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <Clock className={`h-4 w-4 ${getPriorityColor(bag.reported_at)}`} />
                            <span className={getPriorityColor(bag.reported_at)}>
                              Reported{' '}
                              {formatDistanceToNow(new Date(bag.reported_at), {
                                addSuffix: true,
                              })}
                            </span>
                          </div>

                          {bag.assigned_handler && (
                            <>
                              <span className="text-muted-foreground">•</span>
                              <div className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                <span className="text-muted-foreground">
                                  Handler: {bag.assigned_handler}
                                </span>
                              </div>
                            </>
                          )}

                          {bag.compensation_amount && (
                            <>
                              <span className="text-muted-foreground">•</span>
                              <span className="text-muted-foreground">
                                Compensation: ${bag.compensation_amount}
                              </span>
                            </>
                          )}
                        </div>

                        {bag.notes && (
                          <p className="text-sm text-muted-foreground italic">
                            Note: {bag.notes}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col gap-2">
                      {bag.status === 'investigating' && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              updateStatusMutation.mutate({
                                id: bag.id,
                                updates: { status: 'located' },
                              })
                            }
                          >
                            <MapPin className="h-3 w-3 mr-1" />
                            Mark Located
                          </Button>
                          {!bag.assigned_handler && (
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() =>
                                assignHandlerMutation.mutate({
                                  bagId: bag.id,
                                  handlerId: 'current-user',
                                })
                              }
                            >
                              Assign to Me
                            </Button>
                          )}
                        </>
                      )}
                      {bag.status === 'located' && (
                        <Button
                          size="sm"
                          onClick={() =>
                            updateStatusMutation.mutate({
                              id: bag.id,
                              updates: { status: 'in_transit' },
                            })
                          }
                        >
                          Start Delivery
                        </Button>
                      )}
                      {bag.status === 'in_transit' && (
                        <Button
                          size="sm"
                          variant="default"
                          onClick={() =>
                            updateStatusMutation.mutate({
                              id: bag.id,
                              updates: { status: 'delivered', resolved_at: new Date().toISOString() },
                            })
                          }
                        >
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Mark Delivered
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        View Details
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No Mishandled Bags</h3>
              <p className="text-muted-foreground">
                {filter === 'all'
                  ? 'Connect to backend API to view mishandled bags'
                  : `No bags with status: ${filter}`}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

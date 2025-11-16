import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { ArrowUp, ArrowDown, Minus } from 'lucide-react'

interface KPICardProps {
  title: string
  value: string | number
  change?: number
  icon?: React.ReactNode
  description?: string
  trend?: 'up' | 'down' | 'neutral'
}

export function KPICard({ title, value, change, icon, description, trend }: KPICardProps) {
  const getTrendColor = () => {
    if (!change) return 'text-muted-foreground'
    if (trend === 'up') return 'text-green-600 dark:text-green-500'
    if (trend === 'down') return 'text-red-600 dark:text-red-500'
    return 'text-muted-foreground'
  }

  const getTrendIcon = () => {
    if (!change) return null
    if (trend === 'up') return <ArrowUp className="h-4 w-4" />
    if (trend === 'down') return <ArrowDown className="h-4 w-4" />
    return <Minus className="h-4 w-4" />
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {(change !== undefined || description) && (
          <div className="flex items-center gap-1 text-xs">
            {change !== undefined && (
              <span className={cn('flex items-center gap-1 font-medium', getTrendColor())}>
                {getTrendIcon()}
                {Math.abs(change)}%
              </span>
            )}
            {description && (
              <span className="text-muted-foreground">{description}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

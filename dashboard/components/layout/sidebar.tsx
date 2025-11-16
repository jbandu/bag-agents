'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Plane,
  Package,
  AlertTriangle,
  Bot,
  CheckSquare,
  BarChart3,
  Settings,
  Moon,
  Sun,
} from 'lucide-react'
import { useTheme } from '@/providers/theme-provider'
import { Button } from '@/components/ui/button'

const routes = [
  {
    label: 'Dashboard',
    icon: LayoutDashboard,
    href: '/dashboard',
  },
  {
    label: 'Flights',
    icon: Plane,
    href: '/flights',
  },
  {
    label: 'Bags',
    icon: Package,
    href: '/bags',
  },
  {
    label: 'Mishandled',
    icon: AlertTriangle,
    href: '/mishandled',
  },
  {
    label: 'AI Agents',
    icon: Bot,
    href: '/agents',
  },
  {
    label: 'Approvals',
    icon: CheckSquare,
    href: '/approvals',
  },
  {
    label: 'Analytics',
    icon: BarChart3,
    href: '/analytics',
  },
  {
    label: 'Settings',
    icon: Settings,
    href: '/settings',
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex h-full flex-col gap-2 bg-card border-r">
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
          <Package className="h-6 w-6" />
          <span>Baggage Ops</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-2">
        {routes.map((route) => {
          const Icon = route.icon
          const isActive = pathname === route.href || pathname.startsWith(route.href + '/')

          return (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <Icon className="h-4 w-4" />
              {route.label}
            </Link>
          )
        })}
      </nav>
      <div className="border-t p-3">
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-start gap-2"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        >
          {theme === 'dark' ? (
            <>
              <Sun className="h-4 w-4" />
              Light Mode
            </>
          ) : (
            <>
              <Moon className="h-4 w-4" />
              Dark Mode
            </>
          )}
        </Button>
      </div>
    </div>
  )
}

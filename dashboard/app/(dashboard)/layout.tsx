import { Sidebar } from '@/components/layout/sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-64 flex-shrink-0">
        <Sidebar />
      </aside>
      <main className="flex-1 overflow-y-auto bg-background">
        <div className="container mx-auto p-6">
          {children}
        </div>
      </main>
    </div>
  )
}

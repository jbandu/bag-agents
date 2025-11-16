import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type User = {
  id: string
  email: string
  role: 'admin' | 'operator' | 'handler' | 'viewer'
  firstName?: string
  lastName?: string
  airport?: string
}

export async function getCurrentUser(): Promise<User | null> {
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return null

  return {
    id: user.id,
    email: user.email || '',
    role: (user.user_metadata?.role as User['role']) || 'viewer',
    firstName: user.user_metadata?.first_name,
    lastName: user.user_metadata?.last_name,
    airport: user.user_metadata?.airport,
  }
}

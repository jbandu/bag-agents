# Baggage Operations Dashboard

A unified real-time operations dashboard for monitoring and managing baggage operations across the entire airport system.

## Features

### ✅ Implemented

1. **Main Dashboard** (`/dashboard`)
   - Real-time KPIs (mishandling rate, on-time delivery, resolution time)
   - At-risk bags prediction display
   - AI agents status monitoring
   - Active incidents overview
   - Auto-refresh every 30 seconds

2. **Flight Operations** (`/flights`)
   - Active flights departing in next 6 hours
   - Bag counts per flight (checked, loaded, missing)
   - Connection bags with risk scores
   - Flight status tracking
   - Quick actions for flight management

3. **Mishandled Bags Dashboard** (`/mishandled`)
   - Table of all delayed/lost/damaged bags
   - Status filtering and management
   - Handler assignment
   - Auto-refresh every 30 seconds
   - Quick actions for status updates

4. **Core Infrastructure**
   - Next.js 14 with App Router
   - TypeScript throughout
   - shadcn/ui components
   - React Query for data fetching
   - Dark mode support
   - Responsive design
   - Real-time data updates

### 🚧 Planned (Ready for Implementation)

5. **Real-Time Bag Tracking Map** (`/bags`)
6. **AI Agent Insights** (`/agents`)
7. **Pending Approvals** (`/approvals`)
8. **Analytics Dashboard** (`/analytics`)
9. **Handler Mobile View**

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: React Query
- **Real-time**: Socket.io client
- **Authentication**: Supabase Auth

## Getting Started

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment variables:
   ```bash
   cp .env.local .env.local
   ```

   Edit `.env.local`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
   NEXT_PUBLIC_MAPBOX_TOKEN=your-mapbox-token
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000)

### Running with Backend

Make sure the backend API is running:

```bash
# In parent directory
docker-compose up -d
```

## Deployment

### Vercel

```bash
vercel
```

Set environment variables in Vercel dashboard.

## Project Structure

```
dashboard/
├── app/                    # Next.js App Router pages
├── components/            # React components
├── lib/                   # API clients, types, utilities
├── providers/             # React context providers
└── hooks/                 # Custom React hooks
```

## License

MIT

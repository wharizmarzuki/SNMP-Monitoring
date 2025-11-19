# SNMP Monitoring System - Frontend

A modern, responsive dashboard for monitoring network devices via SNMP protocol. Built with Next.js 14, React, TypeScript, and Tailwind CSS.

## Features

### Pages

1. **Dashboard** (`/dashboard`)
   - Network summary with KPI cards (Total Devices, Devices Up, Devices in Alert)
   - Active alerts table
   - Top 5 CPU and Memory utilization charts
   - Network throughput time-series chart

2. **Devices** (`/devices`)
   - List view of all monitored devices
   - Device detail view with:
     - Device information card
     - CPU and Memory utilization charts
     - Network interfaces table

3. **Alerts** (`/alerts`)
   - Active alerts table with severity indicators
   - Acknowledge functionality for alerts

4. **Reports** (`/report`)
   - Report builder with device and date range selection
   - Historical metrics table
   - CSV export functionality

5. **Settings** (`/settings`)
   - Alert recipients management
   - Device CPU/Memory threshold configuration
   - Interface packet drop threshold settings
   - Network discovery trigger

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI)
- **Charts**: Recharts
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Date Formatting**: date-fns

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running (see backend documentation)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env.local
   ```

4. Update the API URL in `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. Run the development server:
   ```bash
   npm run dev
   ```

6. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── dashboard/         # Dashboard page
│   ├── devices/           # Devices list and detail pages
│   ├── alerts/            # Alerts page
│   ├── report/            # Report page
│   ├── settings/          # Settings page
│   ├── layout.tsx         # Root layout with Navbar
│   └── page.tsx           # Home page (redirects to dashboard)
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── KpiCard.tsx       # KPI card component
│   └── StatusBadge.tsx   # Status indicator components
├── lib/                   # Utility libraries
│   ├── api.ts            # API client and endpoints
│   └── utils.ts          # Utility functions
├── providers/            # React providers
│   └── QueryProvider.tsx # React Query provider
└── types/                # TypeScript type definitions
    └── index.ts          # Shared types
```

## API Endpoints

The frontend expects the following backend API endpoints:

### Devices
- `GET /device/` - Get all devices
- `GET /device/{ip}` - Get device by IP
- `GET /device/discover` - Trigger network discovery

### Configuration
- `GET /config/recipients/` - Get alert recipients
- `POST /config/recipients/` - Add alert recipient
- `DELETE /config/recipients/{email}` - Remove recipient
- `PUT /device/{ip}/threshold/cpu` - Update CPU threshold
- `PUT /device/{ip}/threshold/memory` - Update memory threshold
- `PUT /device/{ip}/interface/{if_index}/threshold` - Update interface threshold

### Queries
- `GET /query/network-summary` - Get network summary stats
- `GET /query/top-devices?metric={cpu|memory}` - Get top devices by metric
- `GET /query/device/{ip}/metrics` - Get device time-series metrics
- `GET /query/device/{ip}/interfaces` - Get device interfaces
- `GET /query/history/device?ip=...&start=...&end=...` - Get historical data
- `GET /query/alerts/active` - Get active alerts
- `GET /query/network-throughput` - Get network throughput data

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API base URL (default: http://localhost:8000)

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## License

ISC

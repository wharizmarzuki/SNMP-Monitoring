# Comprehensive Network Report - Implementation Plan

## Overview
Transform the report page from a single-device historical view into a comprehensive network-wide report that provides deep insights into network health and performance over a specified time period.

## Report Requirements

### Metrics to Include
1. **Packet Drop Rate** - Network-wide and per-device packet discards
2. **CPU and Memory Report** - Utilization trends across all devices
3. **Device Bandwidth** - Throughput and utilization metrics
4. **System Uptime** - Device availability and uptime tracking
5. **Device Availability** - Reachability percentage over time period

### Scope
- **Network-wide** (not device-specific)
- **Date range based** (user selects start/end dates)
- **Comprehensive visualizations** (charts, graphs, summary tables)
- **Exportable** (PDF and CSV formats)

---

## UI/UX Design

### Page Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Network Report                                    [Export ▼]│
├─────────────────────────────────────────────────────────────┤
│ Report Configuration Card                                   │
│  [Start Date] [End Date] [Generate Report]                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Executive Summary                                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│  │Avg CPU │ │Avg Mem │ │Uptime %│ │Alerts  │              │
│  └────────┘ └────────┘ └────────┘ └────────┘              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Network Performance Overview                                │
│  [Line Chart: Network-wide Throughput over Time]            │
│  - Inbound/Outbound bandwidth trends                        │
└─────────────────────────────────────────────────────────────┘

┌───────────────────────────┬─────────────────────────────────┐
│ Device Utilization        │ Packet Drop Analysis            │
│  [Area Chart: CPU/Memory] │  [Bar Chart: Discard Rates]     │
└───────────────────────────┴─────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Device Availability Report                                  │
│  [Table with Availability %, Uptime, Downtime]              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Top Issues                                                  │
│  • Devices with most alerts                                 │
│  • Interfaces with highest error rates                      │
│  • Bandwidth utilization leaders                            │
└─────────────────────────────────────────────────────────────┘
```

### Color Scheme
- **Green**: Healthy metrics, good performance
- **Yellow/Orange**: Warning thresholds, moderate issues
- **Red**: Critical issues, high utilization
- **Blue**: Informational, neutral metrics

---

## Backend Implementation

### New API Endpoints

#### 1. `/query/report/summary` (GET)
**Purpose**: Executive summary metrics for date range

**Query Parameters**:
- `start_date`: ISO datetime
- `end_date`: ISO datetime

**Response**:
```typescript
{
  period: {
    start: string,
    end: string,
    duration_hours: number
  },
  summary: {
    avg_cpu_utilization: number,
    avg_memory_utilization: number,
    network_availability_pct: number,
    total_alerts: number,
    total_devices: number,
    devices_up: number,
    devices_down: number
  }
}
```

**SQL Logic**:
```sql
-- Average CPU/Memory across all devices in period
SELECT
  AVG(cpu_utilization) as avg_cpu,
  AVG(memory_utilization) as avg_memory
FROM device_metrics
WHERE timestamp >= start_date AND timestamp <= end_date

-- Availability calculation
SELECT
  COUNT(CASE WHEN is_reachable = true THEN 1 END) * 100.0 / COUNT(*) as availability_pct
FROM device_metrics
JOIN devices ON device_metrics.device_id = devices.id
WHERE timestamp >= start_date AND timestamp <= end_date
```

---

#### 2. `/query/report/network-throughput` (GET)
**Purpose**: Time series of network-wide throughput

**Query Parameters**:
- `start_date`: ISO datetime
- `end_date`: ISO datetime
- `interval`: Optional (1h, 6h, 24h) - aggregation bucket

**Response**:
```typescript
[
  {
    timestamp: string,
    total_inbound_bps: number,
    total_outbound_bps: number,
    avg_utilization_pct: number
  }
]
```

**SQL Logic**:
```sql
-- Sum throughput across all interfaces, group by time bucket
SELECT
  time_bucket(interval, timestamp) as bucket,
  SUM(inbound_bps) as total_inbound,
  SUM(outbound_bps) as total_outbound,
  AVG(utilization_pct) as avg_utilization
FROM interface_metrics
JOIN interfaces ON interface_metrics.interface_id = interfaces.id
WHERE timestamp >= start_date AND timestamp <= end_date
GROUP BY bucket
ORDER BY bucket ASC
```

---

#### 3. `/query/report/device-utilization` (GET)
**Purpose**: CPU/Memory trends over time period

**Query Parameters**:
- `start_date`: ISO datetime
- `end_date`: ISO datetime

**Response**:
```typescript
[
  {
    timestamp: string,
    avg_cpu_utilization: number,
    avg_memory_utilization: number,
    max_cpu_utilization: number,
    max_memory_utilization: number,
    devices_sampled: number
  }
]
```

**SQL Logic**:
```sql
SELECT
  timestamp,
  AVG(cpu_utilization) as avg_cpu,
  AVG(memory_utilization) as avg_memory,
  MAX(cpu_utilization) as max_cpu,
  MAX(memory_utilization) as max_memory,
  COUNT(DISTINCT device_id) as devices_sampled
FROM device_metrics
WHERE timestamp >= start_date AND timestamp <= end_date
GROUP BY timestamp
ORDER BY timestamp ASC
```

---

#### 4. `/query/report/packet-drops` (GET)
**Purpose**: Packet discard rates by device/interface

**Query Parameters**:
- `start_date`: ISO datetime
- `end_date`: ISO datetime

**Response**:
```typescript
[
  {
    device_hostname: string,
    device_ip: string,
    interface_name: string,
    total_discards_in: number,
    total_discards_out: number,
    discard_rate_pct: number, // (discards / octets) * 100
    total_errors_in: number,
    total_errors_out: number
  }
]
```

**SQL Logic**:
```sql
SELECT
  d.hostname,
  d.ip_address,
  i.name as interface_name,
  SUM(im.discards_in) as total_discards_in,
  SUM(im.discards_out) as total_discards_out,
  SUM(im.errors_in) as total_errors_in,
  SUM(im.errors_out) as total_errors_out,
  (SUM(im.discards_in + im.discards_out) * 100.0 /
   NULLIF(SUM(im.octets_in + im.octets_out), 0)) as discard_rate_pct
FROM interface_metrics im
JOIN interfaces i ON im.interface_id = i.id
JOIN devices d ON i.device_id = d.id
WHERE im.timestamp >= start_date AND im.timestamp <= end_date
GROUP BY d.id, i.id
HAVING SUM(im.discards_in + im.discards_out) > 0
ORDER BY discard_rate_pct DESC
LIMIT 20
```

---

#### 5. `/query/report/availability` (GET)
**Purpose**: Device availability metrics for period

**Query Parameters**:
- `start_date`: ISO datetime
- `end_date`: ISO datetime

**Response**:
```typescript
[
  {
    device_hostname: string,
    device_ip: string,
    availability_pct: number,
    total_uptime_seconds: number,
    total_downtime_seconds: number,
    avg_uptime_seconds: number, // from sysUptime
    poll_success_count: number,
    poll_failure_count: number,
    last_seen: string
  }
]
```

**SQL Logic**:
```sql
-- Calculate availability based on reachability polls
SELECT
  d.hostname,
  d.ip_address,
  (COUNT(CASE WHEN d.is_reachable = true THEN 1 END) * 100.0 / COUNT(*)) as availability_pct,
  AVG(dm.uptime) as avg_uptime,
  COUNT(*) as total_polls,
  COUNT(CASE WHEN d.is_reachable = true THEN 1 END) as success_count,
  COUNT(CASE WHEN d.is_reachable = false THEN 1 END) as failure_count,
  MAX(dm.timestamp) as last_seen
FROM device_metrics dm
JOIN devices d ON dm.device_id = d.id
WHERE dm.timestamp >= start_date AND dm.timestamp <= end_date
GROUP BY d.id
ORDER BY availability_pct ASC
```

---

#### 6. `/query/report/top-issues` (GET)
**Purpose**: Identify devices/interfaces with most problems

**Query Parameters**:
- `start_date`: ISO datetime
- `end_date`: ISO datetime

**Response**:
```typescript
{
  top_cpu_devices: Array<{hostname, ip, avg_cpu, max_cpu}>,
  top_memory_devices: Array<{hostname, ip, avg_mem, max_mem}>,
  most_errors: Array<{device, interface, error_count}>,
  highest_utilization: Array<{device, interface, avg_utilization_pct}>,
  least_available: Array<{hostname, ip, availability_pct}>
}
```

---

## Frontend Implementation

### Component Hierarchy
```
ReportPage
├── ReportConfigCard
│   ├── DateRangePicker (start/end date inputs)
│   └── GenerateButton
├── ExecutiveSummaryCard
│   ├── MetricCard (avg CPU)
│   ├── MetricCard (avg Memory)
│   ├── MetricCard (availability %)
│   └── MetricCard (total alerts)
├── NetworkThroughputChart
│   └── LineChart (Recharts)
├── DeviceUtilizationChart
│   └── AreaChart (Recharts)
├── PacketDropAnalysisCard
│   └── BarChart (Recharts)
├── AvailabilityTable
│   └── DataTable (shadcn/ui)
├── TopIssuesCard
│   ├── TopDevicesList
│   └── TopInterfacesList
└── ExportButton
    ├── Export PDF
    └── Export CSV
```

### State Management
```typescript
// Report page state
const [startDate, setStartDate] = useState<string>('');
const [endDate, setEndDate] = useState<string>('');
const [reportGenerated, setReportGenerated] = useState(false);

// Data queries (React Query)
const { data: summary } = useQuery(['reportSummary', startDate, endDate], ...);
const { data: throughput } = useQuery(['reportThroughput', startDate, endDate], ...);
const { data: utilization } = useQuery(['reportUtilization', startDate, endDate], ...);
const { data: packetDrops } = useQuery(['reportPacketDrops', startDate, endDate], ...);
const { data: availability } = useQuery(['reportAvailability', startDate, endDate], ...);
const { data: topIssues } = useQuery(['reportTopIssues', startDate, endDate], ...);
```

### Charts to Implement

#### 1. Network Throughput Chart (Line Chart)
- **X-axis**: Time
- **Y-axis**: Throughput (bps)
- **Lines**: Inbound (blue), Outbound (green)
- **Tooltip**: Shows exact values at time point
- **Library**: Recharts `<LineChart>`

#### 2. Device Utilization Chart (Area Chart)
- **X-axis**: Time
- **Y-axis**: Utilization %
- **Areas**: CPU (red/orange gradient), Memory (blue gradient)
- **Legend**: Shows avg/max values
- **Library**: Recharts `<AreaChart>`

#### 3. Packet Drop Analysis (Bar Chart)
- **X-axis**: Device names
- **Y-axis**: Discard rate %
- **Bars**: Sorted by highest discard rate
- **Colors**: Gradient based on severity (green → yellow → red)
- **Library**: Recharts `<BarChart>`

#### 4. Availability Table (Data Table)
- **Columns**: Device, IP, Availability %, Uptime, Downtime, Last Seen
- **Sortable**: By any column
- **Filterable**: Search by device name
- **Color coding**: Red (<95%), Yellow (95-99%), Green (>99%)
- **Library**: shadcn/ui `<Table>` with sorting

---

## API Layer Updates

### Add to `frontend/src/lib/api.ts`
```typescript
export const reportApi = {
  getSummary: async (start: string, end: string) => {
    const response = await api.get<ReportSummaryResponse>(
      `/query/report/summary`,
      { params: { start_date: start, end_date: end } }
    );
    return response.data;
  },

  getNetworkThroughput: async (start: string, end: string, interval?: string) => {
    const response = await api.get<NetworkThroughputDatapoint[]>(
      `/query/report/network-throughput`,
      { params: { start_date: start, end_date: end, interval } }
    );
    return response.data;
  },

  getDeviceUtilization: async (start: string, end: string) => {
    const response = await api.get<DeviceUtilizationDatapoint[]>(
      `/query/report/device-utilization`,
      { params: { start_date: start, end_date: end } }
    );
    return response.data;
  },

  getPacketDrops: async (start: string, end: string) => {
    const response = await api.get<PacketDropRecord[]>(
      `/query/report/packet-drops`,
      { params: { start_date: start, end_date: end } }
    );
    return response.data;
  },

  getAvailability: async (start: string, end: string) => {
    const response = await api.get<AvailabilityRecord[]>(
      `/query/report/availability`,
      { params: { start_date: start, end_date: end } }
    );
    return response.data;
  },

  getTopIssues: async (start: string, end: string) => {
    const response = await api.get<TopIssuesResponse>(
      `/query/report/top-issues`,
      { params: { start_date: start, end_date: end } }
    );
    return response.data;
  },
};
```

### TypeScript Types
```typescript
// frontend/src/types/report.ts
export interface ReportSummary {
  period: {
    start: string;
    end: string;
    duration_hours: number;
  };
  summary: {
    avg_cpu_utilization: number;
    avg_memory_utilization: number;
    network_availability_pct: number;
    total_alerts: number;
    total_devices: number;
    devices_up: number;
    devices_down: number;
  };
}

export interface NetworkThroughputDatapoint {
  timestamp: string;
  total_inbound_bps: number;
  total_outbound_bps: number;
  avg_utilization_pct: number;
}

export interface DeviceUtilizationDatapoint {
  timestamp: string;
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  max_cpu_utilization: number;
  max_memory_utilization: number;
  devices_sampled: number;
}

export interface PacketDropRecord {
  device_hostname: string;
  device_ip: string;
  interface_name: string;
  total_discards_in: number;
  total_discards_out: number;
  discard_rate_pct: number;
  total_errors_in: number;
  total_errors_out: number;
}

export interface AvailabilityRecord {
  device_hostname: string;
  device_ip: string;
  availability_pct: number;
  total_uptime_seconds: number;
  total_downtime_seconds: number;
  avg_uptime_seconds: number;
  poll_success_count: number;
  poll_failure_count: number;
  last_seen: string;
}

export interface TopIssuesResponse {
  top_cpu_devices: Array<{
    hostname: string;
    ip: string;
    avg_cpu: number;
    max_cpu: number;
  }>;
  top_memory_devices: Array<{
    hostname: string;
    ip: string;
    avg_mem: number;
    max_mem: number;
  }>;
  most_errors: Array<{
    device: string;
    interface: string;
    error_count: number;
  }>;
  highest_utilization: Array<{
    device: string;
    interface: string;
    avg_utilization_pct: number;
  }>;
  least_available: Array<{
    hostname: string;
    ip: string;
    availability_pct: number;
  }>;
}
```

---

## Export Functionality

### CSV Export
```typescript
const exportCSV = (data: any[], filename: string) => {
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row =>
      headers.map(h => {
        const val = row[h];
        return typeof val === 'string' && val.includes(',')
          ? `"${val}"`
          : val;
      }).join(',')
    )
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
};
```

### PDF Export
Use library: `jspdf` + `html2canvas`

```typescript
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const exportPDF = async () => {
  const reportElement = document.getElementById('network-report');
  if (!reportElement) return;

  const canvas = await html2canvas(reportElement);
  const imgData = canvas.toDataURL('image/png');

  const pdf = new jsPDF('p', 'mm', 'a4');
  const imgWidth = 210; // A4 width in mm
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
  pdf.save(`network-report-${format(new Date(), 'yyyy-MM-dd')}.pdf`);
};
```

---

## Implementation Phases

### Phase 1: Backend Foundation (Estimated: 4-6 hours)
1. Create database query functions in `backend/app/api/v1/endpoints/query.py`
2. Implement schemas in `backend/app/core/schemas.py`
3. Add all 6 new API endpoints
4. Test endpoints with manual curl/Postman requests
5. Verify SQL queries return correct data

### Phase 2: Frontend Data Layer (Estimated: 2-3 hours)
1. Add TypeScript types to `frontend/src/types/report.ts`
2. Create API functions in `frontend/src/lib/api.ts`
3. Update OpenAPI type generation if needed
4. Test API calls from frontend

### Phase 3: UI Components (Estimated: 6-8 hours)
1. Create report page layout structure
2. Build ExecutiveSummaryCard with metric KPIs
3. Implement NetworkThroughputChart (line chart)
4. Implement DeviceUtilizationChart (area chart)
5. Create PacketDropAnalysisCard (bar chart)
6. Build AvailabilityTable component
7. Create TopIssuesCard component

### Phase 4: Export & Polish (Estimated: 2-3 hours)
1. Implement CSV export for all sections
2. Implement PDF export functionality
3. Add loading states and error handling
4. Responsive design adjustments
5. Add tooltips and help text

### Phase 5: Testing & Validation (Estimated: 2-3 hours)
1. Test with real data from multiple time ranges
2. Verify calculations are accurate
3. Performance testing with large datasets
4. Browser compatibility testing
5. Export functionality validation

---

## Success Metrics

### Functional Requirements ✓
- [ ] Report shows network-wide metrics (not single device)
- [ ] Date range selector works correctly
- [ ] All 5 requested metrics are visualized:
  - [ ] Packet drop rate
  - [ ] CPU and memory report
  - [ ] Device bandwidth
  - [ ] System uptime
  - [ ] Device availability
- [ ] Charts are interactive and informative
- [ ] Data can be exported to CSV and PDF

### Performance Requirements
- API response time < 2 seconds for 7-day reports
- Frontend renders all charts in < 1 second
- Export functions complete in < 5 seconds

### User Experience
- Intuitive date selection
- Clear data visualization
- Helpful tooltips and legends
- Mobile-responsive design
- Accessible (WCAG 2.1 AA)

---

## Technical Considerations

### Data Volume Management
- Implement pagination for tables (max 100 rows)
- Add data aggregation intervals for long time ranges
- Cache report data on backend (5-minute TTL)
- Lazy load charts (generate on scroll)

### Error Handling
- Handle missing data gracefully (show "No data" message)
- Validate date ranges (end > start, not in future)
- Show loading spinners during data fetch
- Display user-friendly error messages

### Optimization
- Debounce date changes to avoid excessive API calls
- Use React Query for caching and background refetching
- Implement virtual scrolling for large tables
- Compress API responses (gzip)

---

## Future Enhancements (Post-MVP)

1. **Scheduled Reports**: Email reports daily/weekly
2. **Custom Metrics**: User-defined KPIs and thresholds
3. **Comparison Mode**: Compare two time periods side-by-side
4. **Alert Correlation**: Show alerts triggered during report period
5. **SLA Tracking**: Track and report on SLA compliance
6. **Forecasting**: Predict future utilization trends
7. **Anomaly Detection**: Highlight unusual patterns
8. **Multi-tenant**: Filter by device groups/locations

---

## Dependencies

### Backend
- SQLAlchemy (already installed)
- FastAPI (already installed)
- Pydantic (already installed)

### Frontend
- Recharts (install: `npm install recharts`)
- jsPDF (install: `npm install jspdf`)
- html2canvas (install: `npm install html2canvas`)
- date-fns (already installed)
- @tanstack/react-query (already installed)

---

## File Structure

```
backend/
└── app/
    ├── api/v1/endpoints/
    │   └── query.py (add report endpoints)
    └── core/
        └── schemas.py (add report schemas)

frontend/
└── src/
    ├── app/
    │   └── report/
    │       ├── page.tsx (redesign completely)
    │       └── components/
    │           ├── ExecutiveSummaryCard.tsx
    │           ├── NetworkThroughputChart.tsx
    │           ├── DeviceUtilizationChart.tsx
    │           ├── PacketDropAnalysisCard.tsx
    │           ├── AvailabilityTable.tsx
    │           └── TopIssuesCard.tsx
    ├── lib/
    │   └── api.ts (add reportApi)
    └── types/
        └── report.ts (new file with all types)
```

---

## Next Steps

To begin implementation, we should:
1. Review and approve this plan
2. Start with Phase 1 (Backend Foundation)
3. Create git branch: `feature/comprehensive-network-report`
4. Implement endpoints one at a time with tests
5. Move to frontend once backend is stable

**Estimated Total Time**: 16-23 hours of development + testing

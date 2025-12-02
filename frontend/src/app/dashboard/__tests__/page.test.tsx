/**
 * Component tests for Dashboard Page
 * Tests dashboard rendering with mocked API data
 */
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../page'
import * as api from '@/lib/api'

// Mock the API module
jest.mock('@/lib/api', () => ({
  queryApi: {
    getNetworkSummary: jest.fn(),
    getActiveAlerts: jest.fn(),
    getTopDevices: jest.fn(),
    getDeviceUtilization: jest.fn(),
  },
}))

describe('DashboardPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    // Create a new QueryClient for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })

    // Reset all mocks
    jest.clearAllMocks()
  })

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  it('displays loading skeletons initially', () => {
    // Mock API to delay response
    (api.queryApi.getNetworkSummary as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    )
    (api.queryApi.getActiveAlerts as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    )
    (api.queryApi.getTopDevices as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    )
    (api.queryApi.getDeviceUtilization as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    )

    renderWithProviders(<DashboardPage />)

    // Loading skeletons should be present
    // (The actual implementation may vary based on skeleton components)
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('displays network summary KPIs when data loads', async () => {
    // Mock successful API responses
    (api.queryApi.getNetworkSummary as jest.Mock).mockResolvedValue({
      total_devices: 10,
      devices_up: 8,
      devices_down: 2,
      devices_in_alert: 3,
    })
    (api.queryApi.getActiveAlerts as jest.Mock).mockResolvedValue([])
    (api.queryApi.getTopDevices as jest.Mock).mockResolvedValue([])
    (api.queryApi.getDeviceUtilization as jest.Mock).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    // Wait for data to load and KPIs to render
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument() // Total devices
    })

    expect(screen.getByText('8')).toBeInTheDocument() // Devices up
    expect(screen.getByText('2')).toBeInTheDocument() // Devices down
  })

  it('displays "Total Devices" label', async () => {
    (api.queryApi.getNetworkSummary as jest.Mock).mockResolvedValue({
      total_devices: 10,
      devices_up: 8,
      devices_down: 2,
      devices_in_alert: 3,
    })
    (api.queryApi.getActiveAlerts as jest.Mock).mockResolvedValue([])
    (api.queryApi.getTopDevices as jest.Mock).mockResolvedValue([])
    (api.queryApi.getDeviceUtilization as jest.Mock).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Total Devices')).toBeInTheDocument()
    })
  })

  it('displays devices status labels', async () => {
    (api.queryApi.getNetworkSummary as jest.Mock).mockResolvedValue({
      total_devices: 10,
      devices_up: 8,
      devices_down: 2,
      devices_in_alert: 3,
    })
    (api.queryApi.getActiveAlerts as jest.Mock).mockResolvedValue([])
    (api.queryApi.getTopDevices as jest.Mock).mockResolvedValue([])
    (api.queryApi.getDeviceUtilization as jest.Mock).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Devices Up')).toBeInTheDocument()
      expect(screen.getByText('Devices Down')).toBeInTheDocument()
    })
  })

  it('handles API error gracefully', async () => {
    // Mock API error
    (api.queryApi.getNetworkSummary as jest.Mock).mockRejectedValue(
      new Error('API Error')
    )
    (api.queryApi.getActiveAlerts as jest.Mock).mockResolvedValue([])
    (api.queryApi.getTopDevices as jest.Mock).mockResolvedValue([])
    (api.queryApi.getDeviceUtilization as jest.Mock).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    // Component should handle error without crashing
    // Error handling implementation may vary
    await waitFor(() => {
      expect(screen.queryByText('Total Devices')).toBeInTheDocument()
    }, { timeout: 2000 })
  })

  it('displays top CPU devices table', async () => {
    (api.queryApi.getNetworkSummary as jest.Mock).mockResolvedValue({
      total_devices: 10,
      devices_up: 8,
      devices_down: 2,
      devices_in_alert: 3,
    })
    (api.queryApi.getActiveAlerts as jest.Mock).mockResolvedValue([])
    (api.queryApi.getTopDevices as jest.Mock).mockResolvedValue([
      { hostname: 'router-1', ip_address: '192.168.1.1', value: 85.5 },
      { hostname: 'switch-1', ip_address: '192.168.1.2', value: 72.3 },
    ])
    (api.queryApi.getDeviceUtilization as jest.Mock).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('router-1')).toBeInTheDocument()
      expect(screen.getByText('switch-1')).toBeInTheDocument()
    })
  })

  it('displays active alerts count', async () => {
    (api.queryApi.getNetworkSummary as jest.Mock).mockResolvedValue({
      total_devices: 10,
      devices_up: 8,
      devices_down: 2,
      devices_in_alert: 3,
    })
    (api.queryApi.getActiveAlerts as jest.Mock).mockResolvedValue([
      { id: 1, device_ip: '192.168.1.1', alert_type: 'cpu', state: 'triggered' },
      { id: 2, device_ip: '192.168.1.2', alert_type: 'memory', state: 'triggered' },
    ])
    (api.queryApi.getTopDevices as jest.Mock).mockResolvedValue([])
    (api.queryApi.getDeviceUtilization as jest.Mock).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    await waitFor(() => {
      // Should display active alerts
      expect(screen.getByText('3')).toBeInTheDocument() // devices_in_alert from summary
    })
  })

  it('renders chart component when data available', async () => {
    (api.queryApi.getNetworkSummary as jest.Mock).mockResolvedValue({
      total_devices: 10,
      devices_up: 8,
      devices_down: 2,
      devices_in_alert: 3,
    })
    (api.queryApi.getActiveAlerts as jest.Mock).mockResolvedValue([])
    (api.queryApi.getTopDevices as jest.Mock).mockResolvedValue([])
    (api.queryApi.getDeviceUtilization as jest.Mock).mockResolvedValue([
      { timestamp: '2024-01-01T00:00:00Z', avg_cpu: 45, avg_memory: 62 },
      { timestamp: '2024-01-01T01:00:00Z', avg_cpu: 48, avg_memory: 65 },
    ])

    renderWithProviders(<DashboardPage />)

    await waitFor(() => {
      // Recharts renders SVG
      expect(document.querySelector('svg')).toBeInTheDocument()
    })
  })
})

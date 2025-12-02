/**
 * Component tests for KpiCard
 * Tests KPI card rendering with various props
 */
import { render, screen } from '@testing-library/react'
import { Server } from 'lucide-react'
import { KpiCard } from '../KpiCard'

describe('KpiCard', () => {
  it('renders title and value correctly', () => {
    render(
      <KpiCard
        title="Total Devices"
        value={42}
        icon={Server}
      />
    )

    expect(screen.getByText('Total Devices')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders string values correctly', () => {
    render(
      <KpiCard
        title="Status"
        value="Online"
        icon={Server}
      />
    )

    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Online')).toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(
      <KpiCard
        title="Total Devices"
        value={42}
        icon={Server}
        description="Across all sites"
      />
    )

    expect(screen.getByText('Across all sites')).toBeInTheDocument()
  })

  it('does not render description when not provided', () => {
    render(
      <KpiCard
        title="Total Devices"
        value={42}
        icon={Server}
      />
    )

    expect(screen.queryByText(/Across all sites/)).not.toBeInTheDocument()
  })

  it('renders positive trend correctly', () => {
    render(
      <KpiCard
        title="Total Devices"
        value={42}
        icon={Server}
        trend={{ value: 10, isPositive: true }}
      />
    )

    const trendElement = screen.getByText(/\+10% from last hour/)
    expect(trendElement).toBeInTheDocument()
    expect(trendElement).toHaveClass('text-green-600')
  })

  it('renders negative trend correctly', () => {
    render(
      <KpiCard
        title="Total Devices"
        value={42}
        icon={Server}
        trend={{ value: -5, isPositive: false }}
      />
    )

    const trendElement = screen.getByText(/-5% from last hour/)
    expect(trendElement).toBeInTheDocument()
    expect(trendElement).toHaveClass('text-red-600')
  })

  it('does not render trend when not provided', () => {
    render(
      <KpiCard
        title="Total Devices"
        value={42}
        icon={Server}
      />
    )

    expect(screen.queryByText(/from last hour/)).not.toBeInTheDocument()
  })

  it('renders with all props provided', () => {
    render(
      <KpiCard
        title="Active Devices"
        value="85%"
        icon={Server}
        description="Network uptime"
        trend={{ value: 2.5, isPositive: true }}
      />
    )

    expect(screen.getByText('Active Devices')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('Network uptime')).toBeInTheDocument()
    expect(screen.getByText(/\+2.5% from last hour/)).toBeInTheDocument()
  })

  it('renders zero value correctly', () => {
    render(
      <KpiCard
        title="Alerts"
        value={0}
        icon={Server}
      />
    )

    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('renders large numbers correctly', () => {
    render(
      <KpiCard
        title="Total Requests"
        value={1234567}
        icon={Server}
      />
    )

    expect(screen.getByText('1234567')).toBeInTheDocument()
  })

  it('applies correct CSS classes', () => {
    const { container } = render(
      <KpiCard
        title="Total Devices"
        value={42}
        icon={Server}
      />
    )

    // Check card structure exists
    expect(container.querySelector('.text-2xl')).toBeInTheDocument()
    expect(container.querySelector('.font-bold')).toBeInTheDocument()
  })
})

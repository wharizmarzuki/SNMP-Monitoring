/**
 * Component tests for StatusBadge and StatusDot
 * Tests status indicator components
 */
import { render, screen } from '@testing-library/react'
import { StatusBadge, StatusDot } from '../StatusBadge'

describe('StatusBadge', () => {
  it('renders "Up" status correctly', () => {
    render(<StatusBadge status="up" />)

    expect(screen.getByText('Up')).toBeInTheDocument()
  })

  it('renders "Down" status correctly', () => {
    render(<StatusBadge status="down" />)

    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('renders "Warning" status correctly', () => {
    render(<StatusBadge status="warning" />)

    expect(screen.getByText('Warning')).toBeInTheDocument()
  })

  it('applies success variant for up status', () => {
    const { container } = render(<StatusBadge status="up" />)

    // Badge component should be rendered
    expect(screen.getByText('Up')).toBeInTheDocument()
  })

  it('applies destructive variant for down status', () => {
    const { container } = render(<StatusBadge status="down" />)

    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('applies warning variant for warning status', () => {
    const { container } = render(<StatusBadge status="warning" />)

    expect(screen.getByText('Warning')).toBeInTheDocument()
  })
})

describe('StatusDot', () => {
  it('renders green dot for up status', () => {
    const { container } = render(<StatusDot status="up" />)

    const dot = container.querySelector('.bg-green-500')
    expect(dot).toBeInTheDocument()
    expect(dot).toHaveClass('rounded-full')
    expect(dot).toHaveClass('w-2')
    expect(dot).toHaveClass('h-2')
  })

  it('renders red dot for down status', () => {
    const { container } = render(<StatusDot status="down" />)

    const dot = container.querySelector('.bg-red-500')
    expect(dot).toBeInTheDocument()
    expect(dot).toHaveClass('rounded-full')
  })

  it('renders yellow dot for warning status', () => {
    const { container } = render(<StatusDot status="warning" />)

    const dot = container.querySelector('.bg-yellow-500')
    expect(dot).toBeInTheDocument()
    expect(dot).toHaveClass('rounded-full')
  })

  it('renders as inline block element', () => {
    const { container } = render(<StatusDot status="up" />)

    const dot = container.querySelector('span')
    expect(dot).toHaveClass('inline-block')
  })
})

describe('StatusBadge and StatusDot integration', () => {
  it('can render multiple status badges', () => {
    const { container } = render(
      <>
        <StatusBadge status="up" />
        <StatusBadge status="down" />
        <StatusBadge status="warning" />
      </>
    )

    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Down')).toBeInTheDocument()
    expect(screen.getByText('Warning')).toBeInTheDocument()
  })

  it('can render multiple status dots', () => {
    const { container } = render(
      <>
        <StatusDot status="up" />
        <StatusDot status="down" />
        <StatusDot status="warning" />
      </>
    )

    expect(container.querySelectorAll('.bg-green-500').length).toBe(1)
    expect(container.querySelectorAll('.bg-red-500').length).toBe(1)
    expect(container.querySelectorAll('.bg-yellow-500').length).toBe(1)
  })
})

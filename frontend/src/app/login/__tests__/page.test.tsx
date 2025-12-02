/**
 * Component tests for Login Page
 * Tests login form functionality and error handling
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from '../page'
import * as auth from '@/lib/auth'

// Mock the auth service
jest.mock('@/lib/auth', () => ({
  authService: {
    login: jest.fn(),
  },
}))

// Mock useRouter
const mockPush = jest.fn()
const mockReplace = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders login form with all elements', () => {
    render(<LoginPage />)

    expect(screen.getByText('SNMP Monitoring System')).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders card description text', () => {
    render(<LoginPage />)

    expect(
      screen.getByText('Enter your credentials to access the monitoring dashboard')
    ).toBeInTheDocument()
  })

  it('renders setup instructions', () => {
    render(<LoginPage />)

    expect(screen.getByText('First time setup?')).toBeInTheDocument()
    expect(screen.getByText(/python scripts\/setup_admin.py/)).toBeInTheDocument()
  })

  it('updates username field on input', async () => {
    render(<LoginPage />)
    const user = userEvent.setup()

    const usernameInput = screen.getByLabelText('Username') as HTMLInputElement
    await user.type(usernameInput, 'admin')

    expect(usernameInput.value).toBe('admin')
  })

  it('updates password field on input', async () => {
    render(<LoginPage />)
    const user = userEvent.setup()

    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement
    await user.type(passwordInput, 'password123')

    expect(passwordInput.value).toBe('password123')
  })

  it('calls login API on form submit', async () => {
    (auth.authService.login as jest.Mock).mockResolvedValue({ token: 'fake-token' })

    render(<LoginPage />)
    const user = userEvent.setup()

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(usernameInput, 'admin')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(auth.authService.login).toHaveBeenCalledWith({
        username: 'admin',
        password: 'password123',
      })
    })
  })

  it('redirects to dashboard on successful login', async () => {
    (auth.authService.login as jest.Mock).mockResolvedValue({ token: 'fake-token' })

    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Username'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays error message on login failure', async () => {
    (auth.authService.login as jest.Mock).mockRejectedValue({
      status: 401,
      message: 'Invalid credentials',
    })

    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Username'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Invalid username or password')).toBeInTheDocument()
    })
  })

  it('displays network error message on connection failure', async () => {
    (auth.authService.login as jest.Mock).mockRejectedValue({
      code: 'ERR_NETWORK',
      message: 'Network error',
    })

    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Username'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Cannot connect to server. Please check your network connection.')
      ).toBeInTheDocument()
    })
  })

  it('displays inactive account error', async () => {
    (auth.authService.login as jest.Mock).mockRejectedValue({
      status: 403,
      message: 'Account inactive',
    })

    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Username'), 'inactive_user')
    await user.type(screen.getByLabelText('Password'), 'password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Account is inactive. Please contact administrator.')
      ).toBeInTheDocument()
    })
  })

  it('shows loading state during login', async () => {
    // Mock login to take some time
    (auth.authService.login as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    )

    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Username'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'password')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    // Button should show loading state
    expect(screen.getByText('Signing in...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })

  it('disables inputs during login', async () => {
    (auth.authService.login as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    )

    render(<LoginPage />)
    const user = userEvent.setup()

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')

    await user.type(usernameInput, 'admin')
    await user.type(passwordInput, 'password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    // Inputs should be disabled
    expect(usernameInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()
  })

  it('clears error message when user types', async () => {
    (auth.authService.login as jest.Mock).mockRejectedValue({
      status: 401,
      message: 'Invalid credentials',
    })

    render(<LoginPage />)
    const user = userEvent.setup()

    // Trigger error
    await user.type(screen.getByLabelText('Username'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Invalid username or password')).toBeInTheDocument()
    })

    // Type in username field should clear error
    await user.type(screen.getByLabelText('Username'), 'a')

    expect(screen.queryByText('Invalid username or password')).not.toBeInTheDocument()
  })

  it('requires username and password fields', () => {
    render(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')

    expect(usernameInput).toHaveAttribute('required')
    expect(passwordInput).toHaveAttribute('required')
  })

  it('has correct input types', () => {
    render(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')

    expect(usernameInput).toHaveAttribute('type', 'text')
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('has autocomplete attributes', () => {
    render(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')

    expect(usernameInput).toHaveAttribute('autocomplete', 'username')
    expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
  })

  it('autofocuses username field', () => {
    render(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    expect(usernameInput).toHaveAttribute('autofocus')
  })

  it('handles generic error message', async () => {
    (auth.authService.login as jest.Mock).mockRejectedValue({
      message: 'Something went wrong',
    })

    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Username'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })
})

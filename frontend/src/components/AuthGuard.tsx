"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { authService } from "@/lib/auth";
import { useUser } from "@/providers/UserProvider";

/**
 * AuthGuard component that protects routes from unauthorized access
 * - Redirects to /login if user is not authenticated
 * - Redirects to /dashboard if user is authenticated and tries to access /login
 * - Validates token by calling /auth/me to ensure it's not expired
 * - Updates UserContext so Navbar and other components can display user info
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);
  const { setUser } = useUser();

  useEffect(() => {
    const checkAuth = async () => {
      const hasToken = authService.isAuthenticated();
      const isLoginPage = pathname === "/login";

      // No token and not on login page → redirect to login
      if (!hasToken && !isLoginPage) {
        setUser(null); // Clear user context
        router.replace("/login");
        return;
      }

      // No token and on login page → show login page
      if (!hasToken && isLoginPage) {
        setUser(null); // Clear user context
        setIsReady(true);
        return;
      }

      // Has token → validate it by calling API
      if (hasToken) {
        try {
          // Validate token by fetching user info
          const userInfo = await authService.getCurrentUser();

          // Update user context so Navbar displays immediately
          setUser(userInfo);

          // Token is valid
          if (isLoginPage) {
            // On login page with valid token → redirect to dashboard
            router.replace("/dashboard");
          } else {
            // On protected page with valid token → show page
            setIsReady(true);
          }
        } catch (error: any) {
          // Only logout on 401 (expired/invalid token)
          if (error.status === 401 || error.code === "INVALID_TOKEN" || error.code === "INVALID_CREDENTIALS") {
            console.log("Token expired/invalid, clearing auth");
            authService.logout();
            setUser(null); // Clear user context

            if (!isLoginPage) {
              router.replace("/login");
            } else {
              setIsReady(true);
            }
          } else {
            // Network/server error - keep token, show error but allow access
            console.error("Failed to validate token (non-auth error):", error);
            // Try to load cached user if available
            const cachedUser = authService.getCachedUser();
            if (cachedUser) {
              setUser(cachedUser);
            }
            setIsReady(true); // Continue anyway
          }
        }
      }
    };

    checkAuth();
  }, [pathname, router, setUser]);

  // On login page, show immediately (no loading state)
  if (pathname === "/login") {
    return <>{children}</>;
  }

  // On protected pages, wait for auth validation
  if (!isReady) {
    // Show loading indicator while validating authentication
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}


"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { authService } from "@/lib/auth";

/**
 * AuthGuard component that protects routes from unauthorized access
 * - Redirects to /login if user is not authenticated
 * - Redirects to /dashboard if user is authenticated and tries to access /login
 * - Validates token by calling /auth/me to ensure it's not expired
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const hasToken = authService.isAuthenticated();
      const isLoginPage = pathname === "/login";

      // No token and not on login page → redirect to login
      if (!hasToken && !isLoginPage) {
        router.replace("/login");
        return;
      }

      // No token and on login page → show login page
      if (!hasToken && isLoginPage) {
        setIsReady(true);
        return;
      }

      // Has token → validate it by calling API
      if (hasToken) {
        try {
          // Validate token by fetching user info
          await authService.getCurrentUser();

          // Token is valid
          if (isLoginPage) {
            // On login page with valid token → redirect to dashboard
            router.replace("/dashboard");
          } else {
            // On protected page with valid token → show page
            setIsReady(true);
          }
        } catch (error) {
          // Token is invalid or expired → clear and redirect to login
          console.log("Token validation failed, clearing auth");
          authService.logout();

          if (!isLoginPage) {
            router.replace("/login");
          } else {
            setIsReady(true);
          }
        }
      }
    };

    checkAuth();
  }, [pathname, router]);

  // On login page, show immediately (no loading state)
  if (pathname === "/login") {
    return <>{children}</>;
  }

  // On protected pages, wait for auth validation
  if (!isReady) {
    return null; // Show nothing while validating (prevents flash)
  }

  return <>{children}</>;
}


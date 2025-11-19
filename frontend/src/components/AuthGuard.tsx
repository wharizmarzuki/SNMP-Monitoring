"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { authService } from "@/lib/auth";

/**
 * AuthGuard component that protects routes from unauthorized access
 * - Redirects to /login if user is not authenticated
 * - Redirects to /dashboard if user is authenticated and tries to access /login
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      const isAuthenticated = authService.isAuthenticated();
      const isLoginPage = pathname === "/login";

      if (!isAuthenticated && !isLoginPage) {
        // Not authenticated and trying to access protected route → redirect to login
        router.push("/login");
      } else if (isAuthenticated && isLoginPage) {
        // Authenticated and on login page → redirect to dashboard
        router.push("/dashboard");
      } else {
        // All good, allow access
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [pathname, router]);

  // Show nothing while checking auth to prevent flash of wrong content
  if (isChecking && pathname !== "/login") {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

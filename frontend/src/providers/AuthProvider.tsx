"use client";

import { useEffect } from "react";
import { setupAuthInterceptor } from "@/lib/auth";

/**
 * AuthProvider sets up authentication interceptors for API calls
 * Should be used at the root level of the application
 */
export default function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Setup auth interceptor on mount
    setupAuthInterceptor();
  }, []);

  return <>{children}</>;
}

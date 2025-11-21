"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { UserInfo } from "@/lib/auth";

interface UserContextType {
  user: UserInfo | null;
  setUser: (user: UserInfo | null) => void;
  updateUser: (user: UserInfo) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

/**
 * UserProvider manages user state across the application
 * This fixes the hydration issue where Navbar doesn't update after AuthGuard validates the token
 */
export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);

  const updateUser = (newUser: UserInfo) => {
    setUser(newUser);
  };

  return (
    <UserContext.Provider value={{ user, setUser, updateUser }}>
      {children}
    </UserContext.Provider>
  );
}

/**
 * Hook to access user context
 */
export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}

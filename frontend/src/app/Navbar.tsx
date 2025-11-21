"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, HardDrive, Bell, FileText, Settings, User, LogOut } from "lucide-react";
import { authService } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useUser } from "@/providers/UserProvider";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, setUser } = useUser();

  // Hide navbar on login page
  if (pathname === "/login") {
    return null;
  }

  const navItems = [
    { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { href: "/devices", icon: HardDrive, label: "Devices" },
    { href: "/alerts", icon: Bell, label: "Alerts" },
    { href: "/report", icon: FileText, label: "Report" },
    { href: "/settings", icon: Settings, label: "Settings" },
  ];

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/" || pathname === "/dashboard";
    }
    return pathname === href || pathname.startsWith(href + "/");
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null); // Clear user context
    router.push("/login");
  };

  const handleProfileClick = () => {
    router.push("/settings/profile");
  };

  return (
    <div className="w-full border-b bg-white">
      <div className="flex items-center justify-between gap-6 px-4 py-2">
        <div className="flex items-center gap-6">
          <div className="text-lg font-semibold">NetSNMP</div>
          <nav className="flex gap-2">
            {navItems.map(({ href, icon: Icon, label }) => (
              <Link
                key={href}
                href={href}
                className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-slate-100 hover:text-slate-900 transition-colors ${
                  isActive(href)
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-700"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
        </div>

        {/* User menu */}
        <div className="flex items-center gap-2">
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2">
                  <User className="h-4 w-4" />
                  <span className="text-sm">{user.username}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user.username}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleProfileClick} className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  Profile Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </div>
  );
}

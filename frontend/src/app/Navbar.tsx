"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, HardDrive, Bell, FileText, Settings } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

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

  return (
    <div className="w-full border-b bg-white">
      <div className="flex items-center gap-6 px-4 py-2">
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
    </div>
  );
}

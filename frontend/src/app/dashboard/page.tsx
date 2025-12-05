"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { Server, Activity, AlertTriangle, Network } from "lucide-react";
import { KpiCard } from "@/components/KpiCard";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { queryApi } from "@/lib/api";
import { NetworkSummary, Alert, TopDevice, DeviceUtilization } from "@/types";
import { DashboardCardsSkeleton } from "@/components/skeletons/CardSkeleton";
import { ChartSkeleton } from "@/components/skeletons/ChartSkeleton";
import { TableSkeleton } from "@/components/skeletons/TableSkeleton";

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState<number>(60);
  const [interval, setInterval] = useState<number>(1);
  const { resolvedTheme } = useTheme();

  // Smart interval restrictions based on time range (Option 1)
  const getAvailableIntervals = (minutes: number): number[] => {
    if (minutes <= 30) return [1];
    if (minutes <= 60) return [1, 5];
    if (minutes <= 180) return [1, 5];
    if (minutes <= 360) return [5, 10, 15];
    if (minutes <= 720) return [5, 10, 15, 30];
    if (minutes <= 1440) return [10, 15, 30, 60];
    return [60, 360, 720]; // 7 days
  };

  const availableIntervals = getAvailableIntervals(timeRange);

  // Auto-adjust interval when time range changes if current interval is not available
  React.useEffect(() => {
    if (!availableIntervals.includes(interval)) {
      setInterval(availableIntervals[0]);
    }
  }, [timeRange]);
  // Fetch network summary (Phase 3: With error handling)
  const { data: networkSummary, isLoading: summaryLoading, error: summaryError } = useQuery<NetworkSummary>({
    queryKey: ["networkSummary"],
    queryFn: () => queryApi.getNetworkSummary(),
  });

  // Fetch active alerts
  const { data: activeAlerts, isLoading: alertsLoading, error: alertsError } = useQuery<Alert[]>({
    queryKey: ["activeAlerts"],
    queryFn: () => queryApi.getActiveAlerts(),
  });

  // Fetch top CPU devices
  const { data: topCpuDevices, isLoading: cpuLoading, error: cpuError } = useQuery<TopDevice[]>({
    queryKey: ["topCpuDevices"],
    queryFn: () => queryApi.getTopDevices("cpu"),
  });

  // Fetch top memory devices
  const { data: topMemoryDevices, isLoading: memoryLoading, error: memoryError } = useQuery<TopDevice[]>({
    queryKey: ["topMemoryDevices"],
    queryFn: () => queryApi.getTopDevices("memory"),
  });

  // Fetch device utilization
  const { data: deviceUtilization, isLoading: utilizationLoading, error: utilizationError } = useQuery<DeviceUtilization[]>({
    queryKey: ["deviceUtilization", timeRange, interval],
    queryFn: () => queryApi.getDeviceUtilization(timeRange, interval),
  });

  const summary = networkSummary;
  const alerts = activeAlerts || [];
  const cpuDevices = topCpuDevices || [];
  const memoryDevices = topMemoryDevices || [];
  const utilization = deviceUtilization || [];

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>

      {/* Global Error Banner */}
      {(summaryError || alertsError || cpuError || memoryError || utilizationError) && (
        <div className="p-3 bg-red-100 border border-red-300 text-red-800 rounded">
          <p className="font-semibold">Some dashboard data failed to load</p>
          <p className="text-sm mt-1">Please refresh the page. If the problem persists, contact support.</p>
        </div>
      )}

      {/* Main Layout: Left (KPI + Chart) | Right (Sidebar) */}
      <div className="grid gap-4 grid-cols-1 lg:grid-cols-3">
        {/* Left Column (spans 2 columns on large screens) */}
        <div className="lg:col-span-2 space-y-4">
          {/* KPI Cards */}
          {summaryLoading ? (
            <DashboardCardsSkeleton />
          ) : (
            <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
              <KpiCard
                title="Total Devices"
                value={summary?.total_devices || 0}
                icon={Server}
                description="Monitored network devices"
              />
              <KpiCard
                title="Devices Up"
                value={summary?.devices_up || 0}
                icon={Activity}
                description="Currently online"
              />
              <KpiCard
                title="Devices in Alert"
                value={summary?.devices_in_alert || 0}
                icon={AlertTriangle}
                description="Requiring attention"
              />
            </div>
          )}

          {/* Devices in Alert Table - Moved from sidebar */}
          <Card>
            <CardHeader>
              <CardTitle>Devices in Alert</CardTitle>
              <CardDescription>
                Devices currently exceeding thresholds
              </CardDescription>
            </CardHeader>
            <CardContent>
              {alertsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex gap-4">
                      <div className="h-4 flex-1 animate-pulse rounded-md bg-slate-200 dark:bg-slate-800" />
                      <div className="h-4 flex-1 animate-pulse rounded-md bg-slate-200 dark:bg-slate-800" />
                      <div className="h-4 flex-1 animate-pulse rounded-md bg-slate-200 dark:bg-slate-800" />
                      <div className="h-4 flex-1 animate-pulse rounded-md bg-slate-200 dark:bg-slate-800" />
                    </div>
                  ))}
                </div>
              ) : alertsError ? (
                <p className="text-sm text-red-600">Failed to load alerts</p>
              ) : alerts.length === 0 ? (
                <p className="text-sm text-muted-foreground">No active alerts</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Hostname</TableHead>
                      <TableHead>Metric</TableHead>
                      <TableHead>Current Value</TableHead>
                      <TableHead>Remarks</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alerts.map((alert, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">
                          {alert.hostname}
                        </TableCell>
                        <TableCell>{alert.metric}</TableCell>
                        <TableCell>{alert.current_value}</TableCell>
                        <TableCell>{alert.threshold}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Device Bandwidth Utilization Chart */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Device Bandwidth Utilization</CardTitle>
                  <CardDescription>
                    Link utilization percentage over time by device
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Select value={timeRange.toString()} onValueChange={(value) => setTimeRange(Number(value))}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Time Range" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">Past 15 min</SelectItem>
                      <SelectItem value="30">Past 30 min</SelectItem>
                      <SelectItem value="60">Past 1 hour</SelectItem>
                      <SelectItem value="180">Past 3 hours</SelectItem>
                      <SelectItem value="360">Past 6 hours</SelectItem>
                      <SelectItem value="720">Past 12 hours</SelectItem>
                      <SelectItem value="1440">Past 24 hours</SelectItem>
                      <SelectItem value="10080">Past 7 days</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={interval.toString()} onValueChange={(value) => setInterval(Number(value))}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Interval" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1" disabled={!availableIntervals.includes(1)}>1 min</SelectItem>
                      <SelectItem value="5" disabled={!availableIntervals.includes(5)}>5 min</SelectItem>
                      <SelectItem value="10" disabled={!availableIntervals.includes(10)}>10 min</SelectItem>
                      <SelectItem value="15" disabled={!availableIntervals.includes(15)}>15 min</SelectItem>
                      <SelectItem value="30" disabled={!availableIntervals.includes(30)}>30 min</SelectItem>
                      <SelectItem value="60" disabled={!availableIntervals.includes(60)}>1 hour</SelectItem>
                      <SelectItem value="360" disabled={!availableIntervals.includes(360)}>6 hours</SelectItem>
                      <SelectItem value="720" disabled={!availableIntervals.includes(720)}>12 hours</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {utilizationLoading ? (
                <div className="h-[400px] flex items-end gap-2 p-4">
                  {Array.from({ length: 12 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 animate-pulse rounded-md bg-muted/50"
                      style={{ height: `${Math.random() * 60 + 40}%` }}
                    />
                  ))}
                </div>
              ) : utilizationError ? (
                <div className="h-[400px] flex items-center justify-center">
                  <p className="text-sm text-red-600">Failed to load utilization data</p>
                </div>
              ) : utilization.length === 0 ? (
                <div className="h-[400px] flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">No utilization data available</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart
                    data={(() => {
                      // Transform data: group by timestamp with device utilizations as columns
                      const timeSeriesMap = new Map<string, any>();
                      const devices = new Set<string>();

                      utilization.forEach(u => {
                        const deviceName = u.hostname || u.ip_address || 'Unknown';
                        devices.add(deviceName);

                        if (!timeSeriesMap.has(u.timestamp)) {
                          timeSeriesMap.set(u.timestamp, { timestamp: u.timestamp });
                        }

                        const dataPoint = timeSeriesMap.get(u.timestamp);
                        if (dataPoint) {
                          dataPoint[deviceName] = u.max_utilization_pct || 0;
                        }
                      });

                      return Array.from(timeSeriesMap.values()).sort((a, b) =>
                        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
                      );
                    })()}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke={resolvedTheme === 'dark' ? 'hsl(262 27.9% 25%)' : 'hsl(220 13% 85%)'}
                    />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                      stroke={resolvedTheme === 'dark' ? 'hsl(217.9 10.6% 64.9%)' : 'hsl(220 8.9% 46.1%)'}
                    />
                    <YAxis
                      label={{ value: 'Utilization %', angle: -90, position: 'insideLeft' }}
                      domain={(() => {
                        // Calculate max utilization across all devices and time points
                        const maxUtil = Math.max(
                          ...utilization.map(u => u.max_utilization_pct || 0),
                          0
                        );

                        // Dynamic scale based on max value
                        if (maxUtil <= 0.1) return [0, 0.1];
                        if (maxUtil <= 1) return [0, 1];
                        if (maxUtil <= 10) return [0, 10];
                        if (maxUtil <= 25) return [0, 25];
                        if (maxUtil <= 50) return [0, 50];
                        return [0, 100];
                      })()}
                      ticks={(() => {
                        // Calculate max utilization
                        const maxUtil = Math.max(
                          ...utilization.map(u => u.max_utilization_pct || 0),
                          0
                        );

                        // Generate appropriate ticks
                        if (maxUtil <= 0.1) return [0, 0.025, 0.05, 0.075, 0.1];
                        if (maxUtil <= 1) return [0, 0.25, 0.5, 0.75, 1];
                        if (maxUtil <= 10) return [0, 2.5, 5, 7.5, 10];
                        if (maxUtil <= 25) return [0, 6.25, 12.5, 18.75, 25];
                        if (maxUtil <= 50) return [0, 12.5, 25, 37.5, 50];
                        return [0, 25, 50, 75, 100];
                      })()}
                      tickFormatter={(value) => `${value}`}
                      stroke={resolvedTheme === 'dark' ? 'hsl(217.9 10.6% 64.9%)' : 'hsl(220 8.9% 46.1%)'}
                    />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                      formatter={(value: number) => {
                        // Smart decimal places based on value magnitude
                        if (value < 0.01) return `${value.toFixed(4)}%`;  // 0.0001% - 0.0099%
                        if (value < 0.1) return `${value.toFixed(3)}%`;   // 0.010% - 0.099%
                        if (value < 1) return `${value.toFixed(2)}%`;     // 0.10% - 0.99%
                        return `${value.toFixed(1)}%`;                    // 1.0% and above
                      }}
                      contentStyle={{
                        backgroundColor: resolvedTheme === 'dark' ? 'hsl(262 70% 4.1%)' : 'hsl(0 0% 100%)',
                        border: `1px solid ${resolvedTheme === 'dark' ? 'hsl(262 27.9% 16.9%)' : 'hsl(220 13% 91%)'}`,
                        borderRadius: '0.5rem',
                        color: resolvedTheme === 'dark' ? 'hsl(210 20% 98%)' : 'hsl(224 71.4% 4.1%)'
                      }}
                    />
                    <Legend
                      wrapperStyle={{
                        color: resolvedTheme === 'dark' ? 'hsl(210 20% 98%)' : 'hsl(224 71.4% 4.1%)'
                      }}
                    />
                    {/* Dynamically create Area components for each device */}
                    {Array.from(new Set(utilization.map(u => u.hostname || u.ip_address || 'Unknown'))).map((deviceName, index) => {
                      const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#82d882'];
                      return (
                        <Area
                          key={deviceName}
                          type="monotone"
                          dataKey={deviceName}
                          stroke={colors[index % colors.length]}
                          fill={colors[index % colors.length]}
                          fillOpacity={0.6}
                          name={deviceName}
                        />
                      );
                    })}
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar (spans 1 column) */}
        <div className="lg:col-span-1 space-y-4">
        {/* Card 1: Top 5 CPU Devices */}
        <Card>
          <CardHeader>
            <CardTitle>Top 5 CPU Utilization</CardTitle>
            <CardDescription>Devices with highest CPU usage</CardDescription>
          </CardHeader>
          <CardContent>
            {cpuLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="h-4 flex-1 animate-pulse rounded-md bg-slate-200 dark:bg-slate-800" />
                    <div className="h-4 w-16 animate-pulse rounded-md bg-muted/50" />
                  </div>
                ))}
              </div>
            ) : cpuError ? (
              <p className="text-sm text-red-600">Failed to load CPU data</p>
            ) : cpuDevices.length === 0 ? (
              <p className="text-sm text-muted-foreground">No data available</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Device</TableHead>
                    <TableHead className="text-right">Usage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cpuDevices.map((device) => (
                    <TableRow key={device.ip_address}>
                      <TableCell>
                        <div className="font-medium">{device.hostname}</div>
                        <div className="text-sm text-muted-foreground">
                          {device.ip_address}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {`${(device.value ?? 0).toFixed(1)}%`}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Card 2: Top 5 Memory Devices */}
        <Card>
          <CardHeader>
            <CardTitle>Top 5 Memory Utilization</CardTitle>
            <CardDescription>Devices with highest memory usage</CardDescription>
          </CardHeader>
          <CardContent>
            {memoryLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="h-4 flex-1 animate-pulse rounded-md bg-slate-200 dark:bg-slate-800" />
                    <div className="h-4 w-16 animate-pulse rounded-md bg-muted/50" />
                  </div>
                ))}
              </div>
            ) : memoryError ? (
              <p className="text-sm text-red-600">Failed to load memory data</p>
            ) : memoryDevices.length === 0 ? (
              <p className="text-sm text-muted-foreground">No data available</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Device</TableHead>
                    <TableHead className="text-right">Usage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {memoryDevices.map((device) => (
                    <TableRow key={device.ip_address}>
                      <TableCell>
                        <div className="font-medium">{device.hostname}</div>
                        <div className="text-sm text-muted-foreground">
                          {device.ip_address}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {`${(device.value ?? 0).toFixed(1)}%`}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}

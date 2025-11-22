"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
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

export default function DashboardPage() {
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
    queryKey: ["deviceUtilization"],
    queryFn: () => queryApi.getDeviceUtilization(),
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

          {/* Device Bandwidth Utilization Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Device Bandwidth Utilization</CardTitle>
              <CardDescription>
                Link utilization percentage over time by device
              </CardDescription>
            </CardHeader>
            <CardContent>
              {utilizationLoading ? (
                <div className="h-[400px] flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">Loading utilization data...</p>
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
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis
                      label={{ value: 'Utilization %', angle: -90, position: 'insideLeft' }}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                      formatter={(value: number) => `${value.toFixed(1)}%`}
                    />
                    <Legend />
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
        {/* Card 1: Alerts (Spans 2 ROWS) */}
        <Card className="md:row-span-2">
          <CardHeader>
            <CardTitle>Devices in Alert</CardTitle>
            <CardDescription>
              Devices currently exceeding thresholds
            </CardDescription>
          </CardHeader>
          <CardContent>
            {alertsLoading ? (
              <p className="text-sm text-muted-foreground">Loading alerts...</p>
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

        {/* Card 2: Top 5 CPU Devices */}
        {/* This card will automatically go in Row 1, Column 2 */}
        <Card>
          <CardHeader>
            <CardTitle>Top 5 CPU Utilization</CardTitle>
            <CardDescription>Devices with highest CPU usage</CardDescription>
          </CardHeader>
          <CardContent>
            {cpuLoading ? (
              <p className="text-sm text-muted-foreground">Loading CPU data...</p>
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

        {/* Card 3: Top 5 Memory Devices */}
        {/* This card will automatically go in Row 2, Column 2 */}
        <Card>
          <CardHeader>
            <CardTitle>Top 5 Memory Utilization</CardTitle>
            <CardDescription>Devices with highest memory usage</CardDescription>
          </CardHeader>
          <CardContent>
            {memoryLoading ? (
              <p className="text-sm text-muted-foreground">Loading memory data...</p>
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

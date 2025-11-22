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
  BarChart,
  Bar,
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
import { NetworkSummary, Alert, TopDevice, NetworkThroughput, DeviceUtilization } from "@/types";

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

  // Fetch network throughput
  const { data: networkThroughput, isLoading: throughputLoading, error: throughputError } = useQuery<NetworkThroughput[]>({
    queryKey: ["networkThroughput"],
    queryFn: () => queryApi.getNetworkThroughput(),
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
  const throughput = networkThroughput || [];
  const utilization = deviceUtilization || [];

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>

      {/* Global Error Banner */}
      {(summaryError || alertsError || cpuError || memoryError || throughputError || utilizationError) && (
        <div className="p-3 bg-red-100 border border-red-300 text-red-800 rounded">
          <p className="font-semibold">Some dashboard data failed to load</p>
          <p className="text-sm mt-1">Please refresh the page. If the problem persists, contact support.</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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

      {/* Main Grid: 2 columns */}
      <div className="grid gap-4 md:grid-cols-2">
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

      {/* Network Throughput */}
      <Card>
        <CardHeader>
          <CardTitle>Network Throughput</CardTitle>
          <CardDescription>
            Inbound and outbound traffic over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          {throughputLoading ? (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-sm text-muted-foreground">Loading throughput data...</p>
            </div>
          ) : throughputError ? (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-sm text-red-600">Failed to load throughput data</p>
            </div>
          ) : throughput.length === 0 ? (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-sm text-muted-foreground">No throughput data available</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart
                data={throughput}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="inbound_bps"
                  stackId="1"
                  stroke="#8884d8"
                  fill="#8884d8"
                  name="Inbound (bps)"
                />
                <Area
                  type="monotone"
                  dataKey="outbound_bps"
                  stackId="1"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  name="Outbound (bps)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Device Utilization Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Device Bandwidth Utilization</CardTitle>
          <CardDescription>
            Link utilization percentage by device
          </CardDescription>
        </CardHeader>
        <CardContent>
          {utilizationLoading ? (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-sm text-muted-foreground">Loading utilization data...</p>
            </div>
          ) : utilizationError ? (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-sm text-red-600">Failed to load utilization data</p>
            </div>
          ) : utilization.length === 0 ? (
            <div className="h-[300px] flex items-center justify-center">
              <p className="text-sm text-muted-foreground">No utilization data available</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={utilization.map(u => ({
                  name: u.hostname || u.ip_address || 'Unknown',
                  utilization: u.max_utilization_pct || 0,
                  inbound: u.utilization_in_pct || 0,
                  outbound: u.utilization_out_pct || 0,
                }))}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis
                  label={{ value: 'Utilization %', angle: -90, position: 'insideLeft' }}
                  domain={[0, 100]}
                />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(1)}%`}
                />
                <Legend />
                <Bar dataKey="inbound" fill="#8884d8" name="Inbound %" />
                <Bar dataKey="outbound" fill="#82ca9d" name="Outbound %" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

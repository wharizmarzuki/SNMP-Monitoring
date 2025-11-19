"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Pencil } from "lucide-react";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/StatusBadge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { deviceApi, queryApi } from "@/lib/api";
import { Device, DeviceMetric, InterfaceMetric } from "@/types";

// Helper function to format bytes to human-readable format
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Calculate rate as percentage
function calculateRate(part: number, total: number): number {
  return total > 0 ? (part / total * 100) : 0;
}

// Get color class based on rate
function getRateColor(rate: number): string {
  if (rate < 0.1) return 'text-green-600';
  if (rate < 1) return 'text-yellow-600';
  return 'text-red-600';
}

export default function DeviceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const ip = params.ip as string;

  // State to track client-side hydration
  const [isClient, setIsClient] = useState(false);

  // State for threshold inputs
  const [cpuThreshold, setCpuThreshold] = useState<string>("");
  const [memoryThreshold, setMemoryThreshold] = useState<string>("");
  const [reachabilityThreshold, setReachabilityThreshold] =
    useState<string>("");

  // Set to true only when mounted on the client
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Fetch device info
  const { data: deviceData } = useQuery<{ data: Device }>({
    queryKey: ["device", ip],
    queryFn: () => deviceApi.getByIp(ip),
    enabled: !!ip,
  });

  // Fetch device metrics (time series)
  const { data: metricsData } = useQuery<{ data: DeviceMetric[] }>({
    queryKey: ["deviceMetrics", ip],
    queryFn: () => queryApi.getDeviceMetrics(ip),
    enabled: !!ip,
  });

  // Fetch device interfaces (Phase 3: Using optimized summary endpoint - 60-80% smaller payload)
  const { data: interfacesData } = useQuery<{ data: InterfaceMetric[] }>({
    queryKey: ["deviceInterfaces", ip],
    queryFn: () => queryApi.getInterfaceSummary(ip),
    enabled: !!ip,
  });

  const device = deviceData?.data;
  const metrics = metricsData?.data || [];
  const interfaces = interfacesData?.data || [];

  // Populate threshold inputs when device data loads
  useEffect(() => {
    if (device?.cpu_threshold !== undefined) {
      setCpuThreshold(device.cpu_threshold.toString());
    }
    if (device?.memory_threshold !== undefined) {
      setMemoryThreshold(device.memory_threshold.toString());
    }
    if (device?.failure_threshold !== undefined) {
      setReachabilityThreshold(device.failure_threshold.toString());
    }
  }, [
    device?.cpu_threshold,
    device?.memory_threshold,
    device?.failure_threshold,
  ]);

  // State for error and success messages
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);

  // Batch threshold update mutation (Phase 3: Single API call for all thresholds)
  const updateThresholdsMutation = useMutation({
    mutationFn: (thresholds: {
      cpu_threshold?: number;
      memory_threshold?: number;
      failure_threshold?: number;
    }) => deviceApi.updateThresholds(ip, thresholds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", ip] });
      setUpdateError(null);
      setUpdateSuccess("All thresholds updated successfully!");
      // Clear success message after 3 seconds
      setTimeout(() => setUpdateSuccess(null), 3000);
    },
    onError: (error: any) => {
      console.error("Error updating thresholds:", error);
      setUpdateSuccess(null);
      // Use structured error from backend if available
      const errorMessage = error.message || "Failed to update thresholds. Please try again.";
      setUpdateError(errorMessage);
    },
  });

  const handleUpdateThresholds = () => {
    setUpdateError(null);
    setUpdateSuccess(null);

    // Validate inputs
    const cpu = parseFloat(cpuThreshold);
    const memory = parseFloat(memoryThreshold);
    const reachability = parseFloat(reachabilityThreshold);

    if (isNaN(cpu) || cpu < 0 || cpu > 100) {
      setUpdateError("CPU threshold must be between 0 and 100");
      return;
    }
    if (isNaN(memory) || memory < 0 || memory > 100) {
      setUpdateError("Memory threshold must be between 0 and 100");
      return;
    }
    if (isNaN(reachability) || reachability < 0) {
      setUpdateError("Reachability threshold must be a positive number");
      return;
    }

    // Single batch update (Phase 3 optimization: 3 API calls → 1 API call)
    updateThresholdsMutation.mutate({
      cpu_threshold: cpu,
      memory_threshold: memory,
      failure_threshold: reachability,
    });
  };

  // Create a sorted version of metrics to fix the chart order
  const sortedMetrics = useMemo(() => {
    // .slice() creates a copy so we don't mutate the original
    // react-query data in the cache.
    return metrics.slice().reverse();
  }, [metrics]);

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/devices")}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Devices
        </Button>
      </div>

      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">
          {device?.hostname || "Loading..."}
        </h2>
      </div>

      {/* Device Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Device Information</CardTitle>
          <CardDescription>
            Device details and threshold configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          {device ? (
            <div className="space-y-6">
              {/* Device Information - 3 columns */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Hostname
                  </p>
                  <p className="text-base">{device.hostname}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    IP Address
                  </p>
                  <p className="text-base">{device.ip_address}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Vendor
                  </p>
                  <p className="text-base">{device.vendor}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    MAC Address
                  </p>
                  <p className="text-base">{device.mac_address}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Status
                  </p>
                  <div className="mt-1">
                    <StatusBadge status={device.is_reachable ? "up" : "down"} />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Last Poll Success
                  </p>
                  <p className="text-base">
                    {device.last_poll_success
                      ? new Date(
                          device.last_poll_success + "Z"
                        ).toLocaleString()
                      : "N/A"}
                  </p>
                </div>
              </div>

              {/* Threshold Configuration */}
              <div className="border-t pt-4">
                <h3 className="text-sm font-semibold mb-3">
                  Device Thresholds
                </h3>

                {/* Success Message */}
                {updateSuccess && (
                  <div className="mb-4 p-3 bg-green-100 border border-green-300 text-green-800 rounded">
                    {updateSuccess}
                  </div>
                )}

                {/* Error Message */}
                {updateError && (
                  <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded">
                    {updateError}
                  </div>
                )}

                <div className="space-y-4">
                  {/* CPU Threshold */}
                  <div className="grid grid-cols-2 gap-4 items-end">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-2">
                        Current CPU Threshold
                      </p>
                      <p className="text-base">{device.cpu_threshold ?? 80}%</p>
                    </div>
                    <div>
                      <label
                        htmlFor="cpu-threshold"
                        className="text-sm font-medium text-muted-foreground mb-2 block"
                      >
                        New CPU Threshold (%)
                      </label>
                      <Input
                        id="cpu-threshold"
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={cpuThreshold}
                        onChange={(e) => setCpuThreshold(e.target.value)}
                        placeholder="Enter value"
                      />
                    </div>
                  </div>

                  {/* Memory Threshold */}
                  <div className="grid grid-cols-2 gap-4 items-end">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-2">
                        Current Memory Threshold
                      </p>
                      <p className="text-base">
                        {device.memory_threshold ?? 80}%
                      </p>
                    </div>
                    <div>
                      <label
                        htmlFor="memory-threshold"
                        className="text-sm font-medium text-muted-foreground mb-2 block"
                      >
                        New Memory Threshold (%)
                      </label>
                      <Input
                        id="memory-threshold"
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={memoryThreshold}
                        onChange={(e) => setMemoryThreshold(e.target.value)}
                        placeholder="Enter value"
                      />
                    </div>
                  </div>

                  {/* Reachability Threshold */}
                  <div className="grid grid-cols-2 gap-4 items-end">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-2">
                        Current Reachability Threshold
                      </p>
                      <p className="text-base">
                        {device.failure_threshold ?? "Not set"}
                      </p>
                    </div>
                    <div>
                      <label
                        htmlFor="reachability-threshold"
                        className="text-sm font-medium text-muted-foreground mb-2 block"
                      >
                        New Reachability Threshold
                      </label>
                      <Input
                        id="reachability-threshold"
                        type="number"
                        min="0"
                        step="1"
                        value={reachabilityThreshold}
                        onChange={(e) =>
                          setReachabilityThreshold(e.target.value)
                        }
                        placeholder="Enter value"
                      />
                    </div>
                  </div>

                  {/* Single Update Button */}
                  <div className="flex justify-end pt-2">
                    <Button
                      onClick={handleUpdateThresholds}
                      disabled={updateThresholdsMutation.isPending}
                      size="lg"
                    >
                      {updateThresholdsMutation.isPending
                        ? "Updating All Thresholds..."
                        : "Update All Thresholds"}
                    </Button>
                  </div>

                  <p className="text-xs text-muted-foreground">
                    CPU/Memory: Percentage thresholds for alerting |
                    Reachability: Consecutive failed polls before alerting
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Loading device information...
            </p>
          )}
        </CardContent>
      </Card>

      {/* Metrics Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* CPU Utilization Chart */}
        <Card>
          <CardHeader>
            <CardTitle>CPU Utilization</CardTitle>
            <CardDescription>Historical CPU usage over time</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Conditionally render chart only on the client */}
            {!isClient ? (
              <div className="h-[300px] w-full flex items-center justify-center text-sm text-muted-foreground">
                Loading Chart...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={sortedMetrics}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString()
                    }
                  />
                  <YAxis domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="cpu_utilization"
                    stroke="#8884d8"
                    name="CPU %"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Memory Utilization Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Memory Utilization</CardTitle>
            <CardDescription>Historical memory usage over time</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Conditionally render chart only on the client */}
            {!isClient ? (
              <div className="h-[300px] w-full flex items-center justify-center text-sm text-muted-foreground">
                Loading Chart...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={sortedMetrics}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString()
                    }
                  />
                  <YAxis domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="memory_utilization"
                    stroke="#82ca9d"
                    name="Memory %"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Interface List */}
      <Card>
        <CardHeader>
          <CardTitle>Network Interfaces</CardTitle>
          <CardDescription>Interface status, traffic, and error metrics</CardDescription>
        </CardHeader>
        <CardContent>
          {interfaces.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No interface data available
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-center">Interface Name</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                  <TableHead className="text-center">Traffic (In / Out)</TableHead>
                  <TableHead className="text-center">Discard Rate</TableHead>
                  <TableHead className="text-center">Error Rate</TableHead>
                  <TableHead className="text-center">Packet Drop Threshold</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {interfaces.map((iface) => {
                  const octetsIn = iface.octets_in || 0;
                  const octetsOut = iface.octets_out || 0;
                  const discardsIn = iface.discards_in || 0;
                  const discardsOut = iface.discards_out || 0;
                  const errorsIn = iface.errors_in || 0;
                  const errorsOut = iface.errors_out || 0;

                  const totalTraffic = octetsIn + octetsOut;
                  const totalDiscards = discardsIn + discardsOut;
                  const totalErrors = errorsIn + errorsOut;

                  const discardRate = calculateRate(totalDiscards, totalTraffic);
                  const errorRate = calculateRate(totalErrors, totalTraffic);

                  return (
                    <InterfaceRow
                      key={iface.if_index}
                      interface={iface}
                      deviceIp={ip}
                      octetsIn={octetsIn}
                      octetsOut={octetsOut}
                      discardRate={discardRate}
                      errorRate={errorRate}
                      onThresholdUpdate={() => {
                        queryClient.invalidateQueries({
                          queryKey: ["deviceInterfaces", ip],
                        });
                      }}
                    />
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Interface Row Component with inline threshold editing
function InterfaceRow({
  interface: iface,
  deviceIp,
  octetsIn,
  octetsOut,
  discardRate,
  errorRate,
  onThresholdUpdate,
}: {
  interface: InterfaceMetric;
  deviceIp: string;
  octetsIn: number;
  octetsOut: number;
  discardRate: number;
  errorRate: number;
  onThresholdUpdate: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [threshold, setThreshold] = useState(
    iface.packet_drop_threshold?.toString() || "100"
  );
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    const thresholdValue = parseFloat(threshold);
    if (isNaN(thresholdValue) || thresholdValue < 0) {
      setError("Threshold must be a positive number");
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await deviceApi.updateInterfaceThreshold(
        deviceIp,
        iface.if_index,
        thresholdValue
      );
      setIsEditing(false);
      onThresholdUpdate();
    } catch (err: any) {
      console.error("Error updating threshold:", err);
      setError(err.message || "Failed to update threshold");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setThreshold(iface.packet_drop_threshold?.toString() || "100");
    setIsEditing(false);
    setError(null);
  };

  return (
    <TableRow>
      {/* Interface Name */}
      <TableCell className="font-medium text-center">{iface.if_name}</TableCell>

      {/* Status */}
      <TableCell className="text-center">
        <StatusBadge status={iface.oper_status === 1 ? "up" : "down"} />
      </TableCell>

      {/* Traffic (In / Out) */}
      <TableCell className="text-center">
        <div className="flex flex-col text-sm items-center">
          <span className="text-blue-600">↓ {formatBytes(octetsIn)}</span>
          <span className="text-green-600">↑ {formatBytes(octetsOut)}</span>
        </div>
      </TableCell>

      {/* Discard Rate */}
      <TableCell className="text-center">
        <span className={`font-medium ${getRateColor(discardRate)}`}>
          {discardRate.toFixed(3)}%
        </span>
      </TableCell>

      {/* Error Rate */}
      <TableCell className="text-center">
        <span className={`font-medium ${getRateColor(errorRate)}`}>
          {errorRate.toFixed(3)}%
        </span>
      </TableCell>

      {/* Packet Drop Threshold - Inline Editing */}
      <TableCell className="text-center">
        <div className="min-h-[40px] flex items-center justify-center">
          {isEditing ? (
            <div className="flex flex-col gap-2 w-full">
              <div className="flex gap-2 items-center justify-center">
                <Input
                  type="number"
                  min="0"
                  step="1"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  className="w-24 h-8"
                  disabled={isSaving}
                />
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={isSaving}
                  className="h-8"
                >
                  {isSaving ? "..." : "Save"}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="h-8"
                >
                  Cancel
                </Button>
              </div>
              {error && (
                <span className="text-xs text-red-600">{error}</span>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 justify-center">
              <span className="text-sm">
                {iface.packet_drop_threshold || 100} drops
              </span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setIsEditing(true)}
                className="h-7 w-7 p-0 hover:bg-gray-100"
              >
                <Pencil className="h-3.5 w-3.5 text-gray-700" />
              </Button>
            </div>
          )}
        </div>
      </TableCell>
    </TableRow>
  );
}

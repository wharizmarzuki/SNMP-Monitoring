"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Pencil, Trash2, Wrench, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/StatusBadge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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

  // State for time range and interval filters
  const [timeRange, setTimeRange] = useState<number>(60);
  const [interval, setInterval] = useState<number>(1);

  // State for interface table sorting
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  // State for interface table pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Smart interval restrictions (same as dashboard)
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

  // Auto-adjust interval when time range changes
  useEffect(() => {
    if (!availableIntervals.includes(interval)) {
      setInterval(availableIntervals[0]);
    }
  }, [timeRange]);

  // Set to true only when mounted on the client
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Fetch device info
  const { data: deviceData } = useQuery<Device>({
    queryKey: ["device", ip],
    queryFn: () => deviceApi.getByIp(ip),
    enabled: !!ip,
  });

  // Fetch device metrics (time series)
  const { data: metricsData } = useQuery<DeviceMetric[]>({
    queryKey: ["deviceMetrics", ip, timeRange, interval],
    queryFn: () => queryApi.getDeviceMetrics(ip, timeRange, interval),
    enabled: !!ip,
  });

  // Fetch device interfaces (Phase 3: Using optimized summary endpoint - 60-80% smaller payload)
  const { data: interfacesData } = useQuery<InterfaceMetric[]>({
    queryKey: ["deviceInterfaces", ip],
    queryFn: () => queryApi.getInterfaceSummary(ip),
    enabled: !!ip,
  });

  const device = deviceData;
  const metrics = metricsData || [];
  const interfacesRaw = interfacesData || [];

  // Sort interfaces based on column
  const interfaces = useMemo(() => {
    if (!sortColumn) return interfacesRaw;

    return [...interfacesRaw].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortColumn) {
        case "if_name":
          aValue = a.if_name || "";
          bValue = b.if_name || "";
          break;
        case "oper_status":
          aValue = a.oper_status || 0;
          bValue = b.oper_status || 0;
          break;
        case "traffic":
          aValue = (a.octets_in || 0) + (a.octets_out || 0);
          bValue = (b.octets_in || 0) + (b.octets_out || 0);
          break;
        case "discard_rate":
          const aDiscards = (a.discards_in || 0) + (a.discards_out || 0);
          const bDiscards = (b.discards_in || 0) + (b.discards_out || 0);
          const aTraffic = (a.octets_in || 0) + (a.octets_out || 0);
          const bTraffic = (b.octets_in || 0) + (b.octets_out || 0);
          aValue = calculateRate(aDiscards, aTraffic);
          bValue = calculateRate(bDiscards, bTraffic);
          break;
        case "error_rate":
          const aErrors = (a.errors_in || 0) + (a.errors_out || 0);
          const bErrors = (b.errors_in || 0) + (b.errors_out || 0);
          const aTraffic2 = (a.octets_in || 0) + (a.octets_out || 0);
          const bTraffic2 = (b.octets_in || 0) + (b.octets_out || 0);
          aValue = calculateRate(aErrors, aTraffic2);
          bValue = calculateRate(bErrors, bTraffic2);
          break;
        default:
          return 0;
      }

      if (typeof aValue === "string") {
        const comparison = aValue.localeCompare(bValue);
        return sortOrder === "asc" ? comparison : -comparison;
      } else {
        const comparison = aValue - bValue;
        return sortOrder === "asc" ? comparison : -comparison;
      }
    });
  }, [interfacesRaw, sortColumn, sortOrder]);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortOrder("asc");
    }
    // Reset to first page when sorting changes
    setCurrentPage(1);
  };

  // Paginate sorted interfaces
  const paginatedInterfaces = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return interfaces.slice(startIndex, endIndex);
  }, [interfaces, currentPage, itemsPerPage]);

  // Pagination metadata
  const totalItems = interfaces.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  // Reset to first page when itemsPerPage changes
  const handleItemsPerPageChange = (value: string) => {
    setItemsPerPage(value === "all" ? totalItems : Number(value));
    setCurrentPage(1);
  };

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

  // State for delete confirmation
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // State for maintenance mode
  const [maintenanceEnabled, setMaintenanceEnabled] = useState(false);
  const [maintenanceDuration, setMaintenanceDuration] = useState("60");
  const [maintenanceReason, setMaintenanceReason] = useState("");

  // Update maintenance state when device data loads
  useEffect(() => {
    if (device?.maintenance_mode !== undefined) {
      setMaintenanceEnabled(device.maintenance_mode);
    }
    if (device?.maintenance_reason) {
      setMaintenanceReason(device.maintenance_reason);
    }
  }, [device?.maintenance_mode, device?.maintenance_reason]);

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

  // Delete device mutation
  const deleteDeviceMutation = useMutation({
    mutationFn: () => deviceApi.delete(ip),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      router.push("/devices");
    },
    onError: (error: any) => {
      console.error("Failed to delete device:", error);
      alert(`Failed to delete device: ${error.message || "Unknown error"}`);
    },
  });

  // Maintenance mode mutation
  const maintenanceModeMutation = useMutation({
    mutationFn: (data: { enabled: boolean; duration_minutes?: number; reason?: string }) =>
      deviceApi.updateMaintenanceMode(ip, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", ip] });
      setUpdateSuccess("Maintenance mode updated successfully!");
      setTimeout(() => setUpdateSuccess(null), 3000);
    },
    onError: (error: any) => {
      setUpdateError(error.message || "Failed to update maintenance mode");
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

  const handleMaintenanceModeToggle = (checked: boolean) => {
    setMaintenanceEnabled(checked);
    if (!checked) {
      // Disable maintenance mode immediately
      maintenanceModeMutation.mutate({ enabled: false });
    }
  };

  const handleUpdateMaintenanceMode = () => {
    const duration = parseInt(maintenanceDuration);
    if (isNaN(duration) || duration < 0) {
      setUpdateError("Duration must be a positive number");
      return;
    }

    maintenanceModeMutation.mutate({
      enabled: maintenanceEnabled,
      duration_minutes: duration,
      reason: maintenanceReason || undefined,
    });
  };

  const confirmDelete = () => {
    deleteDeviceMutation.mutate();
  };

  // Create a sorted version of metrics to fix the chart order
  const sortedMetrics = useMemo(() => {
    // .slice() creates a copy so we don't mutate the original
    // react-query data in the cache.
    return metrics.slice().reverse();
  }, [metrics]);

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/devices")}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Devices
        </Button>

        <Button
          variant="destructive"
          size="sm"
          onClick={() => setDeleteDialogOpen(true)}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Delete Device
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

              {/* Maintenance Mode Section */}
              <div className="border-t pt-4 mt-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-semibold flex items-center gap-2">
                      <Wrench className="h-4 w-4" />
                      Maintenance Mode
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      Suppress all alerts for this device during maintenance windows
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Label htmlFor="maintenance-toggle" className="text-sm">
                      {maintenanceEnabled ? "Enabled" : "Disabled"}
                    </Label>
                    <Switch
                      id="maintenance-toggle"
                      checked={maintenanceEnabled}
                      onCheckedChange={handleMaintenanceModeToggle}
                      disabled={maintenanceModeMutation.isPending}
                    />
                  </div>
                </div>

                {maintenanceEnabled && (
                  <div className="space-y-4 p-4 bg-amber-50 border border-amber-200 rounded">
                    {device?.maintenance_until && (
                      <div className="text-sm text-amber-900">
                        <strong>Active until:</strong>{" "}
                        {new Date(device.maintenance_until + "Z").toLocaleString()}
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="maintenance-duration">
                          Duration (minutes)
                        </Label>
                        <Input
                          id="maintenance-duration"
                          type="number"
                          min="1"
                          value={maintenanceDuration}
                          onChange={(e) => setMaintenanceDuration(e.target.value)}
                          disabled={maintenanceModeMutation.isPending}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="maintenance-reason">Reason (Optional)</Label>
                        <Input
                          id="maintenance-reason"
                          type="text"
                          placeholder="e.g., Scheduled upgrade"
                          value={maintenanceReason}
                          onChange={(e) => setMaintenanceReason(e.target.value)}
                          disabled={maintenanceModeMutation.isPending}
                        />
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button
                        onClick={handleUpdateMaintenanceMode}
                        disabled={maintenanceModeMutation.isPending}
                        size="sm"
                      >
                        {maintenanceModeMutation.isPending
                          ? "Updating..."
                          : "Update Maintenance Window"}
                      </Button>
                    </div>
                  </div>
                )}

                {device?.maintenance_mode && device?.maintenance_reason && (
                  <div className="mt-2 text-sm text-amber-700">
                    <strong>Reason:</strong> {device.maintenance_reason}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Loading device information...
            </p>
          )}
        </CardContent>
      </Card>

      {/* Compact Chart Filter Toolbar */}
      <div className="flex items-center gap-3 bg-muted/50 p-3 rounded-lg border">
        <span className="text-sm font-medium text-muted-foreground">Chart Filters:</span>
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
        <span className="text-xs text-muted-foreground ml-auto">
          Applies to both CPU and Memory charts
        </span>
      </div>

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

      <div className="space-y-4">
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
            // CHANGE 1: Added 'table-fixed' and 'w-full'
            // 'table-fixed' forces the columns to respect the widths set in the header
            <Table className="table-fixed w-full">
              <TableHeader>
                <TableRow>
                  {/* CHANGE 2: Added explicit widths to all headers */}

                  {/* Wide column for Interface Name */}
                  <TableHead className="text-center w-[220px]">
                    <button
                      onClick={() => handleSort("if_name")}
                      className="flex items-center gap-1 hover:text-foreground transition-colors mx-auto"
                    >
                      Interface Name
                      {sortColumn === "if_name" ? (
                        sortOrder === "asc" ? (
                          <ArrowUp className="h-4 w-4" />
                        ) : (
                          <ArrowDown className="h-4 w-4" />
                        )
                      ) : (
                        <ArrowUpDown className="h-4 w-4 opacity-50" />
                      )}
                    </button>
                  </TableHead>

                  {/* Fixed small width for Status */}
                  <TableHead className="text-center w-[100px]">
                    <button
                      onClick={() => handleSort("oper_status")}
                      className="flex items-center gap-1 hover:text-foreground transition-colors mx-auto"
                    >
                      Status
                      {sortColumn === "oper_status" ? (
                        sortOrder === "asc" ? (
                          <ArrowUp className="h-4 w-4" />
                        ) : (
                          <ArrowDown className="h-4 w-4" />
                        )
                      ) : (
                        <ArrowUpDown className="h-4 w-4 opacity-50" />
                      )}
                    </button>
                  </TableHead>

                  {/* Flexible but defined width for Traffic */}
                  <TableHead className="text-center w-[200px]">
                    <button
                      onClick={() => handleSort("traffic")}
                      className="flex items-center gap-1 hover:text-foreground transition-colors mx-auto"
                    >
                      Traffic (In / Out)
                      {sortColumn === "traffic" ? (
                        sortOrder === "asc" ? (
                          <ArrowUp className="h-4 w-4" />
                        ) : (
                          <ArrowDown className="h-4 w-4" />
                        )
                      ) : (
                        <ArrowUpDown className="h-4 w-4 opacity-50" />
                      )}
                    </button>
                  </TableHead>

                  {/* Fixed widths for Rates */}
                  <TableHead className="text-center w-[120px]">
                    <button
                      onClick={() => handleSort("discard_rate")}
                      className="flex items-center gap-1 hover:text-foreground transition-colors mx-auto"
                    >
                      Discard Rate
                      {sortColumn === "discard_rate" ? (
                        sortOrder === "asc" ? (
                          <ArrowUp className="h-4 w-4" />
                        ) : (
                          <ArrowDown className="h-4 w-4" />
                        )
                      ) : (
                        <ArrowUpDown className="h-4 w-4 opacity-50" />
                      )}
                    </button>
                  </TableHead>
                  <TableHead className="text-center w-[120px]">
                    <button
                      onClick={() => handleSort("error_rate")}
                      className="flex items-center gap-1 hover:text-foreground transition-colors mx-auto"
                    >
                      Error Rate
                      {sortColumn === "error_rate" ? (
                        sortOrder === "asc" ? (
                          <ArrowUp className="h-4 w-4" />
                        ) : (
                          <ArrowDown className="h-4 w-4" />
                        )
                      ) : (
                        <ArrowUpDown className="h-4 w-4 opacity-50" />
                      )}
                    </button>
                  </TableHead>
                  
                  {/* CHANGE 3: Large reserved width (240px) for the Action column
                      This ensures the column is already wide enough to hold 
                      Inputs + Save/Cancel buttons without expanding. */}
                  <TableHead className="text-center w-[240px]">Discard Rate Threshold (%)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedInterfaces.map((iface) => {
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

          {/* Pagination Controls */}
          {interfaces.length > 0 && (
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  Showing {startItem}-{endItem} of {totalItems}
                </span>
              </div>

              <div className="flex items-center gap-4">
                {/* Items per page selector */}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Items per page:</span>
                  <Select value={itemsPerPage.toString()} onValueChange={handleItemsPerPageChange}>
                    <SelectTrigger className="w-[100px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="20">20</SelectItem>
                      <SelectItem value="30">30</SelectItem>
                      <SelectItem value="all">All</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Page navigation */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Device?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete{" "}
              <span className="font-semibold">
                {device?.hostname} ({device?.ip_address})
              </span>
              ? This will remove all associated metrics, interfaces, and alerts.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteDeviceMutation.isPending}
            >
              {deleteDeviceMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
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
    iface.packet_drop_threshold?.toString() || "0.1"
  );
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    const thresholdValue = parseFloat(threshold);
    if (isNaN(thresholdValue) || thresholdValue < 0 || thresholdValue > 100) {
      setError("Threshold must be between 0 and 100%");
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
    setThreshold(iface.packet_drop_threshold?.toString() || "0.1");
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

      {/* Discard Rate Threshold - Inline Editing */}
      <TableCell className="text-center">
        <div className="min-h-[40px] flex items-center justify-center">
          {isEditing ? (
            <div className="flex flex-col gap-2 w-full">
              <div className="flex gap-2 items-center justify-center">
                <Input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  placeholder="0.1"
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
                {iface.packet_drop_threshold || 0.1}%
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

"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
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

  // Fetch device interfaces
  const { data: interfacesData } = useQuery<{ data: InterfaceMetric[] }>({
    queryKey: ["deviceInterfaces", ip],
    queryFn: () => queryApi.getDeviceInterfaces(ip),
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

  // Mutation for updating CPU threshold
  const updateCpuThresholdMutation = useMutation({
    mutationFn: (threshold: number) =>
      deviceApi.updateCpuThreshold(ip, threshold),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", ip] });
      alert("CPU threshold updated successfully!");
    },
    onError: (error) => {
      console.error("Error updating CPU threshold:", error);
      alert("Failed to update CPU threshold");
    },
  });

  // Mutation for updating Memory threshold
  const updateMemoryThresholdMutation = useMutation({
    mutationFn: (threshold: number) =>
      deviceApi.updateMemoryThreshold(ip, threshold),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", ip] });
      alert("Memory threshold updated successfully!");
    },
    onError: (error) => {
      console.error("Error updating Memory threshold:", error);
      alert("Failed to update Memory threshold");
    },
  });

  // Mutation for updating reachability threshold
  const updateReachabilityThresholdMutation = useMutation({
    mutationFn: (threshold: number) =>
      deviceApi.updateReachabilityThreshold(ip, threshold),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", ip] });
      alert("Reachability threshold updated successfully!");
    },
    onError: (error) => {
      console.error("Error updating threshold:", error);
      alert("Failed to update reachability threshold");
    },
  });

  const handleUpdateCpuThreshold = () => {
    const threshold = parseFloat(cpuThreshold);
    if (isNaN(threshold) || threshold < 0 || threshold > 100) {
      alert("Please enter a valid number between 0 and 100");
      return;
    }
    updateCpuThresholdMutation.mutate(threshold);
  };

  const handleUpdateMemoryThreshold = () => {
    const threshold = parseFloat(memoryThreshold);
    if (isNaN(threshold) || threshold < 0 || threshold > 100) {
      alert("Please enter a valid number between 0 and 100");
      return;
    }
    updateMemoryThresholdMutation.mutate(threshold);
  };

  const handleUpdateReachabilityThreshold = () => {
    const threshold = parseFloat(reachabilityThreshold);
    if (isNaN(threshold) || threshold < 0) {
      alert("Please enter a valid positive number");
      return;
    }
    updateReachabilityThresholdMutation.mutate(threshold);
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
                <div className="space-y-4">
                  {/* CPU Threshold */}
                  <div className="grid grid-cols-3 gap-4 items-end">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-2">
                        CPU Threshold (%)
                      </p>
                      <p className="text-base">{device.cpu_threshold ?? 80}%</p>
                    </div>
                    <div>
                      <label
                        htmlFor="cpu-threshold"
                        className="text-sm font-medium text-muted-foreground mb-2 block"
                      >
                        New Threshold (%)
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
                    <div className="flex justify-center">
                      <Button
                        onClick={handleUpdateCpuThreshold}
                        disabled={updateCpuThresholdMutation.isPending}
                      >
                        {updateCpuThresholdMutation.isPending
                          ? "Updating..."
                          : "Update"}
                      </Button>
                    </div>
                  </div>

                  {/* Memory Threshold */}
                  <div className="grid grid-cols-3 gap-4 items-end">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-2">
                        Memory Threshold (%)
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
                        New Threshold (%)
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
                    <div className="flex justify-center">
                      <Button
                        onClick={handleUpdateMemoryThreshold}
                        disabled={updateMemoryThresholdMutation.isPending}
                      >
                        {updateMemoryThresholdMutation.isPending
                          ? "Updating..."
                          : "Update"}
                      </Button>
                    </div>
                  </div>

                  {/* Reachability Threshold */}
                  <div className="grid grid-cols-3 gap-4 items-end">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-2">
                        Reachability Threshold
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
                        New Threshold
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
                    <div className="flex justify-center">
                      <Button
                        onClick={handleUpdateReachabilityThreshold}
                        disabled={updateReachabilityThresholdMutation.isPending}
                      >
                        {updateReachabilityThresholdMutation.isPending
                          ? "Updating..."
                          : "Update"}
                      </Button>
                    </div>
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
          <CardDescription>Interface status and metrics</CardDescription>
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
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Octets In</TableHead>
                  <TableHead>Octets Out</TableHead>
                  <TableHead>Discards In</TableHead>
                  <TableHead>Discards Out</TableHead>
                  <TableHead>Errors In</TableHead>
                  <TableHead>Errors Out</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {interfaces.map((iface) => (
                  <TableRow key={iface.if_index}>
                    <TableCell className="font-medium">
                      {iface.if_name}
                    </TableCell>
                    <TableCell>
                      <StatusBadge
                        status={iface.oper_status === 1 ? "up" : "down"}
                      />
                    </TableCell>
                    <TableCell>{iface.octets_in.toLocaleString()}</TableCell>
                    <TableCell>{iface.octets_out.toLocaleString()}</TableCell>
                    <TableCell>{iface.discards_in}</TableCell>
                    <TableCell>{iface.discards_out}</TableCell>
                    <TableCell>{iface.errors_in}</TableCell>
                    <TableCell>{iface.errors_out}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
import { Badge } from "@/components/ui/badge";
import { CheckCircle, ChevronLeft, ChevronRight } from "lucide-react";
import { queryApi, deviceApi } from "@/lib/api";
import { Alert, AlertHistory } from "@/types";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Alert History filters and pagination
  const [historyPage, setHistoryPage] = useState(1);
  const [historyPerPage] = useState(20);
  const [historySeverityFilter, setHistorySeverityFilter] = useState<string>("all");
  const [historyAlertTypeFilter, setHistoryAlertTypeFilter] = useState<string>("all");
  const [historyClearedFilter, setHistoryClearedFilter] = useState<string>("all");

  const severityMap: Record<Alert['severity'], 'warning' | 'destructive' | 'default'> = {
    'Warning': 'default',
    'High': 'warning',
    'Critical': 'destructive',
  };

  const { data: alertsData, isLoading, error: queryError } = useQuery<Alert[]>({
    queryKey: ["activeAlerts"],
    queryFn: () => queryApi.getActiveAlerts(),
  });

  const alerts = alertsData || [];

  // Fetch alert history with filters
  const { data: alertHistoryData, isLoading: isLoadingHistory } = useQuery<AlertHistory[]>({
    queryKey: [
      "alertHistory",
      historyPage,
      historyPerPage,
      historySeverityFilter,
      historyAlertTypeFilter,
      historyClearedFilter
    ],
    queryFn: () => queryApi.getAlertHistory({
      page: historyPage,
      per_page: historyPerPage,
      severity: historySeverityFilter !== "all" ? historySeverityFilter : undefined,
      alert_type: historyAlertTypeFilter !== "all" ? historyAlertTypeFilter : undefined,
      include_cleared: historyClearedFilter === "all" ? true : historyClearedFilter === "cleared"
    }),
  });

  const alertHistory = alertHistoryData || [];

  // Helper function to parse alert and determine alert type
  const parseAlert = (alert: Alert) => {
    const lowerMetric = alert.metric.toLowerCase();

    // Check for device-level alerts
    if (lowerMetric.includes('cpu')) {
      return { type: 'device' as const, alertType: 'cpu' as const };
    }
    if (lowerMetric.includes('memory')) {
      return { type: 'device' as const, alertType: 'memory' as const };
    }
    if (lowerMetric.includes('reachability') || lowerMetric.includes('ping') || lowerMetric.includes('unreachable')) {
      return { type: 'device' as const, alertType: 'reachability' as const };
    }

    // Check for interface-level alerts
    if (lowerMetric.includes('interface') || lowerMetric.includes('down') || lowerMetric.includes('drop')) {
      if (!alert.if_index) {
        console.warn(`Interface alert missing if_index: ${alert.metric}`);
        return null;
      }

      // Determine if it's a status or drops alert
      if (lowerMetric.includes('drop')) {
        return { type: 'interface' as const, alertType: 'drops' as const, ifIndex: alert.if_index };
      } else {
        // Default to status for interface alerts (includes "down", "up", "status", etc.)
        return { type: 'interface' as const, alertType: 'status' as const, ifIndex: alert.if_index };
      }
    }

    return null;
  };

  const acknowledgeMutation = useMutation({
    mutationFn: async (alert: Alert) => {
      const parsed = parseAlert(alert);

      if (!parsed) {
        console.warn(`Unknown alert metric: ${alert.metric}`);
        return Promise.resolve();
      }

      if (parsed.type === 'device') {
        return deviceApi.acknowledgeDeviceAlert(alert.ip_address, parsed.alertType);
      } else {
        return deviceApi.acknowledgeInterfaceAlert(alert.ip_address, parsed.ifIndex, parsed.alertType);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activeAlerts"] });
      setActionError(null);
      setActionSuccess("Alert acknowledged successfully");
      setTimeout(() => setActionSuccess(null), 3000);
    },
    onError: (error: any) => {
      console.error("Error acknowledging alert:", error);
      setActionSuccess(null);
      const errorMessage = error.message || "Failed to acknowledge alert. Please try again.";
      setActionError(errorMessage);
    },
  });

  const resolveMutation = useMutation({
    mutationFn: async (alert: Alert) => {
      const parsed = parseAlert(alert);

      if (!parsed) {
        console.warn(`Unknown alert metric: ${alert.metric}`);
        return Promise.resolve();
      }

      if (parsed.type === 'device') {
        return deviceApi.resolveDeviceAlert(alert.ip_address, parsed.alertType);
      } else {
        return deviceApi.resolveInterfaceAlert(alert.ip_address, parsed.ifIndex, parsed.alertType);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activeAlerts"] });
      setActionError(null);
      setActionSuccess("Alert resolved successfully");
      setTimeout(() => setActionSuccess(null), 3000);
    },
    onError: (error: any) => {
      console.error("Error resolving alert:", error);
      setActionSuccess(null);
      const errorMessage = error.message || "Failed to resolve alert. Please try again.";
      setActionError(errorMessage);
    },
  });

  const handleAcknowledge = (alert: Alert) => {
    acknowledgeMutation.mutate(alert);
  };

  const handleResolve = (alert: Alert) => {
    resolveMutation.mutate(alert);
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Alerts</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Alerts</CardTitle>
          <CardDescription>
            Devices and interfaces currently in alert state
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Success Message */}
          {actionSuccess && (
            <div className="mb-4 p-3 bg-green-100 border border-green-300 text-green-800 rounded">
              {actionSuccess}
            </div>
          )}

          {/* Error Message */}
          {actionError && (
            <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded">
              {actionError}
            </div>
          )}

          {/* Query Error */}
          {queryError && (
            <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded">
              Failed to load alerts. Please refresh the page.
            </div>
          )}

          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex gap-4">
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 w-24 animate-pulse rounded-md bg-muted/50" />
                </div>
              ))}
            </div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No active alerts</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-center">Device</TableHead>
                  <TableHead className="text-center">IP Address</TableHead>
                  <TableHead className="text-center">Metric</TableHead>
                  <TableHead className="text-center">Current Value</TableHead>
                  <TableHead className="text-center">Remarks</TableHead>
                  <TableHead className="text-center">Severity</TableHead>
                  <TableHead className="text-center">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alerts.map((alert, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium text-center">
                      {alert.hostname}
                    </TableCell>
                    <TableCell className="text-center">{alert.ip_address}</TableCell>
                    <TableCell className="text-center">{alert.metric}</TableCell>
                    <TableCell className="text-center">{alert.current_value}</TableCell>
                    <TableCell className="text-center">{alert.threshold}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant={severityMap[alert.severity] || 'default'}>
                        {alert.severity}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex gap-2 justify-center">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAcknowledge(alert)}
                          disabled={acknowledgeMutation.isPending || resolveMutation.isPending}
                        >
                          {acknowledgeMutation.isPending ? "..." : "Acknowledge"}
                        </Button>
                        <Button
                          size="sm"
                          variant="default"
                          onClick={() => handleResolve(alert)}
                          disabled={acknowledgeMutation.isPending || resolveMutation.isPending}
                        >
                          {resolveMutation.isPending ? "..." : "Resolve"}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Alert History Section */}
      <Card>
        <CardHeader>
          <CardTitle>Alert History</CardTitle>
          <CardDescription>
            Historical record of all alerts with filtering and pagination
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex gap-4 mb-4 flex-wrap">
            <div className="flex-1 min-w-[150px]">
              <label className="text-sm font-medium mb-2 block">Severity</label>
              <Select value={historySeverityFilter} onValueChange={setHistorySeverityFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Severities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  <SelectItem value="Warning">Warning</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1 min-w-[150px]">
              <label className="text-sm font-medium mb-2 block">Alert Type</label>
              <Select value={historyAlertTypeFilter} onValueChange={setHistoryAlertTypeFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="cpu">CPU</SelectItem>
                  <SelectItem value="memory">Memory</SelectItem>
                  <SelectItem value="reachability">Reachability</SelectItem>
                  <SelectItem value="interface_status">Interface Status</SelectItem>
                  <SelectItem value="packet_drop">Packet Drop</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1 min-w-[150px]">
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select value={historyClearedFilter} onValueChange={setHistoryClearedFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="active">Active Only</SelectItem>
                  <SelectItem value="cleared">Cleared Only</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setHistoryPage(1);
                  setHistorySeverityFilter("all");
                  setHistoryAlertTypeFilter("all");
                  setHistoryClearedFilter("all");
                }}
              >
                Reset Filters
              </Button>
            </div>
          </div>

          {/* Alert History Table */}
          {isLoadingHistory ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex gap-4">
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                  <div className="h-4 flex-1 animate-pulse rounded-md bg-muted/50" />
                </div>
              ))}
            </div>
          ) : alertHistory.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">No alert history found</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-center">Alert Type</TableHead>
                    <TableHead className="text-center">Severity</TableHead>
                    <TableHead className="text-center">Triggered At</TableHead>
                    <TableHead className="text-center">Cleared At</TableHead>
                    <TableHead className="text-center">Metric Value</TableHead>
                    <TableHead className="text-center">Threshold</TableHead>
                    <TableHead className="text-center">Email Sent</TableHead>
                    <TableHead className="text-center">Action Taken</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alertHistory.map((historyItem) => (
                    <TableRow key={historyItem.id}>
                      <TableCell className="text-center capitalize">
                        {historyItem.alert_type.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant={severityMap[historyItem.severity as Alert['severity']] || 'default'}>
                          {historyItem.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        {new Date(historyItem.triggered_at+"Z").toLocaleString()}
                      </TableCell>
                      <TableCell className="text-center">
                        {historyItem.cleared_at ? (
                          <span className="text-green-600">
                            {new Date(historyItem.cleared_at+"Z").toLocaleString()}
                          </span>
                        ) : (
                          <Badge variant="destructive">Active</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        {historyItem.metric_value}
                      </TableCell>
                      <TableCell className="text-center">
                        {historyItem.threshold_value}
                      </TableCell>
                      <TableCell className="text-center">
                        {historyItem.email_sent ? (
                          <Badge variant="default">Yes</Badge>
                        ) : (
                          <Badge variant="outline">No</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        {historyItem.action_taken ? (
                          <span className="text-sm capitalize">{historyItem.action_taken}</span>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination Controls */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-muted-foreground">
                  Page {historyPage} • Showing {alertHistory.length} items
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                    disabled={historyPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setHistoryPage((p) => p + 1)}
                    disabled={alertHistory.length < historyPerPage}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

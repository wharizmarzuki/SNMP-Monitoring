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
import { CheckCircle } from "lucide-react";
import { queryApi, deviceApi } from "@/lib/api";
import { Alert } from "@/types";

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

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
            <p className="text-sm text-muted-foreground">Loading alerts...</p>
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
    </div>
  );
}

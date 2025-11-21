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
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Trash2, Plus, Loader2, Activity, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { deviceApi, configApi, healthApi } from "@/lib/api";
import { Recipient } from "@/types";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [newRecipient, setNewRecipient] = useState("");
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Discovery network configuration
  const [networkIp, setNetworkIp] = useState("192.168.254.1");
  const [subnet, setSubnet] = useState("27");

  // Fetch recipients
  const { data: recipients = [], error: recipientsError } = useQuery<Recipient[]>({
    queryKey: ["recipients"],
    queryFn: () => configApi.getRecipients(),
  });

  // Fetch system health
  const { data: healthData, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ["systemHealth"],
    queryFn: () => healthApi.getServices(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Add recipient mutation
  const addRecipientMutation = useMutation({
    mutationFn: (email: string) => configApi.addRecipient(email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recipients"] });
      setNewRecipient("");
      setActionError(null);
      setActionSuccess("Recipient added successfully");
      setTimeout(() => setActionSuccess(null), 3000);
    },
    onError: (error: any) => {
      console.error("Error adding recipient:", error);
      setActionSuccess(null);
      const errorMessage = error.message || "Failed to add recipient. Please try again.";
      setActionError(errorMessage);
    },
  });

  // Delete recipient mutation
  const deleteRecipientMutation = useMutation({
    mutationFn: (id: number) => configApi.deleteRecipient(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recipients"] });
      setActionError(null);
      setActionSuccess("Recipient removed successfully");
      setTimeout(() => setActionSuccess(null), 3000);
    },
    onError: (error: any) => {
      console.error("Error deleting recipient:", error);
      setActionSuccess(null);
      const errorMessage = error.message || "Failed to remove recipient. Please try again.";
      setActionError(errorMessage);
    },
  });

  // Discovery mutation
  const runDiscoveryMutation = useMutation({
    mutationFn: ({ network, subnet }: { network: string; subnet: string }) =>
      deviceApi.discover(network, subnet),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      setIsDiscovering(false);
      setActionError(null);
      setActionSuccess("Network discovery completed successfully");
      setTimeout(() => setActionSuccess(null), 3000);
    },
    onError: (error: any) => {
      console.error("Error running discovery:", error);
      setIsDiscovering(false);
      setActionSuccess(null);
      const errorMessage = error.message || "Failed to run network discovery. Please try again.";
      setActionError(errorMessage);
    },
  });

  const handleAddRecipient = () => {
    if (newRecipient && newRecipient.includes("@")) {
      addRecipientMutation.mutate(newRecipient);
    }
  };

  const handleRunDiscovery = () => {
    // Validate network IP
    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    if (!ipRegex.test(networkIp)) {
      setActionError("Invalid network IP address format");
      return;
    }

    // Validate subnet (CIDR notation)
    const subnetNum = parseInt(subnet);
    if (isNaN(subnetNum) || subnetNum < 0 || subnetNum > 32) {
      setActionError("Subnet must be a number between 0 and 32");
      return;
    }

    setActionError(null);
    setIsDiscovering(true);
    runDiscoveryMutation.mutate({ network: networkIp, subnet: subnet });
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
      </div>

      {/* Success Message - shown above tabs */}
      {actionSuccess && (
        <div className="p-3 bg-green-100 border border-green-300 text-green-800 rounded">
          {actionSuccess}
        </div>
      )}

      {/* Error Message - shown above tabs */}
      {actionError && (
        <div className="p-3 bg-red-100 border border-red-300 text-red-800 rounded">
          {actionError}
        </div>
      )}

      {/* Query Error for recipients */}
      {recipientsError && (
        <div className="p-3 bg-red-100 border border-red-300 text-red-800 rounded">
          Failed to load recipients. Please refresh the page.
        </div>
      )}

      <Tabs defaultValue="recipients" className="space-y-4">
        <TabsList>
          <TabsTrigger value="recipients">Alert Recipients</TabsTrigger>
          <TabsTrigger value="discovery">Discovery</TabsTrigger>
          <TabsTrigger value="health">System Health</TabsTrigger>
        </TabsList>

        {/* Alert Recipients Tab */}
        <TabsContent value="recipients" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Alert Recipients</CardTitle>
              <CardDescription>
                Manage email addresses that receive alert notifications. Note: Your user email is automatically included as a recipient and will be updated when you change your email in Profile Settings.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  type="email"
                  placeholder="email@example.com"
                  value={newRecipient}
                  onChange={(e) => setNewRecipient(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddRecipient()}
                />
                <Button onClick={handleAddRecipient}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add
                </Button>
              </div>

              {recipients.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No recipients configured
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email Address</TableHead>
                      <TableHead className="w-24">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recipients.map((recipient) => (
                      <TableRow key={recipient.email}>
                        <TableCell>{recipient.email}</TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              deleteRecipientMutation.mutate(recipient.id)
                            }
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Discovery Tab */}
        <TabsContent value="discovery" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Network Discovery</CardTitle>
              <CardDescription>
                Configure and trigger network device discovery
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Network IP Input */}
                <div className="space-y-2">
                  <label
                    htmlFor="network-ip"
                    className="text-sm font-medium"
                  >
                    Network IP Address
                  </label>
                  <Input
                    id="network-ip"
                    type="text"
                    placeholder="192.168.254.1"
                    value={networkIp}
                    onChange={(e) => setNetworkIp(e.target.value)}
                    disabled={isDiscovering}
                  />
                  <p className="text-xs text-muted-foreground">
                    Base IP address for the network to scan
                  </p>
                </div>

                {/* Subnet Input */}
                <div className="space-y-2">
                  <label
                    htmlFor="subnet"
                    className="text-sm font-medium"
                  >
                    Subnet Mask (CIDR)
                  </label>
                  <Input
                    id="subnet"
                    type="number"
                    placeholder="27"
                    min="0"
                    max="32"
                    value={subnet}
                    onChange={(e) => setSubnet(e.target.value)}
                    disabled={isDiscovering}
                  />
                  <p className="text-xs text-muted-foreground">
                    CIDR notation (e.g., 24 = /24, 27 = /27)
                  </p>
                </div>
              </div>

              {/* Example Info */}
              <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm">
                <p className="font-medium text-blue-900 mb-1">Example:</p>
                <p className="text-blue-800">
                  Network: <code className="bg-blue-100 px-1 rounded">192.168.1.0</code> with Subnet: <code className="bg-blue-100 px-1 rounded">24</code> will scan 192.168.1.0/24 (256 addresses)
                </p>
                <p className="text-blue-800 mt-1">
                  Network: <code className="bg-blue-100 px-1 rounded">192.168.254.1</code> with Subnet: <code className="bg-blue-100 px-1 rounded">27</code> will scan 192.168.254.1/27 (32 addresses)
                </p>
              </div>

              {/* Discovery Button */}
              <div className="flex items-center gap-4 pt-2">
                <Button
                  onClick={handleRunDiscovery}
                  disabled={isDiscovering}
                  size="lg"
                >
                  {isDiscovering ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Discovering...
                    </>
                  ) : (
                    "Run Network Discovery"
                  )}
                </Button>
                <p className="text-sm text-muted-foreground">
                  This will scan the configured network range for SNMP-enabled devices
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Health Tab */}
        <TabsContent value="health" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    System Health
                  </CardTitle>
                  <CardDescription>
                    Monitor the health of backend services and dependencies
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchHealth()}
                  disabled={healthLoading}
                >
                  <Loader2 className={`h-4 w-4 mr-2 ${healthLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <p className="text-sm text-muted-foreground">Loading health status...</p>
              ) : healthData ? (
                <div className="space-y-6">
                  {/* Overall Status */}
                  <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
                    {healthData.overall_status === "healthy" ? (
                      <CheckCircle2 className="h-6 w-6 text-green-600" />
                    ) : (
                      <AlertCircle className="h-6 w-6 text-amber-600" />
                    )}
                    <div>
                      <p className="font-semibold">
                        Overall Status:{" "}
                        <span
                          className={
                            healthData.overall_status === "healthy"
                              ? "text-green-600"
                              : "text-amber-600"
                          }
                        >
                          {healthData.overall_status === "healthy" ? "Healthy" : "Degraded"}
                        </span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Last checked: {new Date(healthData.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Services Status */}
                  <div>
                    <h3 className="text-sm font-semibold mb-3">Service Status</h3>
                    <div className="grid gap-4">
                      {healthData.services?.map((service: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start justify-between p-4 border rounded-lg"
                        >
                          <div className="flex items-start gap-3">
                            {service.status === "healthy" ? (
                              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                            ) : service.status === "disabled" ? (
                              <XCircle className="h-5 w-5 text-gray-400 mt-0.5" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                            )}
                            <div>
                              <p className="font-medium capitalize">{service.service}</p>
                              <p className="text-sm text-muted-foreground">
                                {service.message}
                              </p>
                              {service.status === "unhealthy" && (
                                <p className="text-xs text-red-600 mt-1">
                                  Action required: Check service configuration
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="flex flex-col items-end">
                            <span
                              className={`px-2 py-1 text-xs font-medium rounded ${
                                service.status === "healthy"
                                  ? "bg-green-100 text-green-800"
                                  : service.status === "disabled"
                                  ? "bg-gray-100 text-gray-800"
                                  : "bg-red-100 text-red-800"
                              }`}
                            >
                              {service.status}
                            </span>
                            {service.response_time_ms > 0 && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {service.response_time_ms}ms
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Environment Info */}
                  {healthData.environment && (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded">
                      <p className="text-sm text-blue-900">
                        <strong>Environment:</strong> {healthData.environment}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-red-600">
                  Failed to load health status. Please try refreshing.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

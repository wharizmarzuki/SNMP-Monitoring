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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Trash2, Plus, Save, Loader2 } from "lucide-react";
import { deviceApi, configApi, queryApi } from "@/lib/api";
import { Device, Recipient, InterfaceMetric } from "@/types";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [newRecipient, setNewRecipient] = useState("");
  const [selectedDeviceForInterface, setSelectedDeviceForInterface] =
    useState("");
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Discovery network configuration
  const [networkIp, setNetworkIp] = useState("192.168.254.1");
  const [subnet, setSubnet] = useState("27");

  // Fetch recipients
  const { data: recipientsData, error: recipientsError } = useQuery<{ data: Recipient[] }>({
    queryKey: ["recipients"],
    queryFn: () => configApi.getRecipients(),
  });

  // Fetch devices
  const { data: devicesData } = useQuery<{ data: Device[] }>({
    queryKey: ["devices"],
    queryFn: () => deviceApi.getAll(),
  });

  // Fetch interfaces for selected device
  const { data: interfacesData } = useQuery<{ data: InterfaceMetric[] }>({
    queryKey: ["deviceInterfaces", selectedDeviceForInterface],
    queryFn: () => queryApi.getDeviceInterfaces(selectedDeviceForInterface),
    enabled: !!selectedDeviceForInterface,
  });

  const recipients = recipientsData?.data || [];
  const devices = devicesData?.data || [];
  const interfaces = interfacesData?.data || [];

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
    mutationFn: (email: string) => configApi.deleteRecipient(email),
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

  // Update threshold mutation
  const updateInterfaceThresholdMutation = useMutation({
    mutationFn: ({
      ip,
      ifIndex,
      threshold,
    }: {
      ip: string;
      ifIndex: number;
      threshold: number;
    }) => deviceApi.updateInterfaceThreshold(ip, ifIndex, threshold),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["deviceInterfaces", selectedDeviceForInterface],
      });
      setActionError(null);
      setActionSuccess("Interface threshold updated successfully");
      setTimeout(() => setActionSuccess(null), 3000);
    },
    onError: (error: any) => {
      console.error("Error updating interface threshold:", error);
      setActionSuccess(null);
      const errorMessage = error.message || "Failed to update interface threshold. Please try again.";
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
          <TabsTrigger value="interfaces">Interface Thresholds</TabsTrigger>
          <TabsTrigger value="discovery">Discovery</TabsTrigger>
        </TabsList>

        {/* Alert Recipients Tab */}
        <TabsContent value="recipients" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Alert Recipients</CardTitle>
              <CardDescription>
                Manage email addresses that receive alert notifications
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
                              deleteRecipientMutation.mutate(recipient.email)
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

        {/* Interface Thresholds Tab */}
        <TabsContent value="interfaces" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Interface Thresholds</CardTitle>
              <CardDescription>
                Configure packet drop thresholds for network interfaces
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Select Device</label>
                <Select
                  value={selectedDeviceForInterface}
                  onValueChange={setSelectedDeviceForInterface}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a device" />
                  </SelectTrigger>
                  <SelectContent>
                    {devices.map((device) => (
                      <SelectItem
                        key={device.ip_address}
                        value={device.ip_address}
                      >
                        {device.hostname} ({device.ip_address})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedDeviceForInterface && (
                <>
                  {interfaces.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No interfaces found
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Interface Name</TableHead>
                          <TableHead>Discard Rate Threshold (%)</TableHead>
                          <TableHead>Action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {interfaces.map((iface) => (
                          <InterfaceThresholdRow
                            key={iface.if_index}
                            interface={iface}
                            deviceIp={selectedDeviceForInterface}
                            onSave={(threshold) =>
                              updateInterfaceThresholdMutation.mutate({
                                ip: selectedDeviceForInterface,
                                ifIndex: iface.if_index,
                                threshold,
                              })
                            }
                          />
                        ))}
                      </TableBody>
                    </Table>
                  )}
                  {selectedDeviceForInterface && interfaces.length > 0 && (
                    <p className="text-xs text-muted-foreground mt-4">
                      Discard rate threshold: Percentage of total traffic (0-100%) that triggers an alert when exceeded.
                      Recommended values: 0.01% (critical links), 0.1% (normal), 1.0% (tolerant).
                    </p>
                  )}
                </>
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
      </Tabs>
    </div>
  );
}

// Interface Threshold Row Component
function InterfaceThresholdRow({
  interface: iface,
  deviceIp,
  onSave,
}: {
  interface: InterfaceMetric;
  deviceIp: string;
  onSave: (threshold: number) => void;
}) {
  const [threshold, setThreshold] = useState(
    iface.packet_drop_threshold?.toString() || "0.1"
  );

  return (
    <TableRow>
      <TableCell className="font-medium">{iface.if_name}</TableCell>
      <TableCell>
        <Input
          type="number"
          min="0"
          max="100"
          step="0.1"
          placeholder="0.1"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          className="w-32"
        />
      </TableCell>
      <TableCell>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onSave(parseFloat(threshold))}
        >
          <Save className="h-4 w-4 mr-2" />
          Save
        </Button>
      </TableCell>
    </TableRow>
  );
}

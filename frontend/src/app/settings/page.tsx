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
import { Trash2, Plus, Loader2 } from "lucide-react";
import { deviceApi, configApi } from "@/lib/api";
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
      </Tabs>
    </div>
  );
}

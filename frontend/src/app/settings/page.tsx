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

  // Fetch recipients
  const { data: recipientsData } = useQuery<{ data: Recipient[] }>({
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
    },
  });

  // Delete recipient mutation
  const deleteRecipientMutation = useMutation({
    mutationFn: (email: string) => configApi.deleteRecipient(email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recipients"] });
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
    },
  });

  // Discovery mutation
  const runDiscoveryMutation = useMutation({
    mutationFn: () => deviceApi.discover(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      setIsDiscovering(false);
    },
    onError: () => {
      setIsDiscovering(false);
    },
  });

  const handleAddRecipient = () => {
    if (newRecipient && newRecipient.includes("@")) {
      addRecipientMutation.mutate(newRecipient);
    }
  };

  const handleRunDiscovery = () => {
    setIsDiscovering(true);
    runDiscoveryMutation.mutate();
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
      </div>

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
                          <TableHead>Packet Drop Threshold</TableHead>
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
                Manually trigger network device discovery
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={handleRunDiscovery} disabled={isDiscovering}>
                {isDiscovering ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Discovering...
                  </>
                ) : (
                  "Run Network Discovery Now"
                )}
              </Button>
              <p className="text-sm text-muted-foreground mt-2">
                This will scan the network for new devices and update the device
                list.
              </p>
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
    iface.packet_drop_threshold?.toString() || "100"
  );

  return (
    <TableRow>
      <TableCell className="font-medium">{iface.if_name}</TableCell>
      <TableCell>
        <Input
          type="number"
          min="0"
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

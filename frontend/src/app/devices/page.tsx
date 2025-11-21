"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StatusDot } from "@/components/StatusBadge";
import { deviceApi, pollingApi } from "@/lib/api";
import { Device } from "@/types";
import { Plus, Trash2, Loader2, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";

export default function DevicesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Add Device modal state
  const [addDeviceOpen, setAddDeviceOpen] = useState(false);
  const [newDeviceIp, setNewDeviceIp] = useState("");
  const [newDeviceHostname, setNewDeviceHostname] = useState("");
  const [validationStatus, setValidationStatus] = useState<
    "idle" | "validating" | "success" | "error"
  >("idle");
  const [validationMessage, setValidationMessage] = useState("");

  // Delete confirmation state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deviceToDelete, setDeviceToDelete] = useState<Device | null>(null);

  const { data: devicesData, isLoading } = useQuery<Device[]>({
    queryKey: ["devices"],
    queryFn: () => deviceApi.getAll(),
  });

  const devices = devicesData || [];

  // Add device mutation
  const addDeviceMutation = useMutation({
    mutationFn: (data: { ip_address: string; hostname?: string }) =>
      deviceApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      queryClient.invalidateQueries({ queryKey: ["network-summary"] });
      setAddDeviceOpen(false);
      setNewDeviceIp("");
      setNewDeviceHostname("");
      setValidationStatus("idle");
      setValidationMessage("");
    },
    onError: (error: any) => {
      setValidationStatus("error");
      setValidationMessage(error.message || "Failed to add device");
    },
  });

  // Delete device mutation
  const deleteDeviceMutation = useMutation({
    mutationFn: (ip: string) => deviceApi.delete(ip),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      queryClient.invalidateQueries({ queryKey: ["network-summary"] });
      setDeleteDialogOpen(false);
      setDeviceToDelete(null);
    },
    onError: (error: any) => {
      console.error("Failed to delete device:", error);
      alert(`Failed to delete device: ${error.message || "Unknown error"}`);
    },
  });

  // Manual polling mutation - triggers poll for ALL devices
  const manualPollMutation = useMutation({
    mutationFn: () => pollingApi.triggerPoll(),
    onSuccess: () => {
      // Wait 3 seconds for polling to complete, then refresh data
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["devices"] });
        queryClient.invalidateQueries({ queryKey: ["network-summary"] });
      }, 3000);
    },
    onError: (error: any) => {
      console.error("Failed to trigger poll:", error);
      alert(`Failed to refresh data: ${error.message || "Unknown error"}`);
    },
  });

  const handleValidateDevice = async () => {
    if (!newDeviceIp) {
      setValidationMessage("Please enter an IP address");
      setValidationStatus("error");
      return;
    }

    // Basic IP validation
    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    if (!ipRegex.test(newDeviceIp)) {
      setValidationMessage("Invalid IP address format");
      setValidationStatus("error");
      return;
    }

    setValidationStatus("validating");
    setValidationMessage("Validating SNMP connectivity...");

    try {
      await deviceApi.create({
        ip_address: newDeviceIp,
        hostname: newDeviceHostname || undefined,
        validate: true,
      });
      setValidationStatus("success");
      setValidationMessage("Device validated and added successfully!");
    } catch (error: any) {
      setValidationStatus("error");
      setValidationMessage(
        error.message || "SNMP validation failed. Device may be unreachable."
      );
    }
  };

  const handleAddDevice = () => {
    if (validationStatus === "success") {
      // Already added during validation
      setAddDeviceOpen(false);
      setNewDeviceIp("");
      setNewDeviceHostname("");
      setValidationStatus("idle");
      setValidationMessage("");
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    } else {
      handleValidateDevice();
    }
  };

  const handleDeleteClick = (device: Device, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click navigation
    setDeviceToDelete(device);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (deviceToDelete) {
      deleteDeviceMutation.mutate(deviceToDelete.ip_address);
    }
  };

  const handleRowClick = (ip: string) => {
    router.push(`/devices/${ip}`);
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Devices</h2>

        <div className="flex gap-2">
          {/* Refresh Data Button */}
          <Button
            variant="outline"
            onClick={() => manualPollMutation.mutate()}
            disabled={manualPollMutation.isPending}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${manualPollMutation.isPending ? 'animate-spin' : ''}`} />
            {manualPollMutation.isPending ? "Polling..." : "Refresh Data"}
          </Button>

          {/* Add Device Button */}
          <Dialog open={addDeviceOpen} onOpenChange={setAddDeviceOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Device
              </Button>
            </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Device</DialogTitle>
              <DialogDescription>
                Add a device manually with SNMP validation. The device must be
                reachable and have SNMP enabled.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="ip_address">IP Address *</Label>
                <Input
                  id="ip_address"
                  placeholder="192.168.1.100"
                  value={newDeviceIp}
                  onChange={(e) => {
                    setNewDeviceIp(e.target.value);
                    setValidationStatus("idle");
                    setValidationMessage("");
                  }}
                  disabled={
                    validationStatus === "validating" ||
                    validationStatus === "success"
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="hostname">Hostname (Optional)</Label>
                <Input
                  id="hostname"
                  placeholder="router-01"
                  value={newDeviceHostname}
                  onChange={(e) => setNewDeviceHostname(e.target.value)}
                  disabled={
                    validationStatus === "validating" ||
                    validationStatus === "success"
                  }
                />
                <p className="text-xs text-muted-foreground">
                  If not provided, will be fetched via SNMP
                </p>
              </div>

              {/* Validation Status */}
              {validationStatus !== "idle" && (
                <div
                  className={`flex items-start gap-2 p-3 rounded ${
                    validationStatus === "validating"
                      ? "bg-blue-50 border border-blue-200"
                      : validationStatus === "success"
                      ? "bg-green-50 border border-green-200"
                      : "bg-red-50 border border-red-200"
                  }`}
                >
                  {validationStatus === "validating" && (
                    <Loader2 className="h-4 w-4 mt-0.5 text-blue-600 animate-spin flex-shrink-0" />
                  )}
                  {validationStatus === "success" && (
                    <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
                  )}
                  {validationStatus === "error" && (
                    <AlertCircle className="h-4 w-4 mt-0.5 text-red-600 flex-shrink-0" />
                  )}
                  <p
                    className={`text-sm ${
                      validationStatus === "validating"
                        ? "text-blue-900"
                        : validationStatus === "success"
                        ? "text-green-900"
                        : "text-red-900"
                    }`}
                  >
                    {validationMessage}
                  </p>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setAddDeviceOpen(false);
                  setNewDeviceIp("");
                  setNewDeviceHostname("");
                  setValidationStatus("idle");
                  setValidationMessage("");
                }}
                disabled={validationStatus === "validating"}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddDevice}
                disabled={
                  validationStatus === "validating" ||
                  validationStatus === "success" ||
                  !newDeviceIp
                }
              >
                {validationStatus === "validating" ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Validating...
                  </>
                ) : validationStatus === "success" ? (
                  "Added!"
                ) : (
                  "Validate & Add"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monitored Devices</CardTitle>
          <CardDescription>
            Click on a device to view detailed metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading devices...</p>
          ) : devices.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No devices found. Use network discovery or add devices manually.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Hostname</TableHead>
                  <TableHead>IP Address</TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead className="w-24">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {devices.map((device) => (
                  <TableRow
                    key={device.ip_address}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleRowClick(device.ip_address)}
                  >
                    <TableCell>
                      <StatusDot status={device.is_reachable ? "up" : "down"} />
                    </TableCell>
                    <TableCell className="font-medium">
                      {device.hostname}
                    </TableCell>
                    <TableCell>{device.ip_address}</TableCell>
                    <TableCell>{device.vendor}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => handleDeleteClick(device, e)}
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

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Device?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete{" "}
              <span className="font-semibold">
                {deviceToDelete?.hostname} ({deviceToDelete?.ip_address})
              </span>
              ? This will remove all associated metrics and alerts. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteDeviceMutation.isPending}
            >
              {deleteDeviceMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

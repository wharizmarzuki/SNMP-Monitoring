"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
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
import { StatusDot } from "@/components/StatusBadge";
import { deviceApi } from "@/lib/api";
import { Device } from "@/types";

export default function DevicesPage() {
  const router = useRouter();

  const { data: devicesData, isLoading } = useQuery<Device[]>({
    queryKey: ["devices"],
    queryFn: () => deviceApi.getAll(),
  });

  const devices = devicesData || [];

  const handleRowClick = (ip: string) => {
    router.push(`/devices/${ip}`);
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Devices</h2>
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
            <p className="text-sm text-muted-foreground">No devices found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Hostname</TableHead>
                  <TableHead>IP Address</TableHead>
                  <TableHead>Vendor</TableHead>
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

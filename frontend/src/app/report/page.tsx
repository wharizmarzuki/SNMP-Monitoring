"use client";

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, FileText } from 'lucide-react';
import { deviceApi, queryApi } from '@/lib/api';
import { Device, HistoryRecord } from '@/types';

export default function ReportPage() {
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [reportGenerated, setReportGenerated] = useState(false);

  // Fetch all devices for dropdown
  const { data: devicesData } = useQuery<Device[]>({
    queryKey: ['devices'],
    queryFn: () => deviceApi.getAll(),
  });

  // Fetch history data when report is generated
  const { data: historyData, isLoading } = useQuery<HistoryRecord[]>({
    queryKey: ['deviceHistory', selectedDevice, startDate, endDate],
    queryFn: () => queryApi.getHistory(selectedDevice, startDate, endDate),
    enabled: reportGenerated && !!selectedDevice && !!startDate && !!endDate,
  });

  const devices = devicesData || [];
  const historyRecords = historyData || [];

  const handleGenerateReport = () => {
    if (selectedDevice && startDate && endDate) {
      setReportGenerated(true);
    }
  };

  const handleExportCSV = () => {
    if (historyRecords.length === 0) return;

    // Get all unique keys from the records
    const headers = Object.keys(historyRecords[0]);

    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...historyRecords.map(record =>
        headers.map(header => {
          const value = record[header];
          // Escape commas and quotes in values
          return typeof value === 'string' && value.includes(',')
            ? `"${value.replace(/"/g, '""')}"`
            : value;
        }).join(',')
      )
    ].join('\n');

    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `report_${selectedDevice}_${format(new Date(), 'yyyy-MM-dd')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Reports</h2>
      </div>

      {/* Report Builder Form */}
      <Card>
        <CardHeader>
          <CardTitle>Report Builder</CardTitle>
          <CardDescription>
            Select a device and date range to generate a historical report
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Device</label>
              <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                <SelectTrigger>
                  <SelectValue placeholder="Select device" />
                </SelectTrigger>
                <SelectContent>
                  {devices.map((device) => (
                    <SelectItem key={device.ip_address} value={device.ip_address}>
                      {device.hostname}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">&nbsp;</label>
              <Button
                onClick={handleGenerateReport}
                disabled={!selectedDevice || !startDate || !endDate}
                className="w-full"
              >
                <FileText className="h-4 w-4 mr-2" />
                Generate
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report Results */}
      {reportGenerated && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Report Data</CardTitle>
                <CardDescription>
                  Historical metrics for {devices.find(d => d.ip_address === selectedDevice)?.hostname}
                </CardDescription>
              </div>
              <Button
                onClick={handleExportCSV}
                disabled={historyRecords.length === 0}
                variant="outline"
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading report data...</p>
            ) : historyRecords.length === 0 ? (
              <p className="text-sm text-muted-foreground">No data available for the selected period</p>
            ) : (
              <div className="max-h-96 overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>CPU Utilization (%)</TableHead>
                      <TableHead>Memory Utilization (%)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {historyRecords.map((record, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          {new Date(record.timestamp).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          {record.cpu_utilization?.toFixed(2) || 'N/A'}
                        </TableCell>
                        <TableCell>
                          {record.memory_utilization?.toFixed(2) || 'N/A'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

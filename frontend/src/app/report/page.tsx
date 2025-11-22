"use client";

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Download, FileText, Activity, HardDrive, AlertTriangle, Clock } from 'lucide-react';
import { reportApi } from '@/lib/api';
import type {
  NetworkThroughputDatapoint,
  ReportDeviceUtilizationDatapoint,
  PacketDropRecord,
  UptimeSummaryResponse,
  AvailabilityRecord
} from '@/types/report';

// Aggregate data to max N points by taking evenly spaced samples
function aggregateData<T>(data: T[], maxPoints: number = 10): T[] {
  if (data.length <= maxPoints) return data;

  const step = Math.ceil(data.length / maxPoints);
  const result: T[] = [];

  for (let i = 0; i < data.length; i += step) {
    result.push(data[i]);
  }

  return result;
}

export default function ReportPage() {
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [reportGenerated, setReportGenerated] = useState(false);

  // Calculate default date range (7 days ago to today)
  React.useEffect(() => {
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 7);

    setStartDate(format(sevenDaysAgo, 'yyyy-MM-dd'));
    setEndDate(format(today, 'yyyy-MM-dd'));
  }, []);

  // Prepare datetime strings with time component
  const getDateTimeString = (dateStr: string, isStart: boolean) => {
    if (!dateStr) return '';
    return isStart ? `${dateStr}T00:00:00` : `${dateStr}T23:59:59`;
  };

  const startDateTime = getDateTimeString(startDate, true);
  const endDateTime = getDateTimeString(endDate, false);

  // Fetch all report data
  const { data: throughputData, isLoading: loadingThroughput } = useQuery<NetworkThroughputDatapoint[]>({
    queryKey: ['reportThroughput', startDateTime, endDateTime],
    queryFn: () => reportApi.getNetworkThroughput(startDateTime, endDateTime),
    enabled: reportGenerated && !!startDateTime && !!endDateTime,
  });

  const { data: utilizationData, isLoading: loadingUtilization } = useQuery<ReportDeviceUtilizationDatapoint[]>({
    queryKey: ['reportUtilization', startDateTime, endDateTime],
    queryFn: () => reportApi.getDeviceUtilization(startDateTime, endDateTime),
    enabled: reportGenerated && !!startDateTime && !!endDateTime,
  });

  const { data: packetDropData, isLoading: loadingPacketDrops } = useQuery<PacketDropRecord[]>({
    queryKey: ['reportPacketDrops', startDateTime, endDateTime],
    queryFn: () => reportApi.getPacketDrops(startDateTime, endDateTime),
    enabled: reportGenerated && !!startDateTime && !!endDateTime,
  });

  const { data: uptimeSummary, isLoading: loadingUptime } = useQuery<UptimeSummaryResponse>({
    queryKey: ['reportUptime', startDateTime, endDateTime],
    queryFn: () => reportApi.getUptimeSummary(startDateTime, endDateTime),
    enabled: reportGenerated && !!startDateTime && !!endDateTime,
  });

  const { data: availabilityData, isLoading: loadingAvailability } = useQuery<AvailabilityRecord[]>({
    queryKey: ['reportAvailability', startDateTime, endDateTime],
    queryFn: () => reportApi.getAvailability(startDateTime, endDateTime),
    enabled: reportGenerated && !!startDateTime && !!endDateTime,
  });

  const isLoading = loadingThroughput || loadingUtilization || loadingPacketDrops || loadingUptime || loadingAvailability;

  const handleGenerateReport = () => {
    if (startDate && endDate) {
      setReportGenerated(true);
    }
  };

  const handleExportPDF = async () => {
    const reportElement = document.getElementById('network-report');
    if (!reportElement) return;

    try {
      const canvas = await html2canvas(reportElement, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');

      const pdf = new jsPDF('portrait', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pdfWidth;
      const imgHeight = (canvas.height * pdfWidth) / canvas.width;

      let heightLeft = imgHeight;
      let position = 0;

      // Add first page
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pdfHeight;

      // Add additional pages if content is longer
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pdfHeight;
      }

      pdf.save(`network-report-${startDate}-to-${endDate}.pdf`);
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  };

  // Aggregate and format throughput data (max 10 points)
  const formattedThroughputData = React.useMemo(() => {
    if (!throughputData) return [];
    const aggregated = aggregateData(throughputData, 10);
    return aggregated.map(d => ({
      time: format(new Date(d.timestamp), 'MMM dd HH:mm'),
      inbound: parseFloat((d.total_inbound_bps / 1_000_000).toFixed(2)), // Convert to Mbps
      outbound: parseFloat((d.total_outbound_bps / 1_000_000).toFixed(2)),
    }));
  }, [throughputData]);

  // Aggregate and format utilization data (max 10 points)
  const formattedUtilizationData = React.useMemo(() => {
    if (!utilizationData) return [];
    const aggregated = aggregateData(utilizationData, 10);
    return aggregated.map(d => ({
      time: format(new Date(d.timestamp), 'MMM dd HH:mm'),
      cpu: parseFloat(d.avg_cpu_utilization.toFixed(2)),
      memory: parseFloat(d.avg_memory_utilization.toFixed(2)),
    }));
  }, [utilizationData]);

  // Format packet drop data with smart x-axis domain
  const formattedPacketDropData = React.useMemo(() => {
    if (!packetDropData) return [];
    return packetDropData.map(d => ({
      device: d.device_hostname,
      rate: parseFloat(d.discard_rate_pct.toFixed(4)),
    }));
  }, [packetDropData]);

  // Calculate smart domain for packet drop chart
  const packetDropDomain = React.useMemo(() => {
    if (formattedPacketDropData.length === 0) return [0, 1];

    const maxRate = Math.max(...formattedPacketDropData.map(d => d.rate));

    if (maxRate < 1) return [0, 1];
    if (maxRate < 10) return [0, 10];
    if (maxRate < 100) return [0, 100];
    return [0, Math.ceil(maxRate / 100) * 100];
  }, [formattedPacketDropData]);

  // Get availability color
  const getAvailabilityColor = (pct: number) => {
    if (pct >= 99) return 'text-green-600';
    if (pct >= 95) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Network Report</h2>
      </div>

      {/* Report Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Report Configuration</CardTitle>
          <CardDescription>
            Select date range to generate comprehensive network report
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
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

            <Button
              onClick={handleGenerateReport}
              disabled={!startDate || !endDate}
            >
              <FileText className="h-4 w-4 mr-2" />
              Generate Report
            </Button>

            {reportGenerated && (
              <Button
                onClick={handleExportPDF}
                variant="outline"
                disabled={isLoading}
              >
                <Download className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Report Content */}
      {reportGenerated && (
        <div id="network-report" className="space-y-4">
          {/* Report Header for PDF */}
          <div className="bg-white p-6 rounded-lg border">
            <h1 className="text-2xl font-bold">Network Performance Report</h1>
            <p className="text-muted-foreground mt-1">
              Period: {startDate} to {endDate}
            </p>
            <p className="text-sm text-muted-foreground">
              Generated: {format(new Date(), 'PPpp')}
            </p>
          </div>

          {isLoading ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">Loading report data...</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ gridTemplateRows: 'repeat(2, minmax(300px, 1fr))' }}>
              {/* Section 1: Network Bandwidth (Top-Left) */}
              <Card className="lg:col-span-1">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Activity className="h-4 w-4" />
                    Network Bandwidth
                  </CardTitle>
                  <CardDescription className="text-xs">Total throughput (Mbps)</CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  {formattedThroughputData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <LineChart data={formattedThroughputData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="time"
                          tick={{ fontSize: 10 }}
                          angle={-45}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: '12px' }} />
                        <Line type="monotone" dataKey="inbound" stroke="#3b82f6" name="Inbound" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="outbound" stroke="#10b981" name="Outbound" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">No throughput data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Section 2: CPU & Memory Utilization (Top-Middle) */}
              <Card className="lg:col-span-1">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <HardDrive className="h-4 w-4" />
                    CPU & Memory Utilization
                  </CardTitle>
                  <CardDescription className="text-xs">Average utilization (%)</CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  {formattedUtilizationData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <AreaChart data={formattedUtilizationData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="time"
                          tick={{ fontSize: 10 }}
                          angle={-45}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: '12px' }} />
                        <Area type="monotone" dataKey="cpu" stackId="1" stroke="#f97316" fill="#fb923c" name="CPU" />
                        <Area type="monotone" dataKey="memory" stackId="2" stroke="#3b82f6" fill="#60a5fa" name="Memory" />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">No utilization data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Section 5: Device Availability (Right Tall - spans 2 rows) */}
              <Card className="lg:col-span-1 lg:row-span-2">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Clock className="h-4 w-4" />
                    Device Availability
                  </CardTitle>
                  <CardDescription className="text-xs">Uptime metrics for all devices</CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  {availabilityData && availabilityData.length > 0 ? (
                    <div className="max-h-[580px] overflow-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="text-xs">Device</TableHead>
                            <TableHead className="text-xs">Availability</TableHead>
                            <TableHead className="text-xs">Avg Uptime</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {availabilityData.map((record, index) => (
                            <TableRow key={index}>
                              <TableCell className="py-2">
                                <div className="font-medium text-sm">{record.device_hostname}</div>
                                <div className="text-xs text-muted-foreground">{record.device_ip}</div>
                              </TableCell>
                              <TableCell className="py-2">
                                <span className={`font-semibold text-sm ${getAvailabilityColor(record.availability_pct)}`}>
                                  {record.availability_pct.toFixed(2)}%
                                </span>
                              </TableCell>
                              <TableCell className="py-2 text-sm">
                                {record.avg_uptime_days.toFixed(1)} days
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">No availability data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Section 3: Packet Drop Rate (Bottom-Left) */}
              <Card className="lg:col-span-1">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <AlertTriangle className="h-4 w-4" />
                    Packet Drop Rate
                  </CardTitle>
                  <CardDescription className="text-xs">Top 10 devices by discard rate</CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  {formattedPacketDropData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={formattedPacketDropData} layout="vertical" margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          type="number"
                          tick={{ fontSize: 11 }}
                          domain={packetDropDomain}
                          tickFormatter={(value) => value.toFixed(value < 1 ? 3 : 0)}
                        />
                        <YAxis dataKey="device" type="category" width={80} tick={{ fontSize: 10 }} />
                        <Tooltip formatter={(value: number) => value.toFixed(4) + '%'} />
                        <Bar dataKey="rate" fill="#ef4444" name="Discard Rate %" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">No packet drops detected</p>
                  )}
                </CardContent>
              </Card>

              {/* Section 4: System Uptime (Bottom-Middle) */}
              <Card className="lg:col-span-1">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Clock className="h-4 w-4" />
                    System Uptime Summary
                  </CardTitle>
                  <CardDescription className="text-xs">Network uptime statistics</CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  {uptimeSummary ? (
                    <div className="space-y-3">
                      <div className="border rounded-lg p-3">
                        <div className="text-xs text-muted-foreground">Average Network Uptime</div>
                        <div className="text-xl font-bold mt-1">
                          {uptimeSummary.avg_uptime_days.toFixed(1)} days
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="border rounded-lg p-3">
                          <div className="text-xs text-muted-foreground">Longest Uptime</div>
                          <div className="font-semibold mt-1 text-green-600 text-sm">
                            {uptimeSummary.longest_uptime.hostname}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {uptimeSummary.longest_uptime.uptime_days.toFixed(1)} days
                          </div>
                        </div>

                        <div className="border rounded-lg p-3">
                          <div className="text-xs text-muted-foreground">Recently Rebooted</div>
                          <div className="font-semibold mt-1 text-orange-600 text-sm">
                            {uptimeSummary.recently_rebooted.hostname}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {uptimeSummary.recently_rebooted.uptime_days.toFixed(1)} days ago
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">No uptime data available</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

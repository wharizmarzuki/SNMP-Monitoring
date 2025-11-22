import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface ChartSkeletonProps {
  height?: string;
  showTitle?: boolean;
}

export function ChartSkeleton({ height = "h-[400px]", showTitle = true }: ChartSkeletonProps) {
  return (
    <Card>
      {showTitle && (
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </CardHeader>
      )}
      <CardContent>
        <div className={`${height} flex items-end gap-2 p-4`}>
          {/* Simulated bar chart */}
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton
              key={i}
              className="flex-1"
              style={{ height: `${Math.random() * 60 + 40}%` }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

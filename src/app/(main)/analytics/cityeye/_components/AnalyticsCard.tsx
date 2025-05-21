import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AnalyticsCardProps {
  title: string;
  children?: React.ReactNode; // To allow content later
}

export default function AnalyticsCard({ title, children }: AnalyticsCardProps) {
  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow duration-300">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="min-h-[200px] flex items-center justify-center">
        {/* Content will go here later */}
        {children || <p className="text-sm text-gray-400">No data yet</p>}
      </CardContent>
    </Card>
  );
}

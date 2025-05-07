// File: app/(main)/customers/components/StatsCard.tsx
interface StatsCardProps {
    title: string
    value: number | string
    colorClass?: string
  }
  
  export default function StatsCard({ title, value, colorClass = '' }: StatsCardProps) {
    return (
      <div className="border p-4 rounded shadow-sm">
        <p className="text-sm text-muted-foreground">{title}</p>
        <h3 className={`text-2xl font-semibold ${colorClass}`}>{value}</h3>
      </div>
    )
  }
interface StatCardProps {
  label: string;
  value: string | number;
  color?: string;
}

export default function StatCard({ label, value, color = "text-slate-200" }: StatCardProps) {
  return (
    <div className="bg-ict-panel rounded-lg p-4 border border-slate-700">
      <div className="text-xs uppercase tracking-wider text-slate-400 mb-1">{label}</div>
      <div className={`text-xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

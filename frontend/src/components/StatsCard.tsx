import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  subtitle?: string;
}

const colorClasses = {
  blue: 'text-twitter-blue bg-twitter-blue/10',
  green: 'text-green-500 bg-green-500/10',
  yellow: 'text-yellow-500 bg-yellow-500/10',
  red: 'text-red-500 bg-red-500/10',
  purple: 'text-purple-500 bg-purple-500/10',
};

export default function StatsCard({ title, value, icon: Icon, color = 'blue', subtitle }: StatsCardProps) {
  return (
    <div className="bg-[#192734] rounded-xl p-6 border border-[#38444d]">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

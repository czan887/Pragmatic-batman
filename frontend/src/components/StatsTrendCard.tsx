import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { TrendChange } from '../types';

interface StatsTrendCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  trend?: TrendChange;
  subtitle?: string;
}

const colorClasses = {
  blue: 'text-twitter-blue bg-twitter-blue/10',
  green: 'text-green-500 bg-green-500/10',
  yellow: 'text-yellow-500 bg-yellow-500/10',
  red: 'text-red-500 bg-red-500/10',
  purple: 'text-purple-500 bg-purple-500/10',
};

const trendColors = {
  up: 'text-green-500',
  down: 'text-red-500',
  same: 'text-gray-500',
};

const TrendIcon = ({ direction }: { direction: 'up' | 'down' | 'same' }) => {
  if (direction === 'up') return <TrendingUp className="w-4 h-4" />;
  if (direction === 'down') return <TrendingDown className="w-4 h-4" />;
  return <Minus className="w-4 h-4" />;
};

export default function StatsTrendCard({
  title,
  value,
  icon: Icon,
  color = 'blue',
  trend,
  subtitle
}: StatsTrendCardProps) {
  return (
    <div className="bg-[#192734] rounded-xl p-6 border border-[#38444d]">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">
            {value.toLocaleString()}
          </p>
          {trend && (
            <div className={`flex items-center gap-1 mt-2 ${trendColors[trend.direction]}`}>
              <TrendIcon direction={trend.direction} />
              <span className="text-sm font-medium">
                {trend.direction === 'same' ? '0%' : `${Math.abs(trend.percentage).toFixed(1)}%`}
              </span>
              <span className="text-xs text-gray-500">vs previous</span>
            </div>
          )}
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard,
  Users,
  ListTodo,
  ScrollText,
  Settings,
  Twitter,
  UserPlus,
  Link,
  Hash,
  UserCog,
  RefreshCw,
  Bot,
  BarChart3,
  LucideIcon,
} from 'lucide-react';
import { profilesApi } from '../api/client';

type NavItem =
  | { to: string; icon: LucideIcon; label: string; type?: never }
  | { type: 'divider'; label: string; to?: never; icon?: never };

const navItems: NavItem[] = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/profiles', icon: Users, label: 'Profiles' },
  { to: '/tasks', icon: ListTodo, label: 'Tasks' },
  { to: '/stats', icon: BarChart3, label: 'Statistics' },
  { type: 'divider', label: 'Bot Actions' },
  { to: '/bot', icon: Bot, label: 'AI Bot' },
  { to: '/user-actions', icon: UserPlus, label: 'User Actions' },
  { to: '/post-actions', icon: Link, label: 'Post Actions' },
  { to: '/hashtag-actions', icon: Hash, label: 'Hashtag Actions' },
  { to: '/account-actions', icon: UserCog, label: 'Account Actions' },
  { type: 'divider', label: 'System' },
  { to: '/logs', icon: ScrollText, label: 'Logs' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  const { data: profiles, isLoading: profilesLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const profileCount = profiles?.length ?? 0;
  const groupCounts = profiles?.reduce((acc, p) => {
    const group = p.group_name || 'Ungrouped';
    acc[group] = (acc[group] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) ?? {};

  return (
    <div className="w-64 bg-[#192734] border-r border-[#38444d] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[#38444d]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-twitter-blue flex items-center justify-center">
            <Twitter className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white">Twitter Bot</h1>
            <span className="text-xs text-gray-400">v2.0</span>
          </div>
        </div>
      </div>

      {/* Profile Stats */}
      <div className="p-4 border-b border-[#38444d]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Profiles</span>
          {profilesLoading ? (
            <RefreshCw className="w-3 h-3 text-gray-500 animate-spin" />
          ) : (
            <span className="text-lg font-bold text-white">{profileCount}</span>
          )}
        </div>
        {Object.keys(groupCounts).length > 0 && (
          <div className="flex flex-wrap gap-1">
            {Object.entries(groupCounts).slice(0, 3).map(([group, count]) => (
              <span
                key={group}
                className="px-2 py-0.5 bg-[#1e2732] rounded text-xs text-gray-400"
                title={group}
              >
                {group.slice(0, 8)}: {count}
              </span>
            ))}
            {Object.keys(groupCounts).length > 3 && (
              <span className="px-2 py-0.5 text-xs text-gray-500">
                +{Object.keys(groupCounts).length - 3} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item, index) => {
            if (item.type === 'divider') {
              return (
                <li key={`divider-${index}`} className="pt-4 pb-2">
                  <span className="text-xs text-gray-500 uppercase tracking-wider px-4">
                    {item.label}
                  </span>
                </li>
              );
            }

            return (
              <li key={item.to}>
                <NavLink
                  to={item.to!}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-twitter-blue/20 text-twitter-blue font-semibold'
                        : 'text-gray-300 hover:bg-[#1e2732] hover:text-white'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5" />
                  <span className="text-sm">{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[#38444d]">
        <div className="text-xs text-gray-500 text-center">
          Built with Playwright + AI
        </div>
      </div>
    </div>
  );
}

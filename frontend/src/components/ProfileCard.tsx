import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Users,
  UserPlus,
  ExternalLink,
  RefreshCw,
  Play,
  Square,
  MoreHorizontal,
} from 'lucide-react';
import { profilesApi } from '../api/client';
import type { ProfileWithActions } from '../types';

interface ProfileCardProps {
  profile: ProfileWithActions;
  onAction?: (action: string, profileId: string) => void;
}

export default function ProfileCard({ profile, onAction }: ProfileCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const queryClient = useQueryClient();

  const openMutation = useMutation({
    mutationFn: () => profilesApi.open(profile.user_id),
    onSuccess: () => {
      setIsOpen(true);
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const closeMutation = useMutation({
    mutationFn: () => profilesApi.close(profile.user_id),
    onSuccess: () => {
      setIsOpen(false);
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const refreshMutation = useMutation({
    mutationFn: () => profilesApi.refreshStats(profile.user_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const handleToggleBrowser = () => {
    if (isOpen) {
      closeMutation.mutate();
    } else {
      openMutation.mutate();
    }
  };

  return (
    <div className="bg-[#192734] rounded-xl border border-[#38444d] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[#38444d]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-[#1e2732] flex items-center justify-center">
              <User className="w-6 h-6 text-gray-400" />
            </div>
            <div>
              <h3 className="font-semibold text-white">{profile.name || 'Unnamed'}</h3>
              <p className="text-sm text-gray-400">
                {profile.domain_name ? `@${profile.domain_name}` : `#${profile.serial_number}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Status indicator */}
            <span
              className={`w-2 h-2 rounded-full ${isOpen ? 'bg-green-500' : 'bg-gray-500'}`}
              title={isOpen ? 'Browser open' : 'Browser closed'}
            />

            {/* Menu */}
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="p-2 text-gray-400 hover:text-white hover:bg-[#1e2732] rounded-lg"
              >
                <MoreHorizontal className="w-5 h-5" />
              </button>

              {menuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-[#1e2732] rounded-lg shadow-lg border border-[#38444d] z-10">
                  <button
                    onClick={() => {
                      onAction?.('follow', profile.user_id);
                      setMenuOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-[#192734] first:rounded-t-lg"
                  >
                    Follow Users
                  </button>
                  <button
                    onClick={() => {
                      onAction?.('timeline', profile.user_id);
                      setMenuOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-[#192734]"
                  >
                    Process Timeline
                  </button>
                  <button
                    onClick={() => {
                      onAction?.('tweet', profile.user_id);
                      setMenuOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-[#192734] last:rounded-b-lg"
                  >
                    Post Tweet
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="p-4 grid grid-cols-3 gap-4 text-center border-b border-[#38444d]">
        <div>
          <div className="flex items-center justify-center gap-1 text-gray-400 text-sm mb-1">
            <Users className="w-4 h-4" />
            Followers
          </div>
          <p className="text-xl font-bold text-white">
            {(profile.followers_count ?? 0).toLocaleString()}
          </p>
        </div>
        <div>
          <div className="flex items-center justify-center gap-1 text-gray-400 text-sm mb-1">
            <UserPlus className="w-4 h-4" />
            Following
          </div>
          <p className="text-xl font-bold text-white">
            {(profile.following_count ?? 0).toLocaleString()}
          </p>
        </div>
        <div>
          <div className="flex items-center justify-center gap-1 text-gray-400 text-sm mb-1">
            Success
          </div>
          <p className="text-xl font-bold text-green-500">{(profile.success_rate ?? 0).toFixed(1)}%</p>
        </div>
      </div>

      {/* Actions */}
      <div className="p-4 flex gap-2">
        <button
          onClick={handleToggleBrowser}
          disabled={openMutation.isPending || closeMutation.isPending}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-full font-semibold transition-colors ${
            isOpen
              ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30'
              : 'bg-twitter-blue/20 text-twitter-blue hover:bg-twitter-blue/30'
          }`}
        >
          {isOpen ? (
            <>
              <Square className="w-4 h-4" /> Close
            </>
          ) : (
            <>
              <Play className="w-4 h-4" /> Open
            </>
          )}
        </button>

        <button
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending || !isOpen}
          className="p-2 text-gray-400 hover:text-white hover:bg-[#1e2732] rounded-full disabled:opacity-50"
          title="Refresh stats"
        >
          <RefreshCw className={`w-5 h-5 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
        </button>

        {profile.domain_name && (
          <a
            href={`https://twitter.com/${profile.domain_name}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 text-gray-400 hover:text-white hover:bg-[#1e2732] rounded-full"
            title="Open on Twitter"
          >
            <ExternalLink className="w-5 h-5" />
          </a>
        )}
      </div>

      {/* Action summary */}
      {(profile.total_assigned ?? 0) > 0 && (
        <div className="px-4 pb-4">
          <div className="text-xs text-gray-500 mb-2">Recent Activity</div>
          <div className="flex gap-4 text-sm">
            <span className="text-gray-400">
              Assigned: <span className="text-white">{profile.total_assigned ?? 0}</span>
            </span>
            <span className="text-gray-400">
              Completed: <span className="text-green-500">{profile.total_completed ?? 0}</span>
            </span>
            <span className="text-gray-400">
              Failed: <span className="text-red-500">{profile.total_failed ?? 0}</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

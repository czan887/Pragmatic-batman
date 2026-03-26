import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, Search, LayoutGrid, List, Play, Square, Users, UserCheck, BarChart3, Globe, Download, MapPin } from 'lucide-react';
import ProfileCard from '../components/ProfileCard';
import { profilesApi, dashboardApi } from '../api/client';
import type { ProfileWithActions } from '../types';

export default function Profiles() {
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const { data: profiles, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: dashboardApi.getProfiles,
  });

  const syncMutation = useMutation({
    mutationFn: profilesApi.sync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const filteredProfiles = profiles?.filter(
    (p) =>
      p.name?.toLowerCase().includes(search.toLowerCase()) ||
      p.domain_name?.toLowerCase().includes(search.toLowerCase()) ||
      p.serial_number?.includes(search)
  );

  const openMutation = useMutation({
    mutationFn: (profileId: string) => profilesApi.open(profileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const closeMutation = useMutation({
    mutationFn: (profileId: string) => profilesApi.close(profileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const [updatingProfiles, setUpdatingProfiles] = useState<string[]>([]);

  const updateLiveDataMutation = useMutation({
    mutationFn: async (profileIds: string[]) => {
      setUpdatingProfiles(profileIds);
      const results = [];
      for (const profileId of profileIds) {
        try {
          const result = await profilesApi.refreshStats(profileId);
          results.push({ profileId, success: true, stats: result.stats });
        } catch (error) {
          results.push({ profileId, success: false, error });
        }
      }
      return results;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      setUpdatingProfiles([]);
    },
    onError: () => {
      setUpdatingProfiles([]);
    },
  });

  const handleAction = (action: string, profileId: string) => {
    if (action === 'open') {
      openMutation.mutate(profileId);
    } else if (action === 'close') {
      closeMutation.mutate(profileId);
    }
    console.log(`Action: ${action} for profile ${profileId}`);
  };

  const toggleSelectAll = () => {
    if (selectedProfiles.length === filteredProfiles?.length) {
      setSelectedProfiles([]);
    } else {
      setSelectedProfiles(filteredProfiles?.map((p) => p.user_id) || []);
    }
  };

  const toggleSelect = (profileId: string) => {
    setSelectedProfiles((prev) =>
      prev.includes(profileId) ? prev.filter((id) => id !== profileId) : [...prev, profileId]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Profiles</h1>
          <p className="text-gray-400">
            {filteredProfiles?.length || 0} profiles {selectedProfiles.length > 0 && `(${selectedProfiles.length} selected)`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex items-center bg-[#192734] rounded-lg border border-[#38444d] p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-twitter-blue text-white' : 'text-gray-400 hover:text-white'}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-twitter-blue text-white' : 'text-gray-400 hover:text-white'}`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Update Live Data Button */}
          <button
            onClick={() => {
              const profilesToUpdate = selectedProfiles.length > 0 ? selectedProfiles : (filteredProfiles?.map(p => p.user_id) || []);
              if (profilesToUpdate.length > 0) {
                updateLiveDataMutation.mutate(profilesToUpdate);
              }
            }}
            disabled={updateLiveDataMutation.isPending || !filteredProfiles?.length}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-full font-semibold hover:bg-green-700 disabled:opacity-50"
            title="Update followers/following stats from Twitter"
          >
            <Download className={`w-4 h-4 ${updateLiveDataMutation.isPending ? 'animate-pulse' : ''}`} />
            {updateLiveDataMutation.isPending
              ? `Updating (${updatingProfiles.length})...`
              : selectedProfiles.length > 0
                ? `Update Selected (${selectedProfiles.length})`
                : 'Update All'}
          </button>

          {/* Sync from AdsPower Button */}
          <button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-twitter-blue text-white rounded-full font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
            title="Sync profiles from AdsPower"
          >
            <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            Sync AdsPower
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search profiles..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-12 pr-4 py-3 bg-[#192734] border border-[#38444d] rounded-full text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
        />
      </div>

      {/* Profiles View */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading profiles...</div>
      ) : !filteredProfiles || filteredProfiles.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400">No profiles found</p>
          <button
            onClick={() => syncMutation.mutate()}
            className="mt-4 text-twitter-blue hover:underline"
          >
            Sync profiles from AdsPower
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredProfiles.map((profile) => (
            <ProfileCard key={profile.user_id} profile={profile} onAction={handleAction} />
          ))}
        </div>
      ) : (
        <ProfileListView
          profiles={filteredProfiles}
          selectedProfiles={selectedProfiles}
          onToggleSelect={toggleSelect}
          onToggleSelectAll={toggleSelectAll}
          onAction={handleAction}
          isOpenPending={openMutation.isPending}
          isClosePending={closeMutation.isPending}
          updatingProfiles={updatingProfiles}
        />
      )}
    </div>
  );
}

function ProfileListView({
  profiles,
  selectedProfiles,
  onToggleSelect,
  onToggleSelectAll,
  onAction,
  isOpenPending,
  isClosePending,
  updatingProfiles,
}: {
  profiles: ProfileWithActions[];
  selectedProfiles: string[];
  onToggleSelect: (id: string) => void;
  onToggleSelectAll: () => void;
  onAction: (action: string, profileId: string) => void;
  isOpenPending: boolean;
  isClosePending: boolean;
  updatingProfiles: string[];
}) {
  const formatLastUpdated = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="bg-[#192734] rounded-xl border border-[#38444d] overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-[#1e2732] border-b border-[#38444d] text-sm font-medium text-gray-400">
            <th className="px-4 py-3 text-left w-16">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedProfiles.length === profiles.length && profiles.length > 0}
                  onChange={onToggleSelectAll}
                  className="w-4 h-4 rounded"
                />
                <span>#</span>
              </div>
            </th>
            <th className="px-4 py-3 text-left">Profile</th>
            <th className="px-4 py-3 text-left">Bio</th>
            <th className="px-4 py-3 text-left">Location</th>
            <th className="px-4 py-3 text-left">Group</th>
            <th className="px-4 py-3 text-center">Followers / Following</th>
            <th className="px-4 py-3 text-center">Stats</th>
            <th className="px-4 py-3 text-center w-24">Updated</th>
            <th className="px-4 py-3 text-right w-32">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#38444d]">
          {profiles.map((profile, index) => (
            <tr
              key={profile.user_id}
              className={`hover:bg-[#1e2732] transition-colors ${
                selectedProfiles.includes(profile.user_id) ? 'bg-twitter-blue/10' : ''
              } ${updatingProfiles.includes(profile.user_id) ? 'animate-pulse bg-green-500/5' : ''}`}
            >
              {/* Checkbox and Number */}
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedProfiles.includes(profile.user_id)}
                    onChange={() => onToggleSelect(profile.user_id)}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-gray-500 text-sm font-mono">{index + 1}</span>
                </div>
              </td>

              {/* Profile Info */}
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-twitter-blue to-purple-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                    {(profile.name || profile.serial_number)[0].toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="font-medium text-white truncate text-sm max-w-[150px]">
                      {profile.name || profile.serial_number}
                    </div>
                    {profile.domain_name && (
                      <div className="text-xs text-gray-400 truncate max-w-[150px]">@{profile.domain_name}</div>
                    )}
                  </div>
                </div>
              </td>

              {/* Bio */}
              <td className="px-4 py-3">
                <div className="text-xs text-gray-400 max-w-[200px] truncate" title={profile.bio || ''}>
                  {profile.bio || <span className="text-gray-600">-</span>}
                </div>
              </td>

              {/* Location */}
              <td className="px-4 py-3">
                {profile.location ? (
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    <MapPin className="w-3 h-3" />
                    <span className="truncate max-w-[100px]" title={profile.location}>
                      {profile.location}
                    </span>
                  </div>
                ) : (
                  <span className="text-xs text-gray-600">-</span>
                )}
              </td>

              {/* Group */}
              <td className="px-4 py-3">
                <span className="px-2 py-1 text-xs rounded-full bg-[#38444d] text-gray-300 inline-block max-w-[120px] truncate">
                  {profile.group_name || 'No Group'}
                </span>
              </td>

              {/* Followers */}
              <td className="px-4 py-3 text-center">
                <div className="flex items-center justify-center gap-3 text-sm">
                  <div className="flex items-center gap-1">
                    <Users className="w-3 h-3 text-gray-400" />
                    <span className="text-white text-xs">{(profile.followers_count ?? 0).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <UserCheck className="w-3 h-3 text-gray-400" />
                    <span className="text-white text-xs">{(profile.following_count ?? 0).toLocaleString()}</span>
                  </div>
                </div>
              </td>

              {/* Stats */}
              <td className="px-4 py-3 text-center">
                <div className="flex items-center justify-center gap-1">
                  <BarChart3 className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-gray-300">
                    {(profile.success_rate ?? 0).toFixed(0)}%
                  </span>
                  <span className="text-xs text-gray-500">
                    ({profile.total_completed ?? 0}/{profile.total_assigned ?? 0})
                  </span>
                </div>
              </td>

              {/* Last Updated */}
              <td className="px-4 py-3 text-center">
                <span className={`text-xs ${profile.last_updated ? 'text-gray-300' : 'text-gray-500'}`}>
                  {formatLastUpdated(profile.last_updated)}
                </span>
              </td>

              {/* Actions */}
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-1">
                  <button
                    onClick={() => onAction('open', profile.user_id)}
                    disabled={isOpenPending}
                    className="p-1.5 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 disabled:opacity-50"
                    title="Open Browser"
                  >
                    <Play className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => onAction('close', profile.user_id)}
                    disabled={isClosePending}
                    className="p-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 disabled:opacity-50"
                    title="Close Browser"
                  >
                    <Square className="w-3 h-3" />
                  </button>
                  {profile.ip_country && (
                    <div className="flex items-center gap-1 px-1.5 py-1 bg-[#38444d] rounded text-xs text-gray-300" title={profile.ip || 'Unknown IP'}>
                      <Globe className="w-3 h-3" />
                      {profile.ip_country}
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

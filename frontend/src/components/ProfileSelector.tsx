import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, Check, ChevronDown, X } from 'lucide-react';
import { profilesApi } from '../api/client';
import type { Profile } from '../types';

type SelectionMode = 'single' | 'multiple' | 'group' | 'all';

interface ProfileSelectorProps {
  selectedProfiles: string[];
  onChange: (profileIds: string[]) => void;
  mode?: SelectionMode;
  allowModeChange?: boolean;
  label?: string;
}

export default function ProfileSelector({
  selectedProfiles,
  onChange,
  mode: initialMode = 'single',
  allowModeChange = true,
  label = 'Select Profiles',
}: ProfileSelectorProps) {
  const [mode, setMode] = useState<SelectionMode>(initialMode);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<string>('');

  const { data: profiles, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  });

  // Get unique groups
  const groups = useMemo(() => {
    if (!profiles) return [];
    const groupSet = new Set<string>();
    profiles.forEach((p) => {
      if (p.group_name) groupSet.add(p.group_name);
    });
    return Array.from(groupSet).sort();
  }, [profiles]);

  // Get profiles by group
  const profilesByGroup = useMemo(() => {
    if (!profiles) return {};
    return profiles.reduce((acc, p) => {
      const group = p.group_name || 'Ungrouped';
      if (!acc[group]) acc[group] = [];
      acc[group].push(p);
      return acc;
    }, {} as Record<string, Profile[]>);
  }, [profiles]);

  const handleModeChange = (newMode: SelectionMode) => {
    setMode(newMode);
    onChange([]);
    setSelectedGroup('');
  };

  const handleSelectAll = () => {
    if (profiles) {
      onChange(profiles.map((p) => p.user_id));
    }
  };

  const handleSelectGroup = (groupName: string) => {
    setSelectedGroup(groupName);
    const groupProfiles = profilesByGroup[groupName] || [];
    onChange(groupProfiles.map((p) => p.user_id));
  };

  const handleToggleProfile = (profileId: string) => {
    if (mode === 'single') {
      onChange([profileId]);
    } else {
      if (selectedProfiles.includes(profileId)) {
        onChange(selectedProfiles.filter((id) => id !== profileId));
      } else {
        onChange([...selectedProfiles, profileId]);
      }
    }
  };

  const handleClear = () => {
    onChange([]);
    setSelectedGroup('');
  };

  const getSelectedLabel = () => {
    if (selectedProfiles.length === 0) return 'Choose profiles...';
    if (mode === 'all' && profiles && selectedProfiles.length === profiles.length) {
      return `All profiles (${profiles.length})`;
    }
    if (mode === 'group' && selectedGroup) {
      return `Group: ${selectedGroup} (${selectedProfiles.length})`;
    }
    if (selectedProfiles.length === 1 && profiles) {
      const p = profiles.find((p) => p.user_id === selectedProfiles[0]);
      return p?.name || p?.serial_number || selectedProfiles[0];
    }
    return `${selectedProfiles.length} profiles selected`;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm text-gray-400">{label}</label>
        {allowModeChange && (
          <div className="flex gap-1">
            <ModeButton
              active={mode === 'single'}
              onClick={() => handleModeChange('single')}
              label="Single"
            />
            <ModeButton
              active={mode === 'multiple'}
              onClick={() => handleModeChange('multiple')}
              label="Multiple"
            />
            <ModeButton
              active={mode === 'group'}
              onClick={() => handleModeChange('group')}
              label="Group"
            />
            <ModeButton
              active={mode === 'all'}
              onClick={() => handleModeChange('all')}
              label="All"
            />
          </div>
        )}
      </div>

      {/* All Profiles Mode */}
      {mode === 'all' && (
        <button
          onClick={handleSelectAll}
          className={`w-full p-3 rounded-lg border transition-colors flex items-center justify-between ${
            profiles && selectedProfiles.length === profiles.length
              ? 'bg-twitter-blue/20 border-twitter-blue text-white'
              : 'bg-[#1e2732] border-[#38444d] text-gray-400 hover:border-gray-500'
          }`}
        >
          <span className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Select All Profiles ({profiles?.length || 0})
          </span>
          {profiles && selectedProfiles.length === profiles.length && (
            <Check className="w-5 h-5 text-twitter-blue" />
          )}
        </button>
      )}

      {/* Group Selection Mode */}
      {mode === 'group' && (
        <div className="space-y-2">
          <select
            value={selectedGroup}
            onChange={(e) => handleSelectGroup(e.target.value)}
            className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
          >
            <option value="">Select a group...</option>
            {groups.map((group) => (
              <option key={group} value={group}>
                {group} ({profilesByGroup[group]?.length || 0} profiles)
              </option>
            ))}
          </select>
          {selectedGroup && (
            <div className="p-3 bg-[#1e2732] rounded-lg">
              <p className="text-sm text-gray-400 mb-2">
                Selected {selectedProfiles.length} profiles from "{selectedGroup}"
              </p>
              <div className="flex flex-wrap gap-1">
                {profilesByGroup[selectedGroup]?.slice(0, 5).map((p) => (
                  <span key={p.user_id} className="px-2 py-1 bg-twitter-blue/20 text-twitter-blue rounded text-xs">
                    {p.name || p.serial_number}
                  </span>
                ))}
                {(profilesByGroup[selectedGroup]?.length || 0) > 5 && (
                  <span className="px-2 py-1 text-gray-500 text-xs">
                    +{(profilesByGroup[selectedGroup]?.length || 0) - 5} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Single or Multiple Selection */}
      {(mode === 'single' || mode === 'multiple') && (
        <div className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue flex items-center justify-between"
          >
            <span className={selectedProfiles.length === 0 ? 'text-gray-500' : ''}>
              {getSelectedLabel()}
            </span>
            <div className="flex items-center gap-1">
              {selectedProfiles.length > 0 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClear();
                  }}
                  className="p-1 hover:bg-[#283340] rounded"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              )}
              <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </div>
          </button>

          {isOpen && (
            <div className="absolute z-50 w-full mt-1 bg-[#1e2732] border border-[#38444d] rounded-lg shadow-xl max-h-64 overflow-y-auto">
              {isLoading ? (
                <div className="p-4 text-center text-gray-500">Loading profiles...</div>
              ) : profiles?.length === 0 ? (
                <div className="p-4 text-center text-gray-500">No profiles found</div>
              ) : (
                profiles?.map((profile) => (
                  <button
                    key={profile.user_id}
                    onClick={() => {
                      handleToggleProfile(profile.user_id);
                      if (mode === 'single') setIsOpen(false);
                    }}
                    className={`w-full p-3 flex items-center justify-between hover:bg-[#283340] transition-colors ${
                      selectedProfiles.includes(profile.user_id) ? 'bg-twitter-blue/10' : ''
                    }`}
                  >
                    <div className="flex flex-col items-start">
                      <span className="text-white">
                        {profile.name || profile.serial_number}
                      </span>
                      <span className="text-xs text-gray-500">
                        {profile.domain_name && `@${profile.domain_name}`}
                        {profile.group_name && ` • ${profile.group_name}`}
                      </span>
                    </div>
                    {selectedProfiles.includes(profile.user_id) && (
                      <Check className="w-5 h-5 text-twitter-blue" />
                    )}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Selected Profiles Summary */}
      {mode === 'multiple' && selectedProfiles.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedProfiles.slice(0, 5).map((id) => {
            const p = profiles?.find((p) => p.user_id === id);
            return (
              <span
                key={id}
                className="px-2 py-1 bg-twitter-blue/20 text-twitter-blue rounded text-xs flex items-center gap-1"
              >
                {p?.name || p?.serial_number || id.slice(0, 8)}
                <button
                  onClick={() => handleToggleProfile(id)}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            );
          })}
          {selectedProfiles.length > 5 && (
            <span className="px-2 py-1 text-gray-500 text-xs">
              +{selectedProfiles.length - 5} more
            </span>
          )}
        </div>
      )}
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
        active
          ? 'bg-twitter-blue text-white'
          : 'bg-[#1e2732] text-gray-400 hover:text-white'
      }`}
    >
      {label}
    </button>
  );
}

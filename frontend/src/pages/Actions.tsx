import { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { UserPlus, Heart, MessageCircle, Send, Users, Layers, UserMinus, Repeat, CheckSquare, Square, Filter } from 'lucide-react';
import { profilesApi, actionsApi } from '../api/client';
import type { Profile } from '../types';

type SelectionMode = 'single' | 'multiple' | 'group' | 'all';

export default function Actions() {
  const [selectionMode, setSelectionMode] = useState<SelectionMode>('single');
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'follow' | 'timeline' | 'tweet' | 'bulk'>('follow');

  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  });

  // Get unique groups from profiles
  const groups = useMemo(() => {
    if (!profiles) return [];
    const groupSet = new Map<string, string>();
    profiles.forEach(p => {
      if (p.group_id && p.group_name) {
        groupSet.set(p.group_id, p.group_name);
      }
    });
    return Array.from(groupSet.entries()).map(([id, name]) => ({ id, name }));
  }, [profiles]);

  // Get effective profile IDs based on selection mode
  const effectiveProfileIds = useMemo(() => {
    switch (selectionMode) {
      case 'single':
        return selectedProfile ? [selectedProfile] : [];
      case 'multiple':
        return selectedProfiles;
      case 'group':
        return profiles?.filter(p => p.group_id === selectedGroup).map(p => p.user_id) || [];
      case 'all':
        return profiles?.map(p => p.user_id) || [];
      default:
        return [];
    }
  }, [selectionMode, selectedProfile, selectedProfiles, selectedGroup, profiles]);

  const toggleProfileSelection = (profileId: string) => {
    setSelectedProfiles(prev =>
      prev.includes(profileId)
        ? prev.filter(id => id !== profileId)
        : [...prev, profileId]
    );
  };

  const selectAllProfiles = () => {
    if (profiles) {
      setSelectedProfiles(profiles.map(p => p.user_id));
    }
  };

  const clearSelection = () => {
    setSelectedProfiles([]);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Actions</h1>
        <p className="text-gray-400">Execute bot actions on your profiles</p>
      </div>

      {/* Profile Selector */}
      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
        <div className="flex items-center justify-between">
          <label className="block text-sm text-gray-400">Profile Selection</label>
          <div className="flex gap-2">
            <button
              onClick={() => setSelectionMode('single')}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                selectionMode === 'single'
                  ? 'bg-twitter-blue text-white'
                  : 'bg-[#1e2732] text-gray-400 hover:text-white'
              }`}
            >
              Single
            </button>
            <button
              onClick={() => setSelectionMode('multiple')}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                selectionMode === 'multiple'
                  ? 'bg-twitter-blue text-white'
                  : 'bg-[#1e2732] text-gray-400 hover:text-white'
              }`}
            >
              Multiple
            </button>
            <button
              onClick={() => setSelectionMode('group')}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                selectionMode === 'group'
                  ? 'bg-twitter-blue text-white'
                  : 'bg-[#1e2732] text-gray-400 hover:text-white'
              }`}
            >
              By Group
            </button>
            <button
              onClick={() => setSelectionMode('all')}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                selectionMode === 'all'
                  ? 'bg-twitter-blue text-white'
                  : 'bg-[#1e2732] text-gray-400 hover:text-white'
              }`}
            >
              All Profiles
            </button>
          </div>
        </div>

        {/* Single Profile Selector */}
        {selectionMode === 'single' && (
          <select
            value={selectedProfile}
            onChange={(e) => setSelectedProfile(e.target.value)}
            className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
          >
            <option value="">Choose a profile...</option>
            {profiles?.map((profile) => (
              <option key={profile.user_id} value={profile.user_id}>
                {profile.name || profile.serial_number} {profile.domain_name && `(@${profile.domain_name})`}
              </option>
            ))}
          </select>
        )}

        {/* Multiple Profile Selector */}
        {selectionMode === 'multiple' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">
                {selectedProfiles.length} of {profiles?.length || 0} profiles selected
              </span>
              <div className="flex gap-2">
                <button
                  onClick={selectAllProfiles}
                  className="flex items-center gap-1 px-3 py-1 text-sm bg-[#1e2732] text-gray-300 rounded hover:bg-[#283340]"
                >
                  <CheckSquare className="w-4 h-4" />
                  Select All
                </button>
                <button
                  onClick={clearSelection}
                  className="flex items-center gap-1 px-3 py-1 text-sm bg-[#1e2732] text-gray-300 rounded hover:bg-[#283340]"
                >
                  <Square className="w-4 h-4" />
                  Clear
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-64 overflow-y-auto p-2 bg-[#1e2732] rounded-lg border border-[#38444d]">
              {profiles?.map((profile) => (
                <label
                  key={profile.user_id}
                  className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                    selectedProfiles.includes(profile.user_id)
                      ? 'bg-twitter-blue/20 border border-twitter-blue'
                      : 'hover:bg-[#283340] border border-transparent'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedProfiles.includes(profile.user_id)}
                    onChange={() => toggleProfileSelection(profile.user_id)}
                    className="w-4 h-4"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="text-white text-sm truncate block">
                      {profile.name || profile.serial_number}
                    </span>
                    {profile.domain_name && (
                      <span className="text-gray-500 text-xs truncate block">
                        @{profile.domain_name}
                      </span>
                    )}
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Group Selector */}
        {selectionMode === 'group' && (
          <div className="space-y-3">
            <select
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
              className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
            >
              <option value="">Choose a group...</option>
              {groups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name} ({profiles?.filter(p => p.group_id === group.id).length || 0} profiles)
                </option>
              ))}
            </select>
            {selectedGroup && (
              <div className="p-3 bg-[#1e2732] rounded-lg border border-[#38444d]">
                <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
                  <Filter className="w-4 h-4" />
                  <span>Profiles in this group:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {profiles?.filter(p => p.group_id === selectedGroup).map((profile) => (
                    <span
                      key={profile.user_id}
                      className="px-2 py-1 text-xs bg-twitter-blue/20 text-twitter-blue rounded-full"
                    >
                      {profile.name || profile.serial_number}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* All Profiles Summary */}
        {selectionMode === 'all' && (
          <div className="p-4 bg-[#1e2732] rounded-lg border border-[#38444d]">
            <div className="flex items-center gap-2 text-twitter-blue">
              <Users className="w-5 h-5" />
              <span className="font-semibold">All {profiles?.length || 0} profiles selected</span>
            </div>
            <p className="text-sm text-gray-400 mt-2">
              Actions will be executed on all profiles sequentially with the configured delay.
            </p>
          </div>
        )}

        {/* Selection Summary */}
        {effectiveProfileIds.length > 0 && (
          <div className="flex items-center gap-2 p-2 bg-green-500/10 border border-green-500/30 rounded-lg">
            <CheckSquare className="w-4 h-4 text-green-500" />
            <span className="text-sm text-green-400">
              {effectiveProfileIds.length} profile{effectiveProfileIds.length !== 1 ? 's' : ''} ready for actions
            </span>
          </div>
        )}
      </div>

      {/* Action Tabs */}
      {effectiveProfileIds.length > 0 && (
        <>
          <div className="flex gap-2 flex-wrap">
            <TabButton
              active={activeTab === 'follow'}
              onClick={() => setActiveTab('follow')}
              icon={UserPlus}
              label="Follow"
            />
            <TabButton
              active={activeTab === 'timeline'}
              onClick={() => setActiveTab('timeline')}
              icon={Heart}
              label="Timeline"
            />
            <TabButton
              active={activeTab === 'tweet'}
              onClick={() => setActiveTab('tweet')}
              icon={Send}
              label="Tweet"
            />
            <TabButton
              active={activeTab === 'bulk'}
              onClick={() => setActiveTab('bulk')}
              icon={Layers}
              label="Bulk Actions"
            />
          </div>

          {/* Action Panels */}
          {activeTab === 'follow' && <FollowPanel profileIds={effectiveProfileIds} isMultiple={effectiveProfileIds.length > 1} />}
          {activeTab === 'timeline' && <TimelinePanel profileIds={effectiveProfileIds} isMultiple={effectiveProfileIds.length > 1} />}
          {activeTab === 'tweet' && <TweetPanel profileIds={effectiveProfileIds} isMultiple={effectiveProfileIds.length > 1} />}
          {activeTab === 'bulk' && <BulkActionsPanel profileIds={effectiveProfileIds} profiles={profiles || []} isMultiple={effectiveProfileIds.length > 1} />}
        </>
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ElementType;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-full font-semibold transition-colors ${
        active
          ? 'bg-twitter-blue text-white'
          : 'bg-[#192734] text-gray-400 hover:bg-[#1e2732] hover:text-white'
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  );
}

function FollowPanel({ profileIds, isMultiple }: { profileIds: string[]; isMultiple: boolean }) {
  const [username, setUsername] = useState('');
  const [targetUsername, setTargetUsername] = useState('');
  const [batchSize, setBatchSize] = useState(15);
  const [useAI, setUseAI] = useState(true);
  const [delay, setDelay] = useState(30);

  const followMutation = useMutation({
    mutationFn: async () => {
      if (isMultiple) {
        // Use multi-profile action for multiple profiles
        return actionsApi.multiProfile({
          profile_ids: profileIds,
          action_type: 'follow',
          target: username,
          use_ai: useAI,
          delay_between_profiles: delay,
        });
      } else {
        return actionsApi.follow({
          profile_id: profileIds[0],
          username,
          use_ai_analysis: useAI,
        });
      }
    },
    onSuccess: () => setUsername(''),
  });

  const followFollowersMutation = useMutation({
    mutationFn: async () => {
      // For multiple profiles, queue follow-followers for each profile
      const results = [];
      for (const profileId of profileIds) {
        const result = await actionsApi.followFollowers({
          profile_id: profileId,
          target_username: targetUsername,
          batch_size: batchSize,
          batch_delay_minutes: 60,
          use_ai_analysis: useAI,
        });
        results.push(result);
      }
      return results;
    },
    onSuccess: () => setTargetUsername(''),
  });

  return (
    <div className="space-y-6">
      {/* Multi-profile indicator */}
      {isMultiple && (
        <div className="flex items-center gap-2 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
          <Users className="w-4 h-4 text-purple-400" />
          <span className="text-sm text-purple-300">
            Actions will be executed on {profileIds.length} profiles
          </span>
        </div>
      )}

      {/* Single Follow */}
      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Follow User {isMultiple && `(${profileIds.length} profiles)`}
        </h3>
        <div className="space-y-4">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Username (without @)"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="flex-1 p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
            />
            <button
              onClick={() => followMutation.mutate()}
              disabled={!username || followMutation.isPending}
              className="px-6 py-3 bg-twitter-blue text-white rounded-lg font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
            >
              {followMutation.isPending ? 'Following...' : 'Follow'}
            </button>
          </div>
          {isMultiple && (
            <div className="flex gap-4 items-center">
              <div className="flex-1">
                <label className="block text-sm text-gray-400 mb-1">Delay between profiles (seconds)</label>
                <input
                  type="number"
                  min={5}
                  max={300}
                  value={delay}
                  onChange={(e) => setDelay(parseInt(e.target.value))}
                  className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
                />
              </div>
            </div>
          )}
        </div>
        {followMutation.isSuccess && (
          <p className="mt-2 text-green-500 text-sm">
            Follow action{isMultiple ? 's' : ''} queued!
          </p>
        )}
      </div>

      {/* Batch Follow */}
      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Follow Followers of User {isMultiple && `(${profileIds.length} profiles)`}
        </h3>
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Target username (without @)"
            value={targetUsername}
            onChange={(e) => setTargetUsername(e.target.value)}
            className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
          />
          <div className="flex gap-4 items-center">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Batch Size</label>
              <input
                type="number"
                min={1}
                max={50}
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value))}
                className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="useAI"
                checked={useAI}
                onChange={(e) => setUseAI(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="useAI" className="text-gray-400">Use AI Analysis</label>
            </div>
          </div>
          <button
            onClick={() => followFollowersMutation.mutate()}
            disabled={!targetUsername || followFollowersMutation.isPending}
            className="w-full px-6 py-3 bg-twitter-blue text-white rounded-lg font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
          >
            {followFollowersMutation.isPending
              ? 'Queuing...'
              : `Queue ${batchSize} Follows${isMultiple ? ` x ${profileIds.length} profiles` : ''}`}
          </button>
        </div>
        {followFollowersMutation.isSuccess && (
          <p className="mt-2 text-green-500 text-sm">Batch follow tasks queued!</p>
        )}
      </div>
    </div>
  );
}

function TimelinePanel({ profileIds, isMultiple }: { profileIds: string[]; isMultiple: boolean }) {
  const [username, setUsername] = useState('');
  const [shouldLike, setShouldLike] = useState(true);
  const [shouldRetweet, setShouldRetweet] = useState(false);
  const [shouldComment, setShouldComment] = useState(false);
  const [useAIComment, setUseAIComment] = useState(true);
  const [maxTweets, setMaxTweets] = useState(10);

  const mutation = useMutation({
    mutationFn: async () => {
      const results = [];
      for (const profileId of profileIds) {
        const result = await actionsApi.processTimeline({
          profile_id: profileId,
          username,
          should_like: shouldLike,
          should_retweet: shouldRetweet,
          should_comment: shouldComment,
          use_ai_comment: useAIComment,
          comment_template: null,
          max_tweets: maxTweets,
        });
        results.push(result);
      }
      return results;
    },
    onSuccess: () => setUsername(''),
  });

  return (
    <div className="space-y-6">
      {/* Multi-profile indicator */}
      {isMultiple && (
        <div className="flex items-center gap-2 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
          <Users className="w-4 h-4 text-purple-400" />
          <span className="text-sm text-purple-300">
            Actions will be executed on {profileIds.length} profiles
          </span>
        </div>
      )}

      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">
          Process User Timeline {isMultiple && `(${profileIds.length} profiles)`}
        </h3>

        <input
          type="text"
          placeholder="Username (without @)"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
        />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={shouldLike}
              onChange={(e) => setShouldLike(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-gray-300">Like tweets</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={shouldRetweet}
              onChange={(e) => setShouldRetweet(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-gray-300">Retweet</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={shouldComment}
              onChange={(e) => setShouldComment(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-gray-300">Comment</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useAIComment}
              onChange={(e) => setUseAIComment(e.target.checked)}
              disabled={!shouldComment}
              className="w-4 h-4"
            />
            <span className="text-gray-300">AI Comments</span>
          </label>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Max Tweets</label>
          <input
            type="number"
            min={1}
            max={50}
            value={maxTweets}
            onChange={(e) => setMaxTweets(parseInt(e.target.value))}
            className="w-32 p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
          />
        </div>

        <button
          onClick={() => mutation.mutate()}
          disabled={!username || mutation.isPending}
          className="w-full px-6 py-3 bg-twitter-blue text-white rounded-lg font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
        >
          {mutation.isPending
            ? 'Processing...'
            : `Process Timeline${isMultiple ? ` (${profileIds.length} profiles)` : ''}`}
        </button>

        {mutation.isSuccess && (
          <p className="text-green-500 text-sm">Timeline processing started!</p>
        )}
      </div>
    </div>
  );
}

function TweetPanel({ profileIds, isMultiple }: { profileIds: string[]; isMultiple: boolean }) {
  const [text, setText] = useState('');
  const [useAI, setUseAI] = useState(false);
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState('informative');

  const mutation = useMutation({
    mutationFn: async () => {
      const results = [];
      for (const profileId of profileIds) {
        const result = await actionsApi.postTweet({
          profile_id: profileId,
          text: useAI ? null : text,
          use_ai_generation: useAI,
          topic: useAI ? topic : null,
          style,
        });
        results.push(result);
      }
      return results;
    },
    onSuccess: () => {
      setText('');
      setTopic('');
    },
  });

  return (
    <div className="space-y-6">
      {/* Multi-profile indicator */}
      {isMultiple && (
        <div className="flex items-center gap-2 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
          <Users className="w-4 h-4 text-purple-400" />
          <span className="text-sm text-purple-300">
            Tweet will be posted on {profileIds.length} profiles
            {useAI && ' (AI will generate unique content for each)'}
          </span>
        </div>
      )}

      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">
          Post Tweet {isMultiple && `(${profileIds.length} profiles)`}
        </h3>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useAI}
            onChange={(e) => setUseAI(e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-gray-300">Use AI to generate tweet</span>
        </label>

        {useAI ? (
          <>
            <input
              type="text"
              placeholder="Topic for the tweet"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
            />
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
            >
              <option value="informative">Informative</option>
              <option value="casual">Casual</option>
              <option value="professional">Professional</option>
              <option value="humorous">Humorous</option>
            </select>
          </>
        ) : (
          <textarea
            placeholder="What's happening?"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={280}
            rows={4}
            className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue resize-none"
          />
        )}

        <div className="flex items-center justify-between">
          {!useAI && (
            <span className="text-sm text-gray-500">{text.length}/280</span>
          )}
          <button
            onClick={() => mutation.mutate()}
            disabled={(!useAI && !text) || (useAI && !topic) || mutation.isPending}
            className="px-6 py-3 bg-twitter-blue text-white rounded-full font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
          >
            {mutation.isPending ? 'Posting...' : `Post${isMultiple ? ` (${profileIds.length})` : ''}`}
          </button>
        </div>

        {mutation.isSuccess && (
          <p className="text-green-500 text-sm">
            Tweet{isMultiple ? 's' : ''} posted!
          </p>
        )}
      </div>
    </div>
  );
}

function BulkActionsPanel({ profileIds, profiles, isMultiple }: { profileIds: string[]; profiles: Profile[]; isMultiple: boolean }) {
  const [bulkType, setBulkType] = useState<'follow' | 'unfollow' | 'like' | 'retweet' | 'comment' | 'multi-profile'>('follow');
  const [inputText, setInputText] = useState('');
  const [useAI, setUseAI] = useState(true);
  const [delay, setDelay] = useState(30);
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const [multiTarget, setMultiTarget] = useState('');
  const [multiAction, setMultiAction] = useState<'follow' | 'unfollow' | 'like' | 'retweet' | 'comment'>('follow');

  // Parse input text into array
  const parseInput = (text: string): string[] => {
    return text
      .split(/[\n,]+/)
      .map((item) => item.trim().replace(/^@/, ''))
      .filter((item) => item.length > 0);
  };

  const items = parseInput(inputText);

  // Helper to execute bulk action on multiple profiles
  const executeBulkOnProfiles = async (
    action: (profileId: string) => Promise<unknown>
  ) => {
    const results = [];
    for (const profileId of profileIds) {
      const result = await action(profileId);
      results.push(result);
    }
    return results;
  };

  // Bulk Follow
  const bulkFollowMutation = useMutation({
    mutationFn: () =>
      executeBulkOnProfiles((profileId) =>
        actionsApi.bulkFollow({
          profile_id: profileId,
          usernames: items,
          use_ai_analysis: useAI,
          delay_between_follows: delay,
        })
      ),
    onSuccess: () => setInputText(''),
  });

  // Bulk Unfollow
  const bulkUnfollowMutation = useMutation({
    mutationFn: () =>
      executeBulkOnProfiles((profileId) =>
        actionsApi.bulkUnfollow({
          profile_id: profileId,
          usernames: items,
          delay_between_unfollows: delay,
        })
      ),
    onSuccess: () => setInputText(''),
  });

  // Bulk Like
  const bulkLikeMutation = useMutation({
    mutationFn: () =>
      executeBulkOnProfiles((profileId) =>
        actionsApi.bulkLike({
          profile_id: profileId,
          tweet_urls: items,
          delay_between_likes: delay,
        })
      ),
    onSuccess: () => setInputText(''),
  });

  // Bulk Retweet
  const bulkRetweetMutation = useMutation({
    mutationFn: () =>
      executeBulkOnProfiles((profileId) =>
        actionsApi.bulkRetweet({
          profile_id: profileId,
          tweet_urls: items,
          delay_between_retweets: delay,
        })
      ),
    onSuccess: () => setInputText(''),
  });

  // Bulk Comment
  const bulkCommentMutation = useMutation({
    mutationFn: () =>
      executeBulkOnProfiles((profileId) =>
        actionsApi.bulkComment({
          profile_id: profileId,
          tweet_urls: items,
          use_ai_generation: useAI,
          comment_template: null,
          delay_between_comments: delay,
        })
      ),
    onSuccess: () => setInputText(''),
  });

  // Multi-Profile Action (uses selected profiles from within this panel)
  const multiProfileMutation = useMutation({
    mutationFn: () =>
      actionsApi.multiProfile({
        profile_ids: selectedProfiles.length > 0 ? selectedProfiles : profileIds,
        action_type: multiAction,
        target: multiTarget,
        use_ai: useAI,
        delay_between_profiles: delay,
      }),
    onSuccess: () => {
      setMultiTarget('');
      setSelectedProfiles([]);
    },
  });

  const handleSubmit = () => {
    switch (bulkType) {
      case 'follow':
        bulkFollowMutation.mutate();
        break;
      case 'unfollow':
        bulkUnfollowMutation.mutate();
        break;
      case 'like':
        bulkLikeMutation.mutate();
        break;
      case 'retweet':
        bulkRetweetMutation.mutate();
        break;
      case 'comment':
        bulkCommentMutation.mutate();
        break;
      case 'multi-profile':
        multiProfileMutation.mutate();
        break;
    }
  };

  const isPending =
    bulkFollowMutation.isPending ||
    bulkUnfollowMutation.isPending ||
    bulkLikeMutation.isPending ||
    bulkRetweetMutation.isPending ||
    bulkCommentMutation.isPending ||
    multiProfileMutation.isPending;

  const isSuccess =
    bulkFollowMutation.isSuccess ||
    bulkUnfollowMutation.isSuccess ||
    bulkLikeMutation.isSuccess ||
    bulkRetweetMutation.isSuccess ||
    bulkCommentMutation.isSuccess ||
    multiProfileMutation.isSuccess;

  const toggleProfile = (id: string) => {
    setSelectedProfiles((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      {/* Multi-profile indicator */}
      {isMultiple && (
        <div className="flex items-center gap-2 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
          <Users className="w-4 h-4 text-purple-400" />
          <span className="text-sm text-purple-300">
            Bulk actions will be executed on {profileIds.length} profiles
          </span>
        </div>
      )}

      {/* Bulk Action Type Selector */}
      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Bulk Action Type</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
          <BulkTypeButton
            active={bulkType === 'follow'}
            onClick={() => setBulkType('follow')}
            icon={UserPlus}
            label="Follow"
          />
          <BulkTypeButton
            active={bulkType === 'unfollow'}
            onClick={() => setBulkType('unfollow')}
            icon={UserMinus}
            label="Unfollow"
          />
          <BulkTypeButton
            active={bulkType === 'like'}
            onClick={() => setBulkType('like')}
            icon={Heart}
            label="Like"
          />
          <BulkTypeButton
            active={bulkType === 'retweet'}
            onClick={() => setBulkType('retweet')}
            icon={Repeat}
            label="Retweet"
          />
          <BulkTypeButton
            active={bulkType === 'comment'}
            onClick={() => setBulkType('comment')}
            icon={MessageCircle}
            label="Comment"
          />
          <BulkTypeButton
            active={bulkType === 'multi-profile'}
            onClick={() => setBulkType('multi-profile')}
            icon={Users}
            label="Multi-Profile"
          />
        </div>
      </div>

      {/* Bulk Input Panel */}
      {bulkType !== 'multi-profile' ? (
        <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white">
            Bulk {bulkType.charAt(0).toUpperCase() + bulkType.slice(1)}
          </h3>
          <p className="text-sm text-gray-400">
            {bulkType === 'follow' || bulkType === 'unfollow'
              ? 'Enter usernames (one per line or comma-separated)'
              : 'Enter tweet URLs (one per line or comma-separated)'}
          </p>

          <textarea
            placeholder={
              bulkType === 'follow' || bulkType === 'unfollow'
                ? 'user1\nuser2\nuser3\n...'
                : 'https://twitter.com/user/status/123\nhttps://twitter.com/user/status/456\n...'
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            rows={8}
            className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue resize-none font-mono text-sm"
          />

          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>{items.length} items detected</span>
            <span>Max: 100</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Delay between actions (seconds)
              </label>
              <input
                type="number"
                min={5}
                max={300}
                value={delay}
                onChange={(e) => setDelay(parseInt(e.target.value))}
                className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
            </div>
            {(bulkType === 'follow' || bulkType === 'comment') && (
              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="bulkUseAI"
                  checked={useAI}
                  onChange={(e) => setUseAI(e.target.checked)}
                  className="w-4 h-4"
                />
                <label htmlFor="bulkUseAI" className="text-gray-400">
                  {bulkType === 'follow' ? 'Use AI Analysis' : 'Use AI Comments'}
                </label>
              </div>
            )}
          </div>

          <button
            onClick={handleSubmit}
            disabled={items.length === 0 || items.length > 100 || isPending}
            className="w-full px-6 py-3 bg-twitter-blue text-white rounded-lg font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
          >
            {isPending
              ? 'Queuing...'
              : `Queue ${items.length} ${bulkType} action${items.length !== 1 ? 's' : ''}${isMultiple ? ` x ${profileIds.length} profiles` : ''}`}
          </button>

          {isSuccess && (
            <p className="text-green-500 text-sm">Bulk actions queued successfully!</p>
          )}
        </div>
      ) : (
        /* Multi-Profile Panel */
        <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white">Multi-Profile Action</h3>
          <p className="text-sm text-gray-400">
            Execute the same action across multiple profiles
          </p>

          {/* Pre-selected profiles notice */}
          {isMultiple && (
            <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <CheckSquare className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-300">
                Using {profileIds.length} pre-selected profiles from above. You can override below.
              </span>
            </div>
          )}

          {/* Profile Selection */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              {isMultiple ? 'Override Profile Selection (optional)' : 'Select Profiles'}
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-48 overflow-y-auto p-2 bg-[#1e2732] rounded-lg border border-[#38444d]">
              {profiles.map((profile) => (
                <label
                  key={profile.user_id}
                  className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                    selectedProfiles.includes(profile.user_id)
                      ? 'bg-twitter-blue/20 border border-twitter-blue'
                      : profileIds.includes(profile.user_id) && selectedProfiles.length === 0
                        ? 'bg-green-500/10 border border-green-500/30'
                        : 'hover:bg-[#283340]'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedProfiles.includes(profile.user_id)}
                    onChange={() => toggleProfile(profile.user_id)}
                    className="w-4 h-4"
                  />
                  <span className="text-white text-sm truncate">
                    {profile.name || profile.serial_number}
                  </span>
                </label>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {selectedProfiles.length > 0
                ? `${selectedProfiles.length} profiles selected (override)`
                : isMultiple
                  ? `Using ${profileIds.length} pre-selected profiles`
                  : '0 profiles selected'}
            </p>
          </div>

          {/* Action Type */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Action Type</label>
            <select
              value={multiAction}
              onChange={(e) => setMultiAction(e.target.value as typeof multiAction)}
              className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
            >
              <option value="follow">Follow User</option>
              <option value="unfollow">Unfollow User</option>
              <option value="like">Like Tweet</option>
              <option value="retweet">Retweet</option>
              <option value="comment">Comment</option>
            </select>
          </div>

          {/* Target */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              {multiAction === 'follow' || multiAction === 'unfollow'
                ? 'Username'
                : 'Tweet URL'}
            </label>
            <input
              type="text"
              placeholder={
                multiAction === 'follow' || multiAction === 'unfollow'
                  ? 'Username (without @)'
                  : 'https://twitter.com/user/status/123'
              }
              value={multiTarget}
              onChange={(e) => setMultiTarget(e.target.value)}
              className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
            />
          </div>

          {/* Delay */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Delay between profiles (seconds)
              </label>
              <input
                type="number"
                min={10}
                max={600}
                value={delay}
                onChange={(e) => setDelay(parseInt(e.target.value))}
                className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="multiUseAI"
                checked={useAI}
                onChange={(e) => setUseAI(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="multiUseAI" className="text-gray-400">
                Use AI
              </label>
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={(selectedProfiles.length === 0 && profileIds.length === 0) || !multiTarget || isPending}
            className="w-full px-6 py-3 bg-twitter-blue text-white rounded-lg font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
          >
            {isPending
              ? 'Queuing...'
              : `Execute ${multiAction} on ${selectedProfiles.length > 0 ? selectedProfiles.length : profileIds.length} profiles`}
          </button>

          {isSuccess && (
            <p className="text-green-500 text-sm">Multi-profile actions queued successfully!</p>
          )}
        </div>
      )}
    </div>
  );
}

function BulkTypeButton({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ElementType;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-1 p-3 rounded-lg font-medium transition-colors ${
        active
          ? 'bg-twitter-blue text-white'
          : 'bg-[#1e2732] text-gray-400 hover:bg-[#283340] hover:text-white'
      }`}
    >
      <Icon className="w-5 h-5" />
      <span className="text-xs">{label}</span>
    </button>
  );
}

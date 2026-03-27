import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { UserPlus, UserMinus, Heart, Repeat, MessageCircle, Sparkles, Trash2, Play, Users } from 'lucide-react';
import { actionsApi } from '../api/client';
import FileImport from '../components/FileImport';
import ProfileSelector from '../components/ProfileSelector';

export default function UserActions() {
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const [userInput, setUserInput] = useState('');
  const [commentTemplate, setCommentTemplate] = useState('');

  // Follow Followers State
  const [followFollowersTarget, setFollowFollowersTarget] = useState('');
  const [followFollowersBatchSize, setFollowFollowersBatchSize] = useState(10);

  // Action checkboxes
  const [shouldFollow, setShouldFollow] = useState(false);
  const [shouldUnfollow, setShouldUnfollow] = useState(false);
  const [shouldLike, setShouldLike] = useState(false);
  const [shouldRetweet, setShouldRetweet] = useState(false);
  const [shouldComment, setShouldComment] = useState(false);
  const [useAIComment, setUseAIComment] = useState(true);
  const [shouldRefactor, setShouldRefactor] = useState(false);
  const [maxTweetsPerUser, setMaxTweetsPerUser] = useState(10);

  const parseUsernames = (text: string): string[] => {
    return text
      .split(/[\n,]+/)
      .map((item) => item.trim().replace(/^@/, ''))
      .filter((item) => item.length > 0);
  };

  const usernames = parseUsernames(userInput);

  const processUsersMutation = useMutation({
    mutationFn: async () => {
      // Process for each selected profile
      const results = await Promise.all(
        selectedProfiles.map((profileId) =>
          actionsApi.processUsers({
            profile_id: profileId,
            usernames,
            should_follow: shouldFollow,
            should_unfollow: shouldUnfollow,
            should_like: shouldLike,
            should_retweet: shouldRetweet,
            should_comment: shouldComment,
            use_ai_comment: useAIComment,
            should_refactor: shouldRefactor,
            comment_template: shouldComment && !useAIComment ? commentTemplate : null,
            max_tweets_per_user: maxTweetsPerUser,
          })
        )
      );
      return results;
    },
    onSuccess: () => {
      // Optionally clear form
    },
  });

  // Follow Followers Mutation
  const followFollowersMutation = useMutation({
    mutationFn: async () => {
      // For multiple profiles, queue follow-followers for each profile
      const results = await Promise.all(
        selectedProfiles.map((profileId) =>
          actionsApi.followFollowers({
            profile_id: profileId,
            target_username: followFollowersTarget.replace('@', ''),
            batch_size: followFollowersBatchSize,
            batch_delay_minutes: 5,
            use_ai_analysis: false,
          })
        )
      );
      return results;
    },
    onSuccess: () => {
      // Optionally clear form
    },
  });

  const handleImport = (items: string[]) => {
    setUserInput((prev) => {
      const existing = parseUsernames(prev);
      const combined = [...new Set([...existing, ...items])];
      return combined.join('\n');
    });
  };

  const clearInput = () => {
    setUserInput('');
  };

  const hasSelectedAction = shouldFollow || shouldUnfollow || shouldLike || shouldRetweet || shouldComment || shouldRefactor;
  const canSubmit = selectedProfiles.length > 0 && usernames.length > 0 && hasSelectedAction;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">User Actions</h1>
        <p className="text-gray-400">Process actions on user profiles and timelines</p>
      </div>

      {/* Profile Selector */}
      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6">
        <ProfileSelector
          selectedProfiles={selectedProfiles}
          onChange={setSelectedProfiles}
          allowModeChange={true}
          label="Select Profiles"
        />
      </div>

      {selectedProfiles.length > 0 && (
        <>
          {/* User Input */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">User IDs / Usernames</h3>
              <div className="flex gap-2">
                <span className="text-sm text-gray-400">{usernames.length} users</span>
                <button
                  onClick={clearInput}
                  className="p-1 text-gray-400 hover:text-white hover:bg-[#283340] rounded"
                  title="Clear all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Enter usernames (one per line or comma-separated)&#10;@user1&#10;user2&#10;user3"
              rows={6}
              className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue resize-none font-mono text-sm"
            />

            <FileImport
              onImport={handleImport}
              label="Or import from file"
              placeholder="Drop file with usernames"
            />
          </div>

          {/* User Engagement Actions */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">User Engagement Actions</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <ActionCheckbox
                checked={shouldFollow}
                onChange={setShouldFollow}
                icon={UserPlus}
                label="Follow User"
                color="text-green-500"
              />
              <ActionCheckbox
                checked={shouldUnfollow}
                onChange={setShouldUnfollow}
                icon={UserMinus}
                label="Unfollow User"
                color="text-red-500"
              />
            </div>
          </div>

          {/* Follow Followers of User */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-twitter-blue" />
              <h3 className="text-lg font-semibold text-white">
                Follow Followers of User {selectedProfiles.length > 1 && `(${selectedProfiles.length} profiles)`}
              </h3>
            </div>
            <p className="text-gray-400 text-sm">
              Organically follow followers of a target user. Each profile will interact with the target's followers
              (like posts, repost, then follow) in a natural, human-like way.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Target Username</label>
                <input
                  type="text"
                  value={followFollowersTarget}
                  onChange={(e) => setFollowFollowersTarget(e.target.value)}
                  placeholder="@elonmusk"
                  className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Number of Followers to Follow</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={followFollowersBatchSize}
                  onChange={(e) => setFollowFollowersBatchSize(parseInt(e.target.value) || 10)}
                  className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
                />
              </div>
            </div>

            <button
              onClick={() => followFollowersMutation.mutate()}
              disabled={!followFollowersTarget || followFollowersMutation.isPending}
              className="flex items-center gap-2 px-6 py-2 bg-twitter-blue text-white rounded-full font-medium hover:bg-twitter-blue/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Users className="w-4 h-4" />
              {followFollowersMutation.isPending
                ? 'Starting...'
                : `Follow ${followFollowersBatchSize} Followers`}
            </button>
            {followFollowersMutation.isSuccess && (
              <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-3">
                <p className="text-green-500 text-sm">Follow followers task started! Check logs for progress.</p>
              </div>
            )}
            {followFollowersMutation.isError && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3">
                <p className="text-red-500 text-sm">
                  {followFollowersMutation.error instanceof Error
                    ? followFollowersMutation.error.message
                    : 'Failed to start follow followers task'}
                </p>
              </div>
            )}
          </div>

          {/* Post-Related Actions */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">Timeline Actions (on user's posts)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <ActionCheckbox
                checked={shouldLike}
                onChange={setShouldLike}
                icon={Heart}
                label="Like Posts"
                color="text-pink-500"
              />
              <ActionCheckbox
                checked={shouldRetweet}
                onChange={setShouldRetweet}
                icon={Repeat}
                label="Retweet Posts"
                color="text-green-500"
              />
              <ActionCheckbox
                checked={shouldRefactor}
                onChange={setShouldRefactor}
                icon={Sparkles}
                label="Refactor Posts"
                color="text-purple-500"
              />
            </div>

            {(shouldLike || shouldRetweet || shouldRefactor) && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Max tweets per user</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={maxTweetsPerUser}
                  onChange={(e) => setMaxTweetsPerUser(parseInt(e.target.value) || 10)}
                  className="w-32 p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
                />
              </div>
            )}
          </div>

          {/* Comment Actions */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">Comment Actions</h3>
            <div className="grid grid-cols-2 gap-4">
              <ActionCheckbox
                checked={shouldComment}
                onChange={setShouldComment}
                icon={MessageCircle}
                label="Add Comment"
                color="text-twitter-blue"
              />
              <ActionCheckbox
                checked={useAIComment}
                onChange={setUseAIComment}
                icon={Sparkles}
                label="Use AI Comment"
                color="text-purple-500"
                disabled={!shouldComment}
              />
            </div>

            {shouldComment && !useAIComment && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Comment Template</label>
                <textarea
                  value={commentTemplate}
                  onChange={(e) => setCommentTemplate(e.target.value)}
                  placeholder="Enter your comment template..."
                  rows={3}
                  className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue resize-none"
                />
              </div>
            )}
          </div>

          {/* Start Button */}
          <div className="flex justify-end">
            <button
              onClick={() => processUsersMutation.mutate()}
              disabled={!canSubmit || processUsersMutation.isPending}
              className="flex items-center gap-2 px-8 py-3 bg-twitter-blue text-white rounded-full font-semibold hover:bg-twitter-blue/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-5 h-5" />
              {processUsersMutation.isPending ? 'Processing...' : `Start Bot (${usernames.length} users × ${selectedProfiles.length} profiles)`}
            </button>
          </div>

          {processUsersMutation.isSuccess && (
            <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
              <p className="text-green-500">User actions queued successfully!</p>
            </div>
          )}

          {processUsersMutation.isError && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
              <p className="text-red-500">
                {processUsersMutation.error instanceof Error
                  ? processUsersMutation.error.message
                  : 'Failed to queue actions'}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ActionCheckbox({
  checked,
  onChange,
  icon: Icon,
  label,
  color,
  disabled = false,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  icon: React.ElementType;
  label: string;
  color: string;
  disabled?: boolean;
}) {
  return (
    <label
      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } ${checked ? 'bg-[#283340]' : 'hover:bg-[#1e2732]'}`}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => !disabled && onChange(e.target.checked)}
        disabled={disabled}
        className="w-5 h-5 rounded"
      />
      <Icon className={`w-5 h-5 ${color}`} />
      <span className="text-white">{label}</span>
    </label>
  );
}

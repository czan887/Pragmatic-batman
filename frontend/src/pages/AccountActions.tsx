import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { UserMinus, Send, Sparkles, Play, AlertTriangle } from 'lucide-react';
import { profilesApi, actionsApi } from '../api/client';
import ProfileSelector from '../components/ProfileSelector';

export default function AccountActions() {
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);

  // Unfollow Non-Followers State
  const [maxUnfollow, setMaxUnfollow] = useState(50);
  const [unfollowDelay, setUnfollowDelay] = useState(30);

  // Create New Post State
  const [postText, setPostText] = useState('');
  const [useAIGeneration, setUseAIGeneration] = useState(false);
  const [aiTopic, setAITopic] = useState('');
  const [aiStyle, setAIStyle] = useState('informative');

  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  });

  const selectedProfile = selectedProfiles[0] || '';
  const selectedProfileData = profiles?.find(p => p.user_id === selectedProfile);

  const unfollowNonFollowersMutation = useMutation({
    mutationFn: async () => {
      const results = await Promise.all(
        selectedProfiles.map((profileId) =>
          actionsApi.unfollowNonFollowers({
            profile_id: profileId,
            max_unfollow: maxUnfollow,
            delay_between_unfollows: unfollowDelay,
          })
        )
      );
      return results;
    },
  });

  const postTweetMutation = useMutation({
    mutationFn: async () => {
      const results = await Promise.all(
        selectedProfiles.map((profileId) =>
          actionsApi.postTweet({
            profile_id: profileId,
            text: useAIGeneration ? null : postText,
            use_ai_generation: useAIGeneration,
            topic: useAIGeneration ? aiTopic : null,
            style: aiStyle,
          })
        )
      );
      return results;
    },
    onSuccess: () => {
      setPostText('');
      setAITopic('');
    },
  });

  const canPostTweet = useAIGeneration ? aiTopic.length > 0 : postText.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Account Actions</h1>
        <p className="text-gray-400">Manage account-level actions</p>
      </div>

      {/* Profile Selector */}
      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6">
        <ProfileSelector
          selectedProfiles={selectedProfiles}
          onChange={setSelectedProfiles}
          allowModeChange={true}
          label="Select Profiles"
        />

        {selectedProfileData && selectedProfiles.length === 1 && (
          <div className="mt-4 p-4 bg-[#1e2732] rounded-lg">
            <div className="flex items-center gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{selectedProfileData.followers_count}</p>
                <p className="text-sm text-gray-400">Followers</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{selectedProfileData.following_count}</p>
                <p className="text-sm text-gray-400">Following</p>
              </div>
              {selectedProfileData.domain_name && (
                <div className="ml-auto">
                  <p className="text-twitter-blue">@{selectedProfileData.domain_name}</p>
                </div>
              )}
            </div>
          </div>
        )}
        {selectedProfiles.length > 1 && (
          <div className="mt-4 p-4 bg-[#1e2732] rounded-lg">
            <p className="text-gray-400">{selectedProfiles.length} profiles selected</p>
          </div>
        )}
      </div>

      {selectedProfiles.length > 0 && (
        <>
          {/* Unfollow Non-Followers */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <div className="flex items-center gap-2">
              <UserMinus className="w-5 h-5 text-red-500" />
              <h3 className="text-lg font-semibold text-white">Unfollow Non-Followers</h3>
            </div>

            <p className="text-gray-400 text-sm">
              Automatically unfollow users who don't follow you back.
              This will fetch your following list, compare with followers, and unfollow non-followers.
            </p>

            <div className="bg-amber-500/10 border border-amber-500/50 rounded-lg p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="text-amber-500 font-semibold">Warning</p>
                <p className="text-amber-400">
                  This action will unfollow users. Make sure you want to proceed.
                  Twitter may rate-limit aggressive unfollowing.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Max users to unfollow</label>
                <input
                  type="number"
                  min={1}
                  max={200}
                  value={maxUnfollow}
                  onChange={(e) => setMaxUnfollow(parseInt(e.target.value) || 50)}
                  className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Delay between unfollows (seconds)</label>
                <input
                  type="number"
                  min={5}
                  max={300}
                  value={unfollowDelay}
                  onChange={(e) => setUnfollowDelay(parseInt(e.target.value) || 30)}
                  className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
                />
              </div>
            </div>

            <button
              onClick={() => unfollowNonFollowersMutation.mutate()}
              disabled={unfollowNonFollowersMutation.isPending}
              className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50"
            >
              <UserMinus className="w-5 h-5" />
              {unfollowNonFollowersMutation.isPending ? 'Processing...' : `Unfollow Non-Followers (max ${maxUnfollow})`}
            </button>

            {unfollowNonFollowersMutation.isSuccess && (
              <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
                <p className="text-green-500">Unfollow non-followers task queued successfully!</p>
              </div>
            )}
          </div>

          {/* Create New Post */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Send className="w-5 h-5 text-twitter-blue" />
              <h3 className="text-lg font-semibold text-white">Create New Post</h3>
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={useAIGeneration}
                onChange={(e) => setUseAIGeneration(e.target.checked)}
                className="w-5 h-5 rounded"
              />
              <Sparkles className="w-5 h-5 text-purple-500" />
              <span className="text-white">Use AI to generate post</span>
            </label>

            {useAIGeneration ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Topic / Prompt</label>
                  <input
                    type="text"
                    value={aiTopic}
                    onChange={(e) => setAITopic(e.target.value)}
                    placeholder="Enter a topic for the AI to write about..."
                    className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Style</label>
                  <select
                    value={aiStyle}
                    onChange={(e) => setAIStyle(e.target.value)}
                    className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
                  >
                    <option value="informative">Informative</option>
                    <option value="casual">Casual</option>
                    <option value="professional">Professional</option>
                    <option value="humorous">Humorous</option>
                  </select>
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Post Content</label>
                <textarea
                  value={postText}
                  onChange={(e) => setPostText(e.target.value)}
                  placeholder="What's happening?"
                  maxLength={280}
                  rows={4}
                  className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue resize-none"
                />
                <div className="flex justify-end mt-1">
                  <span className={`text-sm ${postText.length > 260 ? 'text-amber-500' : 'text-gray-500'}`}>
                    {postText.length}/280
                  </span>
                </div>
              </div>
            )}

            <button
              onClick={() => postTweetMutation.mutate()}
              disabled={!canPostTweet || postTweetMutation.isPending}
              className="flex items-center gap-2 px-6 py-3 bg-twitter-blue text-white rounded-full font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
            >
              <Play className="w-5 h-5" />
              {postTweetMutation.isPending ? 'Posting...' : 'Post'}
            </button>

            {postTweetMutation.isSuccess && (
              <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
                <p className="text-green-500">Post queued successfully!</p>
              </div>
            )}

            {postTweetMutation.isError && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
                <p className="text-red-500">
                  {postTweetMutation.error instanceof Error
                    ? postTweetMutation.error.message
                    : 'Failed to post'}
                </p>
              </div>
            )}
          </div>

          {/* Refactor Post */}
          <RefactorPostSection profileIds={selectedProfiles} />
        </>
      )}
    </div>
  );
}

function RefactorPostSection({ profileIds }: { profileIds: string[] }) {
  const [tweetUrl, setTweetUrl] = useState('');
  const [style, setStyle] = useState('similar');

  const refactorMutation = useMutation({
    mutationFn: async () => {
      const results = await Promise.all(
        profileIds.map((profileId) =>
          actionsApi.refactorPost({
            profile_id: profileId,
            original_tweet_url: tweetUrl,
            style,
          })
        )
      );
      return results;
    },
    onSuccess: () => {
      setTweetUrl('');
    },
  });

  const isValidUrl = tweetUrl.includes('twitter.com') || tweetUrl.includes('x.com');

  return (
    <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-purple-500" />
        <h3 className="text-lg font-semibold text-white">Refactor Post</h3>
      </div>

      <p className="text-gray-400 text-sm">
        Take an existing tweet, rewrite it with AI, and post the refactored version.
      </p>

      <div>
        <label className="block text-sm text-gray-400 mb-1">Original Tweet URL</label>
        <input
          type="text"
          value={tweetUrl}
          onChange={(e) => setTweetUrl(e.target.value)}
          placeholder="https://twitter.com/user/status/123456789"
          className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue font-mono text-sm"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">Refactor Style</label>
        <select
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
        >
          <option value="similar">Similar (keep same tone)</option>
          <option value="casual">Casual</option>
          <option value="professional">Professional</option>
          <option value="humorous">Humorous</option>
        </select>
      </div>

      <button
        onClick={() => refactorMutation.mutate()}
        disabled={!isValidUrl || refactorMutation.isPending}
        className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50"
      >
        <Sparkles className="w-5 h-5" />
        {refactorMutation.isPending ? 'Refactoring...' : 'Refactor & Post'}
      </button>

      {refactorMutation.isSuccess && (
        <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
          <p className="text-green-500">Refactor task queued successfully!</p>
        </div>
      )}

      {refactorMutation.isError && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
          <p className="text-red-500">
            {refactorMutation.error instanceof Error
              ? refactorMutation.error.message
              : 'Failed to refactor'}
          </p>
        </div>
      )}
    </div>
  );
}

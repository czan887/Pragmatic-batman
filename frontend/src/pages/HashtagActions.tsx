import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Hash, Heart, Repeat, MessageCircle, Sparkles, Trash2, Play } from 'lucide-react';
import { actionsApi } from '../api/client';
import FileImport from '../components/FileImport';
import ProfileSelector from '../components/ProfileSelector';

export default function HashtagActions() {
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const [hashtagInput, setHashtagInput] = useState('');
  const [commentTemplate, setCommentTemplate] = useState('');

  // Action checkboxes
  const [shouldLike, setShouldLike] = useState(false);
  const [shouldRetweet, setShouldRetweet] = useState(false);
  const [shouldComment, setShouldComment] = useState(false);
  const [useAIComment, setUseAIComment] = useState(true);
  const [shouldRefactor, setShouldRefactor] = useState(false);
  const [maxPostsPerHashtag, setMaxPostsPerHashtag] = useState(10);

  const parseHashtags = (text: string): string[] => {
    return text
      .split(/[\n,]+/)
      .map((item) => item.trim().replace(/^#/, ''))
      .filter((item) => item.length > 0);
  };

  const hashtags = parseHashtags(hashtagInput);

  const processHashtagsMutation = useMutation({
    mutationFn: async () => {
      const results = await Promise.all(
        selectedProfiles.map((profileId) =>
          actionsApi.processHashtag({
            profile_id: profileId,
            hashtags,
            should_like: shouldLike,
            should_retweet: shouldRetweet,
            should_comment: shouldComment,
            use_ai_comment: useAIComment,
            should_refactor: shouldRefactor,
            comment_template: shouldComment && !useAIComment ? commentTemplate : null,
            max_posts_per_hashtag: maxPostsPerHashtag,
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
    // Remove # prefix if present
    const cleanHashtags = items.map(item => item.replace(/^#/, ''));
    setHashtagInput((prev) => {
      const existing = parseHashtags(prev);
      const combined = [...new Set([...existing, ...cleanHashtags])];
      return combined.join('\n');
    });
  };

  const clearInput = () => {
    setHashtagInput('');
  };

  const hasSelectedAction = shouldLike || shouldRetweet || shouldComment || shouldRefactor;
  const canSubmit = selectedProfiles.length > 0 && hashtags.length > 0 && hasSelectedAction;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Hashtag Actions</h1>
        <p className="text-gray-400">Search hashtags and process posts</p>
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
          {/* Hashtag Input */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Hash className="w-5 h-5 text-twitter-blue" />
                <h3 className="text-lg font-semibold text-white">Hashtags</h3>
              </div>
              <div className="flex gap-2">
                <span className="text-sm text-gray-400">{hashtags.length} hashtags</span>
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
              value={hashtagInput}
              onChange={(e) => setHashtagInput(e.target.value)}
              placeholder="Enter hashtags (without # symbol, one per line)&#10;coding&#10;webdev&#10;javascript"
              rows={6}
              className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue resize-none font-mono text-sm"
            />

            {/* Show hashtags as chips */}
            {hashtags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {hashtags.slice(0, 10).map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-twitter-blue/20 text-twitter-blue rounded-full text-sm"
                  >
                    #{tag}
                  </span>
                ))}
                {hashtags.length > 10 && (
                  <span className="px-2 py-1 text-gray-400 text-sm">
                    +{hashtags.length - 10} more
                  </span>
                )}
              </div>
            )}

            <FileImport
              onImport={handleImport}
              label="Or import from file"
              placeholder="Drop file with hashtags"
            />
          </div>

          {/* Available Actions */}
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">Available Actions</h3>
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

            <div>
              <label className="block text-sm text-gray-400 mb-1">Max posts per hashtag</label>
              <input
                type="number"
                min={1}
                max={50}
                value={maxPostsPerHashtag}
                onChange={(e) => setMaxPostsPerHashtag(parseInt(e.target.value) || 10)}
                className="w-32 p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
            </div>
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
              onClick={() => processHashtagsMutation.mutate()}
              disabled={!canSubmit || processHashtagsMutation.isPending}
              className="flex items-center gap-2 px-8 py-3 bg-twitter-blue text-white rounded-full font-semibold hover:bg-twitter-blue/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-5 h-5" />
              {processHashtagsMutation.isPending ? 'Processing...' : `Start Bot (${hashtags.length} hashtags × ${selectedProfiles.length} profiles)`}
            </button>
          </div>

          {processHashtagsMutation.isSuccess && (
            <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
              <p className="text-green-500">Hashtag processing queued successfully!</p>
            </div>
          )}

          {processHashtagsMutation.isError && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
              <p className="text-red-500">
                {processHashtagsMutation.error instanceof Error
                  ? processHashtagsMutation.error.message
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

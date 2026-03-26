import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Key, Bot, Clock, Shield, CheckCircle, XCircle, Loader2, Eye, EyeOff } from 'lucide-react';
import { settingsApi } from '../api/client';

export default function Settings() {
  const queryClient = useQueryClient();

  // Fetch current settings
  const { data: currentSettings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
  });

  // Local state for form
  const [settings, setSettings] = useState({
    geminiApiKey: '',
    anthropicApiKey: '',
    adspowerApiKey: '',
    batchSize: 15,
    batchDelayMinutes: 60,
    minActionDelay: 2,
    maxActionDelay: 5,
    enableProfileAnalysis: true,
    enableBehaviorPlanning: true,
    enableMcpRecovery: true,
  });

  // API key visibility toggles
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);
  const [showAdspowerKey, setShowAdspowerKey] = useState(false);

  // Update local state when settings load
  useEffect(() => {
    if (currentSettings) {
      setSettings({
        geminiApiKey: '',
        anthropicApiKey: '',
        adspowerApiKey: '',
        batchSize: currentSettings.default_batch_size,
        batchDelayMinutes: currentSettings.default_batch_delay_minutes,
        minActionDelay: currentSettings.min_action_delay,
        maxActionDelay: currentSettings.max_action_delay,
        enableProfileAnalysis: currentSettings.enable_profile_analysis,
        enableBehaviorPlanning: currentSettings.enable_behavior_planning,
        enableMcpRecovery: currentSettings.enable_mcp_recovery,
      });
    }
  }, [currentSettings]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: () =>
      settingsApi.update({
        gemini_api_key: settings.geminiApiKey || undefined,
        anthropic_api_key: settings.anthropicApiKey || undefined,
        adspower_api_key: settings.adspowerApiKey || undefined,
        default_batch_size: settings.batchSize,
        default_batch_delay_minutes: settings.batchDelayMinutes,
        min_action_delay: settings.minActionDelay,
        max_action_delay: settings.maxActionDelay,
        enable_profile_analysis: settings.enableProfileAnalysis,
        enable_behavior_planning: settings.enableBehaviorPlanning,
        enable_mcp_recovery: settings.enableMcpRecovery,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      // Clear API key fields after save
      setSettings((prev) => ({
        ...prev,
        geminiApiKey: '',
        anthropicApiKey: '',
        adspowerApiKey: '',
      }));
    },
  });

  // Test mutations
  const testGeminiMutation = useMutation({
    mutationFn: settingsApi.testGemini,
  });

  const testAdspowerMutation = useMutation({
    mutationFn: settingsApi.testAdspower,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-twitter-blue animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400">Configure your Twitter bot</p>
      </div>

      <div className="grid gap-6 max-w-2xl">
        {/* API Keys */}
        <SettingsCard title="API Keys" icon={Key}>
          <div className="space-y-4">
            {/* Gemini API Key */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Gemini API Key</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showGeminiKey ? 'text' : 'password'}
                    value={settings.geminiApiKey}
                    onChange={(e) => setSettings({ ...settings, geminiApiKey: e.target.value })}
                    placeholder={currentSettings?.gemini_api_key || 'Enter new API key'}
                    className="w-full p-3 pr-10 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
                  />
                  <button
                    type="button"
                    onClick={() => setShowGeminiKey(!showGeminiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    {showGeminiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  onClick={() => testGeminiMutation.mutate()}
                  disabled={testGeminiMutation.isPending}
                  className="px-4 py-3 bg-[#283340] text-white rounded-lg hover:bg-[#38444d] disabled:opacity-50"
                >
                  {testGeminiMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Test'
                  )}
                </button>
              </div>
              {testGeminiMutation.isSuccess && (
                <p className="text-green-500 text-sm mt-1 flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Connection successful
                </p>
              )}
              {testGeminiMutation.isError && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <XCircle className="w-4 h-4" /> Connection failed
                </p>
              )}
            </div>

            {/* Anthropic API Key */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Anthropic API Key (Optional)</label>
              <div className="relative">
                <input
                  type={showAnthropicKey ? 'text' : 'password'}
                  value={settings.anthropicApiKey}
                  onChange={(e) => setSettings({ ...settings, anthropicApiKey: e.target.value })}
                  placeholder={currentSettings?.anthropic_api_key || 'Enter new API key'}
                  className="w-full p-3 pr-10 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
                />
                <button
                  type="button"
                  onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  {showAnthropicKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">Used for profile analysis (Claude)</p>
            </div>

            {/* AdsPower API Key */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">AdsPower API Key</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showAdspowerKey ? 'text' : 'password'}
                    value={settings.adspowerApiKey}
                    onChange={(e) => setSettings({ ...settings, adspowerApiKey: e.target.value })}
                    placeholder={currentSettings?.adspower_api_key || 'Enter new API key'}
                    className="w-full p-3 pr-10 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue"
                  />
                  <button
                    type="button"
                    onClick={() => setShowAdspowerKey(!showAdspowerKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    {showAdspowerKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  onClick={() => testAdspowerMutation.mutate()}
                  disabled={testAdspowerMutation.isPending}
                  className="px-4 py-3 bg-[#283340] text-white rounded-lg hover:bg-[#38444d] disabled:opacity-50"
                >
                  {testAdspowerMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Test'
                  )}
                </button>
              </div>
              {testAdspowerMutation.isSuccess && (
                <p className="text-green-500 text-sm mt-1 flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Connection successful
                </p>
              )}
              {testAdspowerMutation.isError && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <XCircle className="w-4 h-4" /> Connection failed
                </p>
              )}
            </div>
          </div>
        </SettingsCard>

        {/* Bot Settings */}
        <SettingsCard title="Bot Settings" icon={Bot}>
          <div className="grid gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Default Batch Size</label>
              <input
                type="number"
                min={1}
                max={100}
                value={settings.batchSize}
                onChange={(e) => setSettings({ ...settings, batchSize: parseInt(e.target.value) || 15 })}
                className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
              <p className="text-xs text-gray-500 mt-1">Number of actions per batch</p>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Batch Delay (minutes)</label>
              <input
                type="number"
                min={1}
                max={240}
                value={settings.batchDelayMinutes}
                onChange={(e) =>
                  setSettings({ ...settings, batchDelayMinutes: parseInt(e.target.value) || 60 })
                }
                className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
              <p className="text-xs text-gray-500 mt-1">Wait time between batches</p>
            </div>
          </div>
        </SettingsCard>

        {/* Timing Settings */}
        <SettingsCard title="Timing" icon={Clock}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Min Action Delay (sec)</label>
              <input
                type="number"
                min={1}
                max={30}
                step={0.5}
                value={settings.minActionDelay}
                onChange={(e) =>
                  setSettings({ ...settings, minActionDelay: parseFloat(e.target.value) || 2 })
                }
                className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Max Action Delay (sec)</label>
              <input
                type="number"
                min={2}
                max={60}
                step={0.5}
                value={settings.maxActionDelay}
                onChange={(e) =>
                  setSettings({ ...settings, maxActionDelay: parseFloat(e.target.value) || 5 })
                }
                className="w-full p-3 bg-[#1e2732] border border-[#38444d] rounded-lg text-white focus:outline-none focus:border-twitter-blue"
              />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">Random delay range between actions</p>
        </SettingsCard>

        {/* AI Features */}
        <SettingsCard title="AI Features" icon={Shield}>
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="text-white">Profile Analysis</p>
                <p className="text-xs text-gray-500">Use AI to analyze profiles before following</p>
              </div>
              <input
                type="checkbox"
                checked={settings.enableProfileAnalysis}
                onChange={(e) =>
                  setSettings({ ...settings, enableProfileAnalysis: e.target.checked })
                }
                className="w-5 h-5"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="text-white">Behavior Planning</p>
                <p className="text-xs text-gray-500">Plan human-like action patterns</p>
              </div>
              <input
                type="checkbox"
                checked={settings.enableBehaviorPlanning}
                onChange={(e) =>
                  setSettings({ ...settings, enableBehaviorPlanning: e.target.checked })
                }
                className="w-5 h-5"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="text-white">MCP Self-Healing</p>
                <p className="text-xs text-gray-500">Use AI to recover from selector failures</p>
              </div>
              <input
                type="checkbox"
                checked={settings.enableMcpRecovery}
                onChange={(e) =>
                  setSettings({ ...settings, enableMcpRecovery: e.target.checked })
                }
                className="w-5 h-5"
              />
            </label>
          </div>
        </SettingsCard>

        {/* Save Button */}
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-twitter-blue text-white rounded-lg font-semibold hover:bg-twitter-blue/90 disabled:opacity-50"
        >
          {saveMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Save className="w-5 h-5" />
          )}
          {saveMutation.isPending ? 'Saving...' : 'Save Settings'}
        </button>

        {saveMutation.isSuccess && (
          <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
            <p className="text-green-500 flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Settings saved successfully! Some settings may require a restart.
            </p>
          </div>
        )}

        {saveMutation.isError && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
            <p className="text-red-500">
              {saveMutation.error instanceof Error
                ? saveMutation.error.message
                : 'Failed to save settings'}
            </p>
          </div>
        )}

        {/* Current Settings Info */}
        {currentSettings && (
          <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Current Configuration</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-400">AI Model</p>
                <p className="text-white">{currentSettings.ai_model}</p>
              </div>
              <div>
                <p className="text-gray-400">AdsPower URL</p>
                <p className="text-white font-mono text-xs">{currentSettings.adspower_url}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SettingsCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[#192734] rounded-xl border border-[#38444d] p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-twitter-blue/10 rounded-lg">
          <Icon className="w-5 h-5 text-twitter-blue" />
        </div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      {children}
    </div>
  );
}

import { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Send, Bot as BotIcon, User, Loader2, Trash2, Settings2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { botApi, profilesApi } from '../api/client';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  actions?: BotAction[];
  status?: 'pending' | 'executing' | 'completed' | 'error';
}

interface BotAction {
  type: string;
  target?: string;
  params?: Record<string, unknown>;
  status: 'pending' | 'executing' | 'completed' | 'error';
  result?: string;
}

export default function Bot() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I'm your Twitter Bot Assistant powered by Claude AI. I can help you automate Twitter actions using natural language commands.

**Here are some things I can do:**
- Follow/Unfollow users
- Like, retweet, or comment on posts
- Process hashtags and user timelines
- Create AI-generated posts
- Manage multiple profiles at once

**Example commands:**
- "Follow @elonmusk using profile 1"
- "Like and retweet the latest 5 posts from #AI"
- "Post a tweet about the future of AI"
- "Unfollow all non-followers"

Just tell me what you want to do!`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  });

  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await botApi.sendMessage({
        message,
        profile_id: selectedProfile || undefined,
        conversation_history: messages.map(m => ({
          role: m.role,
          content: m.content,
        })),
      });
      return response;
    },
    onMutate: (message) => {
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      setInput('');
    },
    onSuccess: (response) => {
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        actions: response.actions,
        status: response.actions?.length ? 'pending' : undefined,
      };
      setMessages(prev => [...prev, assistantMessage]);
    },
    onError: (error) => {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to process message'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    },
  });

  const executeActionsMutation = useMutation({
    mutationFn: async (messageId: string) => {
      const message = messages.find(m => m.id === messageId);
      if (!message?.actions) {
        throw new Error('No actions to execute');
      }

      // Update message status
      setMessages(prev => prev.map(m =>
        m.id === messageId ? { ...m, status: 'executing' } : m
      ));

      const response = await botApi.executeActions({
        actions: message.actions,
        profile_id: selectedProfile || undefined,
      });

      return { messageId, result: response };
    },
    onSuccess: (data) => {
      if (!data) return;
      const { messageId, result } = data;
      setMessages(prev => prev.map(m =>
        m.id === messageId
          ? {
              ...m,
              status: 'completed',
              actions: m.actions?.map((a, i) => ({
                ...a,
                status: 'completed' as const,
                result: result.results[i],
              })),
            }
          : m
      ));
    },
    onError: (_error, messageId) => {
      setMessages(prev => prev.map(m =>
        m.id === messageId ? { ...m, status: 'error' } : m
      ));
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sendMessageMutation.isPending) return;
    sendMessageMutation.mutate(input.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearChat = () => {
    setMessages([messages[0]]); // Keep welcome message
  };

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[#38444d]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center">
            <BotIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">AI Bot Assistant</h1>
            <p className="text-sm text-gray-400">Powered by Claude AI with MCP Integration</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Profile Selector */}
          <select
            value={selectedProfile}
            onChange={(e) => setSelectedProfile(e.target.value)}
            className="p-2 bg-[#1e2732] border border-[#38444d] rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
          >
            <option value="">Auto-select Profile</option>
            {profiles?.map((profile) => (
              <option key={profile.user_id} value={profile.user_id}>
                {profile.domain_name || profile.name || profile.user_id}
              </option>
            ))}
          </select>
          <button
            onClick={clearChat}
            className="p-2 text-gray-400 hover:text-white hover:bg-[#283340] rounded-lg"
            title="Clear chat"
          >
            <Trash2 className="w-5 h-5" />
          </button>
          <button
            className="p-2 text-gray-400 hover:text-white hover:bg-[#283340] rounded-lg"
            title="Settings"
          >
            <Settings2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onExecuteActions={() => executeActionsMutation.mutate(message.id)}
            isExecuting={executeActionsMutation.isPending && executeActionsMutation.variables === message.id}
          />
        ))}
        {sendMessageMutation.isPending && (
          <div className="flex items-center gap-2 text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-[#38444d]">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tell me what you want to do..."
              rows={1}
              className="w-full p-3 pr-12 bg-[#1e2732] border border-[#38444d] rounded-xl text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500 resize-none"
              style={{ minHeight: '48px', maxHeight: '150px' }}
            />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || sendMessageMutation.isPending}
            className="px-4 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}

function MessageBubble({
  message,
  onExecuteActions,
  isExecuting,
}: {
  message: ChatMessage;
  onExecuteActions: () => void;
  isExecuting: boolean;
}) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
          isUser
            ? 'bg-twitter-blue'
            : isSystem
            ? 'bg-red-600'
            : 'bg-purple-600'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : isSystem ? (
          <AlertCircle className="w-4 h-4 text-white" />
        ) : (
          <BotIcon className="w-4 h-4 text-white" />
        )}
      </div>
      <div
        className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}
      >
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-twitter-blue text-white rounded-tr-sm'
              : isSystem
              ? 'bg-red-500/20 text-red-400 border border-red-500/50 rounded-tl-sm'
              : 'bg-[#192734] text-white border border-[#38444d] rounded-tl-sm'
          }`}
        >
          <div className="whitespace-pre-wrap text-sm markdown-content">
            {message.content.split('\n').map((line, i) => {
              // Simple markdown-like rendering
              if (line.startsWith('**') && line.endsWith('**')) {
                return <p key={i} className="font-bold">{line.slice(2, -2)}</p>;
              }
              if (line.startsWith('- ')) {
                return <p key={i} className="ml-2">{line}</p>;
              }
              return <p key={i}>{line || '\u00A0'}</p>;
            })}
          </div>
        </div>

        {/* Actions Section */}
        {message.actions && message.actions.length > 0 && (
          <div className="mt-2 p-3 bg-[#1e2732] rounded-lg border border-[#38444d]">
            <p className="text-xs text-gray-400 mb-2">Planned Actions:</p>
            <ul className="space-y-1">
              {message.actions.map((action, index) => (
                <li key={index} className="flex items-center gap-2 text-sm">
                  {action.status === 'completed' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : action.status === 'executing' ? (
                    <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />
                  ) : action.status === 'error' ? (
                    <AlertCircle className="w-4 h-4 text-red-500" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-gray-500" />
                  )}
                  <span className="text-gray-300">
                    {action.type}: {action.target || 'N/A'}
                  </span>
                  {action.result && (
                    <span className="text-gray-500 text-xs">({action.result})</span>
                  )}
                </li>
              ))}
            </ul>
            {message.status === 'pending' && (
              <button
                onClick={onExecuteActions}
                disabled={isExecuting}
                className="mt-3 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-semibold hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isExecuting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  'Execute Actions'
                )}
              </button>
            )}
            {message.status === 'completed' && (
              <p className="mt-2 text-green-500 text-sm flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" />
                All actions completed
              </p>
            )}
          </div>
        )}

        <span className="text-xs text-gray-500 mt-1 block">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}

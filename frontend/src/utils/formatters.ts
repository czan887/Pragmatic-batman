/**
 * Shared formatting utilities for the Twitter Bot frontend
 */

import type { TaskStatus } from '../types';

/**
 * Format a task type string to human readable format
 * @example "follow_user" -> "Follow User"
 */
export function formatTaskType(type: string): string {
  return type
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Get CSS color class for a task status
 */
export function getStatusColor(status: TaskStatus): string {
  switch (status) {
    case 'pending':
      return 'bg-yellow-500/10 text-yellow-500';
    case 'in_progress':
      return 'bg-twitter-blue/10 text-twitter-blue';
    case 'completed':
      return 'bg-green-500/10 text-green-500';
    case 'failed':
      return 'bg-red-500/10 text-red-500';
    case 'cancelled':
      return 'bg-gray-500/10 text-gray-500';
    default:
      return 'bg-gray-500/10 text-gray-500';
  }
}

/**
 * Get CSS color class for a log level
 */
export function getLevelColor(level: string): string {
  switch (level) {
    case 'SUCCESS':
      return 'text-green-500';
    case 'WARNING':
      return 'text-yellow-500';
    case 'ERROR':
      return 'text-red-500';
    case 'DEBUG':
      return 'text-gray-500';
    default:
      return 'text-twitter-blue';
  }
}

/**
 * Format timestamp to time only (HH:MM:SS)
 */
export function formatTime(timestamp: string | null): string {
  if (!timestamp) return '--:--:--';
  const date = new Date(timestamp);
  return isNaN(date.getTime()) ? '--:--:--' : date.toLocaleTimeString();
}

/**
 * Format timestamp to full date and time
 */
export function formatDateTime(timestamp: string | null): string {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return isNaN(date.getTime()) ? '-' : date.toLocaleString();
}

/**
 * Format a profile name with fallback to serial number
 */
export function formatProfileName(profile: { name?: string | null; serial_number?: string }): string {
  return profile.name || profile.serial_number || 'Unknown';
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(timestamp: string | null): string {
  if (!timestamp) return '-';

  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return '-';

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

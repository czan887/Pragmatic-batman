/**
 * Notification Service Bridge
 *
 * Allows axios interceptor and other non-React code to access
 * notification functions from the NotificationContext.
 */

type NotificationFunction = (message: string, title?: string, suggestion?: string) => void;

interface NotificationService {
  showSuccess: NotificationFunction;
  showError: NotificationFunction;
  showWarning: NotificationFunction;
  showInfo: NotificationFunction;
}

let notificationService: NotificationService | null = null;

/**
 * Initialize the notification service with context functions
 * Called from App.tsx after NotificationContext is available
 */
export function initNotificationService(service: NotificationService) {
  notificationService = service;
}

/**
 * Get the notification service
 * Returns null if not initialized
 */
export function getNotificationService(): NotificationService | null {
  return notificationService;
}

/**
 * Show an error notification via the service
 * Safe to call even if service is not initialized
 */
export function showErrorNotification(message: string, title?: string, suggestion?: string) {
  if (notificationService) {
    notificationService.showError(message, title, suggestion);
  } else {
    console.error('[Notification Service] Not initialized:', title, message);
  }
}

/**
 * Show a success notification via the service
 */
export function showSuccessNotification(message: string, title?: string) {
  if (notificationService) {
    notificationService.showSuccess(message, title);
  } else {
    console.log('[Notification Service] Not initialized:', title, message);
  }
}

/**
 * Show a warning notification via the service
 */
export function showWarningNotification(message: string, title?: string) {
  if (notificationService) {
    notificationService.showWarning(message, title);
  } else {
    console.warn('[Notification Service] Not initialized:', title, message);
  }
}

/**
 * Show an info notification via the service
 */
export function showInfoNotification(message: string, title?: string) {
  if (notificationService) {
    notificationService.showInfo(message, title);
  } else {
    console.info('[Notification Service] Not initialized:', title, message);
  }
}

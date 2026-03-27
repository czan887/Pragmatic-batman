import { createContext, useContext, useCallback, ReactNode } from 'react';
import { Toaster, toast } from 'sonner';

interface NotificationContextType {
  showSuccess: (message: string, title?: string) => void;
  showError: (message: string, title?: string, suggestion?: string) => void;
  showWarning: (message: string, title?: string) => void;
  showInfo: (message: string, title?: string) => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

interface NotificationProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const showSuccess = useCallback((message: string, title?: string) => {
    toast.success(message, {
      description: title ? undefined : undefined,
      duration: 4000,
    });
  }, []);

  const showError = useCallback((message: string, title?: string, suggestion?: string) => {
    toast.error(title || 'Error', {
      description: suggestion ? `${message}\n${suggestion}` : message,
      duration: 6000,
    });
  }, []);

  const showWarning = useCallback((message: string, title?: string) => {
    toast.warning(title || 'Warning', {
      description: message,
      duration: 5000,
    });
  }, []);

  const showInfo = useCallback((message: string, title?: string) => {
    toast.info(title || 'Info', {
      description: message,
      duration: 4000,
    });
  }, []);

  return (
    <NotificationContext.Provider value={{ showSuccess, showError, showWarning, showInfo }}>
      {children}
      <Toaster
        position="bottom-right"
        theme="dark"
        richColors
        closeButton
        toastOptions={{
          style: {
            background: '#192734',
            border: '1px solid #38444d',
            color: '#fff',
          },
        }}
      />
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

export { NotificationContext };

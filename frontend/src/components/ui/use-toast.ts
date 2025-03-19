'use client';

import { useState } from 'react';

interface ToastProps {
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
  duration?: number;
}

const DEFAULT_TOAST_DURATION = 5000; // 5 seconds

export function useToast() {
  const [toasts, setToasts] = useState<(ToastProps & { id: string, open: boolean })[]>([]);

  const toast = (props: ToastProps) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast = { ...props, id, open: true };
    
    setToasts(prev => [...prev, newToast]);
    
    if (props.duration !== 0) {
      setTimeout(() => {
        dismiss(id);
      }, props.duration || DEFAULT_TOAST_DURATION);
    }
    
    return { id };
  };

  const dismiss = (id?: string) => {
    if (id) {
      setToasts(prev => 
        prev.map(t => t.id === id ? { ...t, open: false } : t)
      );
      
      // Remove from state after animation would complete
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 300);
    } else {
      // Dismiss all
      setToasts(prev => prev.map(t => ({ ...t, open: false })));
      
      setTimeout(() => {
        setToasts([]);
      }, 300);
    }
  };

  return {
    toast,
    dismiss,
    toasts
  };
}

export { useToast as toast };
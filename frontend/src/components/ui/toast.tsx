'use client';

import React from 'react';

interface ToastProps {
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

const Toast: React.FC<ToastProps> = ({ 
  title, 
  description, 
  variant = 'default',
  open,
  children 
}) => {
  if (!open) return null;
  
  return (
    <div className={`fixed bottom-4 right-4 max-w-md p-4 rounded-md shadow-lg ${
      variant === 'destructive' ? 'bg-red-600 text-white' : 'bg-white text-black'
    }`}>
      {title && <div className="font-medium">{title}</div>}
      {description && <div className="text-sm mt-1">{description}</div>}
      {children}
    </div>
  );
};

export { Toast };
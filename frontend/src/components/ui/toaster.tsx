'use client';

import { useToast } from './use-toast';
import { Toast } from './toast';

export function Toaster() {
  const { toasts } = useToast();
  
  return (
    <>
      {toasts.map(({ id, title, description, open, variant }) => (
        <Toast 
          key={id}
          title={title}
          description={description}
          variant={variant}
          open={open}
        />
      ))}
    </>
  );
}
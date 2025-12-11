import * as React from 'react';
import { cn } from '@/lib/utils';

/**
 * Skeleton component
 * Loading placeholder with animated pulse
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-muted', className)}
      {...props}
    />
  );
}

export { Skeleton };


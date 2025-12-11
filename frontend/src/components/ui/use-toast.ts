/**
 * Placeholder for shadcn/ui toast hook
 * This will be replaced with actual shadcn/ui toast implementation
 */

export function useToast() {
  return {
    toast: ({ title, description, variant }: { title?: string; description?: string; variant?: string }) => {
      console.log('Toast:', { title, description, variant });
    }
  };
}


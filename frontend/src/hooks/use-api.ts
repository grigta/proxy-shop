/**
 * React Query hooks for all API operations
 * Provides type-safe data fetching and mutations with caching
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ui/use-toast';
import type {
  UserProfile,
  UserHistoryResponse,
  ActivateCouponRequest,
  ActivateCouponResponse,
  ReferralsResponse,
  ProductsListResponse,
  CountryListItem,
  StateListItem,
  ProxyType,
  PurchaseRequest,
  PurchaseResponse,
  PurchaseHistoryResponse,
  ValidateProxyResponse,
  ExtendProxyRequest,
  ExtendProxyResponse,
  CreatePaymentRequest,
  CreatePaymentResponse,
  TransactionHistoryResponse
} from '@/types/api';
import { QUERY_KEYS } from '@/lib/constants';

// ============================================
// User Hooks
// ============================================

/**
 * Get user profile
 * Updates auth store on success
 */
export function useUserProfile(options?: Omit<UseQueryOptions<UserProfile>, 'queryKey' | 'queryFn'>) {
  const { setUser, logout, accessToken, user } = useAuthStore();

  return useQuery<UserProfile>({
    queryKey: QUERY_KEYS.user.profile,
    queryFn: async () => {
      try {
        const profile = await apiClient.getProfile();
        setUser(profile);
        return profile;
      } catch (error: any) {
        if (error.response?.status === 401) {
          logout();
        }
        throw error;
      }
    },
    // Only fetch if we have an access token
    enabled: !!accessToken && options?.enabled !== false,
    // Use existing user data as initialData to avoid flickering
    initialData: user || undefined,
    ...options
  });
}

/**
 * Get user history with pagination and filtering
 */
export function useUserHistory(
  params: { action_type?: string; page?: number; page_size?: number } = {},
  options?: Omit<UseQueryOptions<UserHistoryResponse>, 'queryKey' | 'queryFn'>
) {
  const { accessToken } = useAuthStore();

  return useQuery<UserHistoryResponse>({
    queryKey: QUERY_KEYS.user.history(params),
    queryFn: () => apiClient.getHistory(params),
    enabled: !!accessToken && options?.enabled !== false,
    ...options
  });
}

/**
 * Activate coupon mutation
 * Invalidates user profile on success
 */
export function useActivateCoupon() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<ActivateCouponResponse, Error, ActivateCouponRequest>({
    mutationFn: (data) => apiClient.activateCoupon(data),
    onSuccess: (data) => {
      // Invalidate user profile to refresh balance
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.user.profile });
      
      toast({
        title: 'Success',
        description: data.message,
        variant: 'default'
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to activate coupon',
        variant: 'destructive'
      });
    }
  });
}

/**
 * Get user referrals with pagination
 */
export function useReferrals(
  userId: number,
  params: { page?: number; page_size?: number } = {},
  options?: Omit<UseQueryOptions<ReferralsResponse>, 'queryKey' | 'queryFn'>
) {
  const { accessToken } = useAuthStore();

  return useQuery<ReferralsResponse>({
    queryKey: QUERY_KEYS.user.referrals(userId, params),
    queryFn: () => apiClient.getReferrals(userId, params),
    enabled: !!accessToken && !!userId && options?.enabled !== false,
    ...options
  });
}

// ============================================
// Products Hooks
// ============================================

/**
 * Get SOCKS5 products with filters and pagination
 * Keeps previous data for smooth transitions
 */
export function useSocks5Products(
  params: {
    country: string;
    state?: string;
    city?: string;
    zip?: string;
    random?: boolean;
    page?: number;
    page_size?: number;
  },
  options?: Omit<UseQueryOptions<ProductsListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ProductsListResponse>({
    queryKey: QUERY_KEYS.products.socks5(params),
    queryFn: () => apiClient.getSocks5Products(params),
    enabled: !!params.country, // Only fetch if country is selected
    ...options
  });
}

/**
 * Get PPTP products with filters and pagination
 */
export function usePptpProducts(
  params: {
    country: string;
    state?: string;
    city?: string;
    zip?: string;
    random?: boolean;
    page?: number;
    page_size?: number;
  },
  options?: Omit<UseQueryOptions<ProductsListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ProductsListResponse>({
    queryKey: QUERY_KEYS.products.pptp(params),
    queryFn: () => apiClient.getPptpProducts(params),
    enabled: !!params.country,
    ...options
  });
}

/**
 * Get available countries for proxy type
 * Cached for 5 minutes
 */
export function useCountries(
  proxyType: ProxyType,
  options?: Omit<UseQueryOptions<CountryListItem[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CountryListItem[]>({
    queryKey: QUERY_KEYS.products.countries(proxyType),
    queryFn: () => apiClient.getCountries(proxyType),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options
  });
}

/**
 * Get available states for country
 * Cached for 5 minutes
 */
export function useStates(
  country: string,
  proxyType: ProxyType,
  options?: Omit<UseQueryOptions<StateListItem[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<StateListItem[]>({
    queryKey: QUERY_KEYS.products.states(country, proxyType),
    queryFn: () => apiClient.getStates(country, proxyType),
    enabled: !!country,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options
  });
}

// ============================================
// Purchase Hooks
// ============================================

/**
 * Purchase SOCKS5 proxy mutation
 * Invalidates user profile and purchase history on success
 */
export function usePurchaseSocks5() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { setUser } = useAuthStore();

  return useMutation<PurchaseResponse, Error, PurchaseRequest>({
    mutationFn: (data) => apiClient.purchaseSocks5(data),
    onSuccess: (data) => {
      // Update balance in auth store
      const currentUser = useAuthStore.getState().user;
      if (currentUser) {
        setUser({ ...currentUser, balance: data.new_balance });
      }

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.user.profile });
      queryClient.invalidateQueries({ queryKey: ['purchase', 'history'] });

      toast({
        title: 'Покупка совершена успешно!',
        description: `ID Покупки: ${data.order_id}, Цена: ${data.price}$, Страна: ${data.country}`,
        variant: 'default'
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Ошибка покупки',
        description: error.response?.data?.detail || 'Попробуйте еще раз, или напишите в поддержку',
        variant: 'destructive'
      });
    }
  });
}

/**
 * Purchase PPTP proxy mutation
 */
export function usePurchasePptp() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { setUser } = useAuthStore();

  return useMutation<PurchaseResponse, Error, Omit<PurchaseRequest, 'quantity'>>({
    mutationFn: (data) => apiClient.purchasePptp(data),
    onSuccess: (data) => {
      // Update balance
      const currentUser = useAuthStore.getState().user;
      if (currentUser) {
        setUser({ ...currentUser, balance: data.new_balance });
      }

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.user.profile });
      queryClient.invalidateQueries({ queryKey: ['purchase', 'history'] });

      toast({
        title: 'Покупка совершена успешно!',
        description: `ID: ${data.order_id}, Цена: ${data.price}$, Страна: ${data.country}, Штат: ${data.state}`,
        variant: 'default'
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Ошибка покупки',
        description: error.response?.data?.detail || 'Попробуйте еще раз, или напишите в поддержку',
        variant: 'destructive'
      });
    }
  });
}

/**
 * Get purchase history with pagination
 */
export function usePurchaseHistory(
  userId: number,
  params: { proxy_type?: ProxyType; page?: number; page_size?: number } = {},
  options?: Omit<UseQueryOptions<PurchaseHistoryResponse>, 'queryKey' | 'queryFn'>
) {
  const { accessToken } = useAuthStore();

  return useQuery<PurchaseHistoryResponse>({
    queryKey: QUERY_KEYS.purchase.history(userId, params),
    queryFn: () => apiClient.getPurchaseHistory(userId, params),
    enabled: !!accessToken && !!userId && options?.enabled !== false,
    ...options
  });
}

/**
 * Validate proxy status mutation
 * Shows toast with validation result
 */
export function useValidateProxy() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<ValidateProxyResponse, Error, { proxyId: number; proxyType: ProxyType }>({
    mutationFn: ({ proxyId, proxyType }) => apiClient.validateProxy(proxyId, proxyType),
    onSuccess: (data) => {
      // Invalidate purchase history if refund was processed
      if (data.refund_eligible && !data.online) {
        queryClient.invalidateQueries({ queryKey: ['purchase', 'history'] });
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.user.profile });
      }

      // Show formatted message from backend
      toast({
        title: data.online ? 'Прокси онлайн!' : 'Прокси офлайн',
        description: data.message,
        variant: data.online ? 'default' : 'destructive'
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Ошибка проверки',
        description: error.response?.data?.detail || 'Не удалось проверить прокси',
        variant: 'destructive'
      });
    }
  });
}

/**
 * Extend proxy duration mutation
 * Updates balance and invalidates queries on success
 */
export function useExtendProxy() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { setUser } = useAuthStore();

  return useMutation<
    ExtendProxyResponse,
    Error,
    { proxyId: number; proxyType: ProxyType; data: ExtendProxyRequest }
  >({
    mutationFn: ({ proxyId, proxyType, data }) => apiClient.extendProxy(proxyId, proxyType, data),
    onSuccess: (data) => {
      // Update balance
      const currentUser = useAuthStore.getState().user;
      if (currentUser) {
        setUser({ ...currentUser, balance: data.new_balance });
      }

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.user.profile });
      queryClient.invalidateQueries({ queryKey: ['purchase', 'history'] });

      // Show formatted message from backend
      toast({
        title: 'Прокси продлен!',
        description: data.message,
        variant: 'default'
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Ошибка продления',
        description: error.response?.data?.detail || 'Не удалось продлить прокси',
        variant: 'destructive'
      });
    }
  });
}

// ============================================
// Payment Hooks
// ============================================

/**
 * Create Heleket payment invoice with universal payment link
 */
export function useGenerateAddress() {
  const { toast } = useToast();

  return useMutation<CreatePaymentResponse, Error, CreatePaymentRequest>({
    mutationFn: (data) => apiClient.generateAddress(data),
    onError: (error: any) => {
      toast({
        title: 'Ошибка создания платежа',
        description: error.response?.data?.detail || 'Не удалось создать платеж',
        variant: 'destructive'
      });
    }
  });
}

/**
 * Get payment history with pagination
 */
export function usePaymentHistory(
  userId: number,
  params: { page?: number; page_size?: number } = {},
  options?: Omit<UseQueryOptions<TransactionHistoryResponse>, 'queryKey' | 'queryFn'>
) {
  const { accessToken } = useAuthStore();

  return useQuery<TransactionHistoryResponse>({
    queryKey: QUERY_KEYS.payment.history(userId, params),
    queryFn: () => apiClient.getPaymentHistory(userId, params),
    enabled: !!accessToken && !!userId && options?.enabled !== false,
    ...options
  });
}


import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { apiClient } from '@/lib/api-client';
import { copyToClipboard as copyText } from '@/lib/clipboard';
import { ProxyItem, PurchaseResponse, APIError } from '@/types/api';
import { AxiosError } from 'axios';

type ModalState = 'none' | 'confirm' | 'success' | 'error';

interface PurchaseFlowConfig {
  purchaseFunction: (
    proxy: ProxyItem,
    couponCode: string | undefined
  ) => Promise<PurchaseResponse>;
  unavailableMessageSocks: string;
  unavailableMessagePptp: string;
  proxyType: 'socks' | 'pptp';
}

export const usePurchaseFlow = (config: PurchaseFlowConfig) => {
  const { user, updateUser } = useAuth();

  // Purchase modal states
  const [selectedProxy, setSelectedProxy] = useState<ProxyItem | null>(null);
  const [modalState, setModalState] = useState<ModalState>('none');
  const [couponCode, setCouponCode] = useState<string>('');
  const [purchasing, setPurchasing] = useState<boolean>(false);
  const [purchaseResponse, setPurchaseResponse] = useState<PurchaseResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Handle buy button click
  const handleBuyClick = (proxy: ProxyItem) => {
    if (!user) {
      window.location.href = '/auth';
      return;
    }

    setSelectedProxy(proxy);
    setModalState('confirm');
    setCouponCode('');
    setErrorMessage('');
  };

  // Handle purchase
  const handlePurchase = async () => {
    if (!user) {
      window.location.href = '/auth';
      return;
    }

    if (!selectedProxy) return;

    // Check balance
    if (parseFloat(user.balance) < parseFloat(selectedProxy.price)) {
      setErrorMessage('Insufficient balance. Please deposit funds.');
      setModalState('error');
      return;
    }

    setPurchasing(true);
    try {
      const response = await config.purchaseFunction(
        selectedProxy,
        couponCode || undefined
      );

      setPurchaseResponse(response);

      // Update user profile with new balance
      const updatedProfile = await apiClient.getProfile();
      updateUser(updatedProfile);

      setModalState('success');
    } catch (err) {
      const axiosError = err as AxiosError<APIError>;
      const detail = axiosError.response?.data?.detail || 'Purchase failed. Please try again.';
      const errorCode = axiosError.response?.data?.error_code;

      // Parse error message with error_code priority
      let errorMsg = detail;

      // Check error_code first
      if (errorCode === 'INSUFFICIENT_FUNDS') {
        errorMsg = 'Insufficient funds. Please deposit more balance.';
      } else if (errorCode === 'PROXY_UNAVAILABLE') {
        errorMsg = config.unavailableMessageSocks;
      } else if (errorCode === 'NO_SERVERS_AVAILABLE') {
        errorMsg = config.unavailableMessagePptp;
      }
      // Fallback to HTTP status
      else if (axiosError.response?.status === 404) {
        errorMsg = config.proxyType === 'socks' 
          ? config.unavailableMessageSocks
          : config.unavailableMessagePptp;
      }
      // Last resort: parse detail text
      else if (detail.toLowerCase().includes('insufficient') || detail.toLowerCase().includes('balance')) {
        errorMsg = 'Insufficient funds. Please deposit more balance.';
      }

      setErrorMessage(errorMsg);
      setModalState('error');
    } finally {
      setPurchasing(false);
    }
  };

  // Handle copy to clipboard
  const handleCopy = async (field: string, value: string) => {
    const success = await copyText(value);
    if (success) {
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    }
  };

  // Close modal and reset states
  const closeModal = () => {
    setModalState('none');
    setSelectedProxy(null);
    setPurchaseResponse(null);
    setErrorMessage('');
    setCouponCode('');
    setCopiedField(null);
  };

  return {
    user,
    selectedProxy,
    modalState,
    couponCode,
    setCouponCode,
    purchasing,
    purchaseResponse,
    errorMessage,
    copiedField,
    handleBuyClick,
    handlePurchase,
    handleCopy,
    closeModal,
  };
};


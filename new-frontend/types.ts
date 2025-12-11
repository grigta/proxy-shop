export enum SpeedLevel {
  FAST = 'Fast',
  MODERATE = 'Moderate',
  SLOW = 'Slow'
}

export interface Tier {
  name: string;
  code: string;
  proxyCount: string;
  discount: string;
  features: string[];
  isCurrent?: boolean;
}

export interface FaqItem {
  question: string;
  answer: string;
}
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Utility function for merging Tailwind CSS classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Comprehensive timezone utilities for CogniVox Frontend
 */

export const getCurrentDateTime = (): string => {
  return new Date().toISOString();
};

export const getClientTimezone = () => {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const now = new Date();
  const offset = -now.getTimezoneOffset();
  const offsetHours = Math.floor(Math.abs(offset) / 60);
  const offsetMinutes = Math.abs(offset) % 60;
  
  // Use string padding compatible with older TypeScript versions
  const offsetHoursStr = offsetHours < 10 ? '0' + offsetHours : offsetHours.toString();
  const offsetMinutesStr = offsetMinutes < 10 ? '0' + offsetMinutes : offsetMinutes.toString();
  const offsetString = `${offset >= 0 ? '+' : '-'}${offsetHoursStr}:${offsetMinutesStr}`;
  
  return { timezone, offset, offsetString };
};

export const formatToLocalTimezone = (utcTimestamp: string | Date): string => {
  try {
    const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
    if (isNaN(date.getTime())) return 'Invalid date';
    
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZoneName: 'short'
    });
  } catch (error) {
    return 'Invalid date';
  }
};

export const formatRelativeTime = (timestamp: string | Date): string => {
  try {
    if (!timestamp) return 'Unknown';
    
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    const now = new Date();
    
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);
    
    if (diffInSeconds < 0) return 'just now';
    if (diffInSeconds < 60) return 'just now';
    if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''} ago`;
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
    if (diffInDays < 7) return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`;
    
    return formatToLocalTimezone(date);
  } catch (error) {
    return 'Unknown';
  }
};

export const getTimezoneDebugInfo = () => {
  const now = new Date();
  const clientTz = getClientTimezone();
  
  return {
    utcTime: now.toISOString(),
    localTime: now.toLocaleString(),
    timezone: clientTz.timezone,
    offsetString: clientTz.offsetString,
    timestamp: now.getTime()
  };
};

import { useEffect } from 'react'

/**
 * Custom hook to update document.title for each page.
 * @param {string} title - Page title (will be appended with " | TradeAI")
 */
export function usePageTitle(title) {
  useEffect(() => {
    const prev = document.title
    document.title = title ? `${title} | TradeAI` : 'TradeAI — AI Stock Trading Simulator'
    return () => {
      document.title = prev
    }
  }, [title])
}

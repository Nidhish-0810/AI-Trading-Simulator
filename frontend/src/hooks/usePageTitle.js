import { useEffect } from 'react'

export function usePageTitle(title) {
  useEffect(() => {
    const prev = document.title
    document.title = title ? `${title} | TradeAI` : 'TradeAI — AI Stock Trading Simulator'
    return () => {
      document.title = prev
    }
  }, [title])
}
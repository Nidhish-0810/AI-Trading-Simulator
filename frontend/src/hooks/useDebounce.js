import { useState, useEffect } from 'react'

/**
 * Custom hook that debounces a value by the given delay.
 * Useful for search inputs to avoid API calls on every keystroke.
 *
 * @param {any} value - The value to debounce
 * @param {number} delay - Delay in milliseconds (default 300ms)
 * @returns {any} - Debounced value (only updates after delay expires)
 *
 * @example
 * const debouncedSearch = useDebounce(searchInput, 300)
 * useEffect(() => { if (debouncedSearch) fetchResults(debouncedSearch) }, [debouncedSearch])
 */
export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

interface UseFetchState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useFetch<T>(
  fetchFn: (() => Promise<T>) | null,
  deps: unknown[] = []
): UseFetchState<T> & { refetch: () => void } {
  const [state, setState] = useState<UseFetchState<T>>({
    data: null,
    loading: false,
    error: null,
  })
  const fetchFnRef = useRef(fetchFn)
  fetchFnRef.current = fetchFn

  const execute = useCallback(async () => {
    if (!fetchFnRef.current) return
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await fetchFnRef.current()
      setState({ data, loading: false, error: null })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Fetch failed'
      setState((s) => ({ ...s, loading: false, error: msg }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    execute()
  }, [execute])

  return { ...state, refetch: execute }
}

export function useAsyncFn<T, A extends unknown[]>(
  fn: (...args: A) => Promise<T>
): {
  execute: (...args: A) => Promise<void>
  data: T | null
  loading: boolean
  error: string | null
  reset: () => void
} {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(
    async (...args: A) => {
      setLoading(true)
      setError(null)
      try {
        const result = await fn(...args)
        setData(result)
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Operation failed'
        setError(msg)
      } finally {
        setLoading(false)
      }
    },
    [fn]
  )

  const reset = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  return { execute, data, loading, error, reset }
}

import { useQuery } from '@tanstack/react-query'
import { metaApi } from '../api/metaApi'
import { metaKeys } from '../../../shared/queryKeys'

export function useSources() {
  return useQuery({
    queryKey: metaKeys.sources(),
    queryFn: metaApi.getSources,
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60,
  })
}

export function useCategories() {
  return useQuery({
    queryKey: metaKeys.categories(),
    queryFn: metaApi.getCategories,
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60,
  })
}

export function useStats() {
  return useQuery({
    queryKey: metaKeys.stats(),
    queryFn: metaApi.getStats,
    staleTime: 1000 * 60,
    refetchInterval: 1000 * 30,
  })
}

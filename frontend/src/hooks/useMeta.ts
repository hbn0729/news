/**
 * useMeta Hooks - 元数据查询
 *
 * 职责：
 * - 来源列表
 * - 分类列表
 * - 统计信息
 */

import { useQuery } from '@tanstack/react-query'
import { metaApi } from '../api/client'

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: metaApi.getSources,
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60,
  })
}

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: metaApi.getCategories,
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60,
  })
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: metaApi.getStats,
    staleTime: 1000 * 60,
    refetchInterval: 1000 * 30,
  })
}

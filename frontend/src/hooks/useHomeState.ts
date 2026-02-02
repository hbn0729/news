/**
 * useHomeState Hook - Home 页面状态管理
 *
 * 职责：
 * - 管理筛选状态
 * - 封装数据查询
 * - 提供刷新功能
 */

import { useState, useMemo, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useNews } from './useNews'
import { useDebounce } from './useDebounce'
import type { NewsFilters } from '../types'

export function useHomeState() {
  // 筛选状态
  const [source, setSource] = useState<string | null>(null)
  const [category, setCategory] = useState<string | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [starredOnly, setStarredOnly] = useState(false)

  const queryClient = useQueryClient()

  // 防抖搜索
  const debouncedSearch = useDebounce(searchInput, 300)

  // 构建筛选对象
  const filters: NewsFilters = useMemo(
    () => ({
      source,
      category,
      search: debouncedSearch || undefined,
      starredOnly,
    }),
    [source, category, debouncedSearch, starredOnly]
  )

  // 查询新闻
  const newsQuery = useNews(filters)

  // 提取文章列表
  const articles = useMemo(
    () => newsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [newsQuery.data]
  )

  const total = newsQuery.data?.pages[0]?.total ?? 0

  // 刷新函数
  const handleRefresh = useCallback(() => {
    newsQuery.refetch()
    queryClient.invalidateQueries({ queryKey: ['stats'] })
    queryClient.invalidateQueries({ queryKey: ['sources'] })
    queryClient.invalidateQueries({ queryKey: ['categories'] })
  }, [newsQuery, queryClient])

  // 切换收藏筛选
  const toggleStarredOnly = useCallback(() => {
    setStarredOnly((prev) => !prev)
  }, [])

  return {
    // 筛选状态
    source,
    setSource,
    category,
    setCategory,
    searchInput,
    setSearchInput,
    starredOnly,
    toggleStarredOnly,

    // 数据
    articles,
    total,

    // 查询状态
    isLoading: newsQuery.isLoading,
    isError: newsQuery.isError,
    error: newsQuery.error,
    isRefetching: newsQuery.isRefetching,
    hasNextPage: newsQuery.hasNextPage ?? false,
    isFetchingNextPage: newsQuery.isFetchingNextPage,

    // 操作
    fetchNextPage: newsQuery.fetchNextPage,
    handleRefresh,
  }
}

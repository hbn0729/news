/**
 * useNews Hook - 新闻列表查询
 *
 * 职责：
 * - 分页查询
 * - 无限滚动
 */

import { useInfiniteQuery } from '@tanstack/react-query'
import { newsApi } from '../api/client'
import type { NewsFilters } from '../types'

export function useNews(filters: NewsFilters = {}) {
  const { source, category, search, starredOnly } = filters

  return useInfiniteQuery({
    queryKey: ['news', source ?? '', category ?? '', search ?? '', starredOnly ?? false],
    queryFn: async ({ pageParam = 1 }) => {
      return newsApi.getNews({
        page: pageParam,
        perPage: 20,
        filters,
      })
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.page < lastPage.pages) {
        return lastPage.page + 1
      }
      return undefined
    },
    initialPageParam: 1,
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
    placeholderData: (previousData) => previousData,
  })
}

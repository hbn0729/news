import { useInfiniteQuery } from '@tanstack/react-query'
import type { NewsFilters } from '../../../types'
import { newsApi } from '../api/newsApi'
import { newsKeys } from '../../../shared/queryKeys'

export function useNews(filters: NewsFilters = {}) {
  return useInfiniteQuery({
    queryKey: newsKeys.list(filters),
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

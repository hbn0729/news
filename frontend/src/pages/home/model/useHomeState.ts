import { useState, useMemo, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { NewsFilters } from '@/types'
import { useNews, useUpdateArticle } from '@/features/news'
import { useCategories, useSources } from '@/features/meta'
import { useDebounce } from '@/shared/hooks/useDebounce'
import { metaKeys } from '@/shared/queryKeys'

export function useHomeState() {
  const [source, setSource] = useState<string | null>(null)
  const [category, setCategory] = useState<string | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [publishedDate, setPublishedDate] = useState<string | null>(null)
  const [starredOnly, setStarredOnly] = useState(false)

  const queryClient = useQueryClient()
  const debouncedSearch = useDebounce(searchInput, 300)

  const filters: NewsFilters = useMemo(
    () => ({
      source,
      category,
      search: debouncedSearch || undefined,
      publishedDate,
      starredOnly,
    }),
    [source, category, debouncedSearch, publishedDate, starredOnly]
  )

  const newsQuery = useNews(filters)
  const sourcesQuery = useSources()
  const categoriesQuery = useCategories()
  const updateArticle = useUpdateArticle()

  const articles = useMemo(
    () => newsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [newsQuery.data]
  )

  const total = newsQuery.data?.pages[0]?.total ?? 0

  const handleRefresh = useCallback(() => {
    newsQuery.refetch()
    queryClient.invalidateQueries({ queryKey: metaKeys.stats() })
    queryClient.invalidateQueries({ queryKey: metaKeys.sources() })
    queryClient.invalidateQueries({ queryKey: metaKeys.categories() })
  }, [newsQuery, queryClient])

  const toggleStarredOnly = useCallback(() => {
    setStarredOnly((prev) => !prev)
  }, [])

  const handleRead = useCallback(
    (id: string) => {
      updateArticle.mutate({ id, update: { isRead: true } })
    },
    [updateArticle]
  )

  const handleStar = useCallback(
    (id: string, isStarred: boolean) => {
      updateArticle.mutate({ id, update: { isStarred: !isStarred } })
    },
    [updateArticle]
  )

  return {
    source,
    setSource,
    category,
    setCategory,
    searchInput,
    setSearchInput,
    publishedDate,
    setPublishedDate,
    starredOnly,
    toggleStarredOnly,
    articles,
    total,
    sources: sourcesQuery.data ?? [],
    categories: categoriesQuery.data ?? [],
    isLoading: newsQuery.isLoading,
    isError: newsQuery.isError,
    error: newsQuery.error,
    isRefetching: newsQuery.isRefetching,
    hasNextPage: newsQuery.hasNextPage ?? false,
    isFetchingNextPage: newsQuery.isFetchingNextPage,
    isSourcesLoading: sourcesQuery.isLoading,
    isSourcesError: sourcesQuery.isError,
    isCategoriesLoading: categoriesQuery.isLoading,
    isCategoriesError: categoriesQuery.isError,
    fetchNextPage: newsQuery.fetchNextPage,
    handleRefresh,
    handleRead,
    handleStar,
  }
}

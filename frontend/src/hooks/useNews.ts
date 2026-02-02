import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

export interface Article {
  id: string
  title: string
  content: string | null
  summary: string | null
  url: string
  source: string
  source_category: string | null
  published_at: string
  collected_at: string
  ai_quality_score: number | null
  ai_category: string | null
  ai_keywords: string[] | null
  ai_processed: boolean
  is_read: boolean
  is_starred: boolean
  is_filtered: boolean
}

interface PaginatedNews {
  items: Article[]
  total: number
  page: number
  per_page: number
  pages: number
}

interface UseNewsParams {
  source?: string | null
  category?: string | null
  search?: string
  starredOnly?: boolean
  minQuality?: number
}

const api = axios.create({
  baseURL: '/api',
})

export function useNews(params: UseNewsParams = {}) {
  const { source, category, search, starredOnly, minQuality } = params

  return useInfiniteQuery({
    // Stable queryKey with primitive values
    queryKey: ['news', source ?? '', category ?? '', search ?? '', starredOnly ?? false, minQuality ?? 0],
    queryFn: async ({ pageParam = 1 }) => {
      const response = await api.get<PaginatedNews>('/news', {
        params: {
          page: pageParam,
          per_page: 20,
          source: source || undefined,
          category: category || undefined,
          search: search || undefined,
          starred_only: starredOnly || undefined,
          min_quality: minQuality || undefined,
        },
      })
      return response.data
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.page < lastPage.pages) {
        return lastPage.page + 1
      }
      return undefined
    },
    initialPageParam: 1,
    // 自动刷新配置：每30秒重新获取数据
    refetchInterval: 30000, // 30秒
    // 窗口获得焦点时重新获取
    refetchOnWindowFocus: true,
    // 保持之前的数据，避免闪烁
    placeholderData: (previousData) => previousData,
  })
}

export function useUpdateArticle() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      id,
      update,
    }: {
      id: string
      update: { is_read?: boolean; is_starred?: boolean }
    }) => {
      const response = await api.patch<Article>(`/news/${id}`, update)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] })
    },
  })
}

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: async () => {
      const response = await api.get<{ source: string; count: number }[]>('/sources')
      return response.data
    },
    staleTime: 1000 * 60 * 5,
    // 每分钟重新获取数据源列表
    refetchInterval: 1000 * 60,
  })
}

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await api.get<{ category: string; count: number }[]>('/categories')
      return response.data
    },
    staleTime: 1000 * 60 * 5,
    // 每分钟重新获取分类列表
    refetchInterval: 1000 * 60,
  })
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await api.get<{
        total_articles: number
        unread: number
        starred: number
        filtered: number
        ai_processed: number
      }>('/stats')
      return response.data
    },
    staleTime: 1000 * 60,
    // 每30秒重新获取统计数据
    refetchInterval: 1000 * 30,
  })
}

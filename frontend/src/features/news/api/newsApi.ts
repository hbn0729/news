import type { Article, ArticleDTO, ArticleUpdate, NewsFilters, PaginatedNews, PaginatedNewsDTO } from '../../../types'
import httpClient from '../../../shared/api/httpClient'
import { mapArticleDtoToArticle, mapArticleUpdateToDto, mapPaginatedNewsDtoToPaginatedNews } from './serializers'

export const newsApi = {
  async getNews(params: {
    page?: number
    perPage?: number
    filters?: NewsFilters
  }): Promise<PaginatedNews> {
    const { page = 1, perPage = 20, filters = {} } = params
    const response = await httpClient.get<PaginatedNewsDTO>('/news', {
      params: {
        page,
        per_page: perPage,
        source: filters.source || undefined,
        category: filters.category || undefined,
        search: filters.search || undefined,
        published_date: filters.publishedDate || undefined,
        starred_only: filters.starredOnly || undefined,
      },
    })
    return mapPaginatedNewsDtoToPaginatedNews(response.data)
  },

  async getArticle(id: string): Promise<Article> {
    const response = await httpClient.get<ArticleDTO>(`/news/${id}`)
    return mapArticleDtoToArticle(response.data)
  },

  async updateArticle(id: string, update: ArticleUpdate): Promise<Article> {
    const response = await httpClient.patch<ArticleDTO>(`/news/${id}`, mapArticleUpdateToDto(update))
    return mapArticleDtoToArticle(response.data)
  },

  async markAllRead(source?: string): Promise<{ marked_read: number }> {
    const response = await httpClient.post<{ marked_read: number }>('/news/mark-all-read', null, {
      params: { source },
    })
    return response.data
  },
}

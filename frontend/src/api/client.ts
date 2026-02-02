/**
 * API Client - 统一的 API 访问层
 *
 * 职责：
 * - 封装 axios 实例
 * - 统一错误处理
 * - 提供类型安全的 API 方法
 */

import axios from 'axios'
import type {
  Article,
  ArticleUpdate,
  PaginatedNews,
  SourceInfo,
  CategoryInfo,
  Stats,
  NewsFilters,
} from '../types'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器（可扩展：添加 token 等）
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// 响应拦截器（统一错误处理）
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ============================================
// 新闻相关 API
// ============================================

export const newsApi = {
  /**
   * 获取分页新闻列表
   */
  async getNews(params: {
    page?: number
    perPage?: number
    filters?: NewsFilters
  }): Promise<PaginatedNews> {
    const { page = 1, perPage = 20, filters = {} } = params
    const response = await api.get<PaginatedNews>('/news', {
      params: {
        page,
        per_page: perPage,
        source: filters.source || undefined,
        category: filters.category || undefined,
        search: filters.search || undefined,
        starred_only: filters.starredOnly || undefined,
      },
    })
    return response.data
  },

  /**
   * 获取单篇文章
   */
  async getArticle(id: string): Promise<Article> {
    const response = await api.get<Article>(`/news/${id}`)
    return response.data
  },

  /**
   * 更新文章状态
   */
  async updateArticle(id: string, update: ArticleUpdate): Promise<Article> {
    const response = await api.patch<Article>(`/news/${id}`, update)
    return response.data
  },

  /**
   * 标记所有为已读
   */
  async markAllRead(source?: string): Promise<{ marked_read: number }> {
    const response = await api.post<{ marked_read: number }>('/news/mark-all-read', null, {
      params: { source },
    })
    return response.data
  },
}

// ============================================
// 元数据相关 API
// ============================================

export const metaApi = {
  /**
   * 获取来源列表
   */
  async getSources(): Promise<SourceInfo[]> {
    const response = await api.get<SourceInfo[]>('/sources')
    return response.data
  },

  /**
   * 获取分类列表
   */
  async getCategories(): Promise<CategoryInfo[]> {
    const response = await api.get<CategoryInfo[]>('/categories')
    return response.data
  },

  /**
   * 获取统计信息
   */
  async getStats(): Promise<Stats> {
    const response = await api.get<Stats>('/stats')
    return response.data
  },
}

export default api

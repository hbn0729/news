import type {
  Article,
  ArticleDTO,
  ArticleUpdate,
  ArticleUpdateDTO,
  PaginatedNews,
  PaginatedNewsDTO,
} from '../../../types'

export function mapArticleDtoToArticle(dto: ArticleDTO): Article {
  return {
    id: dto.id,
    title: dto.title,
    content: dto.content,
    summary: dto.summary,
    url: dto.url,
    source: dto.source,
    sourceCategory: dto.source_category,
    publishedAt: dto.published_at,
    collectedAt: dto.collected_at,
    isRead: dto.is_read,
    isStarred: dto.is_starred,
    isFiltered: dto.is_filtered,
  }
}

export function mapPaginatedNewsDtoToPaginatedNews(dto: PaginatedNewsDTO): PaginatedNews {
  return {
    items: dto.items.map(mapArticleDtoToArticle),
    total: dto.total,
    page: dto.page,
    perPage: dto.per_page,
    pages: dto.pages,
  }
}

export function mapArticleUpdateToDto(update: ArticleUpdate): ArticleUpdateDTO {
  return {
    is_read: update.isRead,
    is_starred: update.isStarred,
  }
}

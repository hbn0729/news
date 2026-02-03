import type { Article } from '../../types'

export function getArticleHref(article: Pick<Article, 'source' | 'url'>) {
  if (article.source === 'itjuzi') {
    return 'https://www.itjuzi.com/bulletin'
  }
  return article.url
}

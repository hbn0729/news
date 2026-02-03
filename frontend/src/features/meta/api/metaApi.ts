import type { CategoryInfo, SourceInfo, Stats, StatsDTO } from '../../../types'
import httpClient from '../../../shared/api/httpClient'
import { mapStatsDtoToStats } from './serializers'

export const metaApi = {
  async getSources(): Promise<SourceInfo[]> {
    const response = await httpClient.get<SourceInfo[]>('/sources')
    return response.data
  },

  async getCategories(): Promise<CategoryInfo[]> {
    const response = await httpClient.get<CategoryInfo[]>('/categories')
    return response.data
  },

  async getStats(): Promise<Stats> {
    const response = await httpClient.get<StatsDTO>('/stats')
    return mapStatsDtoToStats(response.data)
  },
}

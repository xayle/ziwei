import apiClient from './client'
import { saveBlobAsFile } from './fushengReport'

export type ShareCardLayout = 'default' | 'douyin'

/** T097/T098：导出命盘分享卡 PNG（douyin=9:16） */
export async function downloadCaseShareCard(
  caseId: string,
  layout: ShareCardLayout = 'douyin',
): Promise<Blob> {
  const id = caseId.trim()
  if (!id) throw new Error('case_id required')
  const { data } = await apiClient.get<Blob>(
    `/api/v1/cases/${encodeURIComponent(id)}/export/card`,
    {
      params: { layout },
      responseType: 'blob',
      timeout: 120_000,
    },
  )
  return data
}

export function saveShareCardPng(blob: Blob, basename = '浮生-竖版分享卡'): void {
  const name = basename.endsWith('.png') ? basename : `${basename}.png`
  saveBlobAsFile(blob, name)
}

export { saveBlobAsFile }

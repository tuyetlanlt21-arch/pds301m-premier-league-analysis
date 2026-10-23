export type Row = Record<string, any>

export type DatasetName =
  | 'cleaned_matches'
  | 'team_match'
  | 'team_season_summary'
  | 'team_home_away_summary'
  | 'attacking_summary'
  | 'defensive_summary'
  | 'winning_patterns'
  | 'losing_patterns'
  | 'form_consistency_summary'
  | 'half_time_full_time_summary'
  | 'half_time_full_time_transition'
  | 'goal_distribution'
  | 'goal_statistics'
  | 'season_summary'
  | 'efficiency_correlations'
  | 'efficiency_outcome_comparison'
  | 'efficiency_patterns'

export type AnalyticsData = Record<DatasetName, Row[]>

const files: DatasetName[] = [
  'cleaned_matches', 'team_match', 'team_season_summary', 'team_home_away_summary',
  'attacking_summary', 'defensive_summary', 'winning_patterns', 'losing_patterns',
  'form_consistency_summary', 'half_time_full_time_summary', 'half_time_full_time_transition',
  'goal_distribution', 'goal_statistics', 'season_summary', 'efficiency_correlations',
  'efficiency_outcome_comparison', 'efficiency_patterns',
]

export async function loadAnalytics(): Promise<AnalyticsData> {
  const entries = await Promise.all(files.map(async (name) => {
    const response = await fetch(`/data/${name}.json`)
    if (!response.ok) throw new Error(`Unable to load ${name}.json`)
    return [name, await response.json()] as const
  }))
  return Object.fromEntries(entries) as AnalyticsData
}

export const formatNumber = (value: unknown, digits = 0) => {
  if (value === null || value === undefined || value === '' || Number.isNaN(Number(value))) return 'Unavailable'
  return Number(value).toLocaleString('en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

export const formatPercent = (value: unknown, digits = 1) => value === null || value === undefined || Number.isNaN(Number(value)) ? 'Unavailable' : `${formatNumber(value, digits)}%`

export const seasonsFrom = (data: AnalyticsData) => data.season_summary.map((row) => String(row.Season))
export const teamsFrom = (data: AnalyticsData, season?: string) => Array.from(new Set(data.team_season_summary.filter((row) => !season || row.Season === season).map((row) => row.Team as string))).sort()

export function downloadCsv(rows: Row[], filename: string) {
  if (!rows.length) return
  const columns = Object.keys(rows[0])
  const escape = (value: unknown) => `"${String(value ?? '').replace(/"/g, '""')}"`
  const csv = [columns.map(escape).join(','), ...rows.map((row) => columns.map((column) => escape(row[column])).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url; link.download = filename; link.click(); URL.revokeObjectURL(url)
}

export const resultLabel: Record<string, string> = { H: 'Win', D: 'Draw', A: 'Loss' }

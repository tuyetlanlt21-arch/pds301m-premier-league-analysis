import { Fragment, useEffect, useMemo, useState, type CSSProperties, type ElementType } from 'react'
import {
  ArrowDown, ArrowUp, ArrowsLeftRight, ChartLineUp, Check, CaretDown, DownloadSimple,
  GitBranch, List, MagnifyingGlass, Moon, PushPin, Ranking, ShieldCheck, Sun,
  Table, TrendUp, Trophy, UsersThree, X,
} from '@phosphor-icons/react'
import {
  Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip,
  XAxis, YAxis,
} from 'recharts'
import { AnalyticsData, downloadCsv, formatNumber, formatPercent, loadAnalytics, resultLabel, seasonsFrom, teamsFrom } from './data'
import './styles.css'
import './transition.css'

type Page = 'Overview' | 'Team Rankings' | 'Attack & Defense' | 'Match Dynamics' | 'Team Comparison' | 'Trends & Statistics' | 'Data Explorer'
type IconProps = { size?: number | string; weight?: any }

const nav: { label: Page; icon: ElementType<IconProps> }[] = [
  { label: 'Overview', icon: ChartLineUp }, { label: 'Team Rankings', icon: Ranking },
  { label: 'Attack & Defense', icon: ShieldCheck }, { label: 'Match Dynamics', icon: ArrowsLeftRight },
  { label: 'Team Comparison', icon: GitBranch }, { label: 'Trends & Statistics', icon: TrendUp },
  { label: 'Data Explorer', icon: Table },
]

const descriptions: Record<Page, string> = {
  Overview: 'Explore the season through its most important numbers.',
  'Team Rankings': 'Compare season performance through the same 3–1–0 measures used in the pipeline.',
  'Attack & Defense': 'Which teams score most effectively, and which teams concede the fewest goals?',
  'Match Dynamics': 'How do match results develop from half-time state to full-time outcome?',
  'Team Comparison': 'How do two teams compare across the same season metrics?',
  'Trends & Statistics': 'What patterns can we discover in Premier League data?',
  'Data Explorer': 'What happened in each match? Search the canonical match records.',
}

function App() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [error, setError] = useState('')
  const [page, setPage] = useState<Page>('Overview')
  const [season, setSeason] = useState('')
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem('premier-theme') as 'light' | 'dark') || 'light')
  const [sidebarPinned, setSidebarPinned] = useState(() => localStorage.getItem('premier-sidebar-pinned') === 'true')
  const [sidebarHover, setSidebarHover] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)

  useEffect(() => { loadAnalytics().then((loaded) => { setData(loaded); setSeason(seasonsFrom(loaded)[0] || '') }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Unable to load analytics data.')) }, [])
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem('premier-theme', theme) }, [theme])
  useEffect(() => { localStorage.setItem('premier-sidebar-pinned', String(sidebarPinned)) }, [sidebarPinned])
  useEffect(() => { document.body.style.overflow = mobileNav ? 'hidden' : ''; return () => { document.body.style.overflow = '' } }, [mobileNav])
  useEffect(() => { if (!mobileNav) return; const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setMobileNav(false) }; window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey) }, [mobileNav])

  if (error) return <div className="state-screen"><div className="state-mark">!</div><h1>Data unavailable</h1><p>{error}</p><button className="button primary" onClick={() => window.location.reload()}>Retry</button></div>
  if (!data) return <div className="state-screen"><div className="loader-line" /><p>Loading the verified analytics layer…</p></div>

  const seasons = () => seasonsFrom(data)
  const active = sidebarPinned || sidebarHover || mobileNav
  const navigate = (next: Page) => { setPage(next); setMobileNav(false) }
  return <div className={`app-shell ${active ? 'sidebar-expanded' : ''}`}>
    <aside className={`sidebar ${active ? 'expanded' : ''} ${mobileNav ? 'mobile-open' : ''}`} onMouseEnter={() => setSidebarHover(true)} onMouseLeave={() => setSidebarHover(false)}>
      <div className="brand-lockup"><div className="brand-mark">PI</div><div className="brand-copy"><strong>Premier</strong><span>Intelligence</span></div></div>
      <nav aria-label="Primary navigation">
        <div className="nav-kicker">Workspace</div>
        {nav.map(({ label, icon: Icon }) => <button key={label} className={`nav-item ${page === label ? 'selected' : ''}`} onClick={() => navigate(label)} aria-label={label} aria-current={page === label ? 'page' : undefined}><Icon size={20} weight={page === label ? 'fill' : 'regular'} /><span>{label}</span></button>)}
      </nav>
      <div className="sidebar-footer"><button className="pin-control" onClick={() => setSidebarPinned((value) => !value)} aria-label={sidebarPinned ? 'Unpin sidebar' : 'Pin sidebar'}><PushPin size={16} weight={sidebarPinned ? 'fill' : 'regular'} /><span>{sidebarPinned ? 'Pinned open' : 'Pin sidebar'}</span></button><div className="data-note"><span className="status-dot" /> <span>Verified local data</span></div></div>
    </aside>
    {mobileNav && <button className="drawer-backdrop" aria-label="Close navigation" onClick={() => setMobileNav(false)} />}
    <main className="main-content">
      <header className="topbar"><button className="mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open navigation"><List size={22} /></button><div className="breadcrumb"><span>Premier Intelligence</span><b>/</b><strong>{page}</strong></div><div className="top-actions"><div className="data-status"><span className="status-dot" />Local analytics</div><button className="theme-toggle" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>{theme === 'light' ? <Moon size={19} /> : <Sun size={19} />}</button></div></header>
      <div className="page-wrap"><div className="page-heading"><div><p className="eyebrow">Premier League analytics</p><h1>{page === 'Overview' ? 'Premier League Overview' : page}</h1><p className="page-description">{descriptions[page]}</p></div><div className="heading-controls"><SeasonSelect season={season} seasons={seasons()} onChange={setSeason} /></div></div><PageView page={page} data={data} season={season} setSeason={setSeason} setPage={setPage} /></div>
    </main>
  </div>
}

function seasons(data: AnalyticsData) { return data.season_summary.map((row) => String(row.Season)) }

function SeasonSelect({ season, seasons, onChange }: { season: string; seasons: string[]; onChange: (value: string) => void }) {
  return <label className="select-wrap"><span>Season</span><select value={season} onChange={(event) => onChange(event.target.value)}>{seasons.map((value) => <option key={value}>{value}</option>)}</select><CaretDown size={15} /></label>
}

function PageView(props: { page: Page; data: AnalyticsData; season: string; setSeason: (value: string) => void; setPage: (value: Page) => void }) {
  switch (props.page) {
    case 'Overview': return <Overview {...props} />
    case 'Team Rankings': return <Rankings {...props} />
    case 'Attack & Defense': return <AttackDefense {...props} />
    case 'Match Dynamics': return <Dynamics {...props} />
    case 'Team Comparison': return <Comparison {...props} />
    case 'Trends & Statistics': return <Trends {...props} />
    case 'Data Explorer': return <Explorer {...props} />
  }
}

function SectionTitle({ eyebrow, title, note }: { eyebrow: string; title: string; note?: string }) { return <div className="section-title"><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>{note && <span className="section-note">{note}</span>}</div> }

function MetricStrip({ metrics }: { metrics: { label: string; value: string; detail?: string }[] }) { return <div className="metric-strip">{metrics.map((metric) => <div className="metric" key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong>{metric.detail && <small>{metric.detail}</small>}</div>)}</div> }

function Overview({ data, season, setPage }: { data: AnalyticsData; season: string; setPage: (value: Page) => void }) {
  const current = data.season_summary.find((row) => row.Season === season) || data.season_summary[0]
  const teams = data.team_season_summary.filter((row) => row.Season === season).sort((a, b) => Number(b.PointsPerMatch) - Number(a.PointsPerMatch))
  const trend = data.season_summary.map((row) => ({ season: row.Season, goals: Number(row.GoalsPerMatch), home: Number(row.HomeWinRatePct), away: Number(row.AwayWinRatePct) }))
  return <>
    <MetricStrip metrics={[{ label: 'Matches analyzed', value: formatNumber(current?.CompletedMatches) }, { label: 'Goals scored', value: formatNumber(Number(current?.GoalsPerMatch || 0) * Number(current?.CompletedMatches || 0)) }, { label: 'Average goals', value: formatNumber(current?.GoalsPerMatch, 2), detail: 'per completed match' }, { label: 'Teams observed', value: formatNumber(current?.ParticipatingTeams) }]} />
    <div className="content-grid overview-grid"><section className="panel chart-panel"><SectionTitle eyebrow="League pulse" title="Goals per match" note="Season comparison" /><div className="chart-legend"><span><i className="legend-swatch blue" />Goals per completed match</span></div><div className="chart-box large"><ResponsiveContainer width="100%" height="100%"><LineChart data={trend} margin={{ top: 16, right: 24, left: 16, bottom: 24 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="season" tickLine={false} axisLine={false} tickMargin={10} /><YAxis domain={['dataMin - 0.15', 'dataMax + 0.15']} tickLine={false} axisLine={false} width={58} tickMargin={10} tickFormatter={(value) => Number(value).toFixed(2)} /><Tooltip formatter={(value: number) => [formatNumber(value, 2), 'Goals / match']} /><Line type="monotone" dataKey="goals" stroke="var(--accent)" strokeWidth={3} dot={{ r: 4, fill: 'var(--accent)', strokeWidth: 0 }} activeDot={{ r: 6 }} /></LineChart></ResponsiveContainer></div><p className="chart-footnote">A descriptive view of completed fixtures. It does not imply a predictive trend.</p></section><section className="panel ranking-panel"><SectionTitle eyebrow={season} title="Top by points per match" note="Season view" /><div className="rank-list">{teams.slice(0, 5).map((team, index) => <div className="rank-row" key={team.Team}><span className="rank-number">0{index + 1}</span><div className="rank-team"><strong>{team.Team}</strong><span>{formatNumber(team.Wins)}W · {formatNumber(team.Draws)}D · {formatNumber(team.Losses)}L</span></div><b>{formatNumber(team.PointsPerMatch, 2)}</b></div>)}</div><button className="text-link" onClick={() => setPage('Team Rankings')}>Open full rankings <ArrowUp size={14} /></button></section></div>
  </>
}

function Rankings({ data, season }: { data: AnalyticsData; season: string }) {
  const [query, setQuery] = useState(''); const [sort, setSort] = useState('PointsPerMatch'); const [ascending, setAscending] = useState(false)
  const rows = useMemo(() => data.team_season_summary.filter((row) => row.Season === season && String(row.Team).toLowerCase().includes(query.toLowerCase())).sort((a, b) => { const left = Number(a[sort]); const right = Number(b[sort]); return ascending ? left - right : right - left }), [data, season, query, sort, ascending])
  const columns = [['Team', 'Team'], ['Matches', 'MP'], ['Wins', 'W'], ['Draws', 'D'], ['Losses', 'L'], ['GoalsScored', 'GF'], ['GoalsConceded', 'GA'], ['GoalDifference', 'GD'], ['Points', 'Pts'], ['PointsPerMatch', 'PPM'], ['CleanSheets', 'CS']]
  return <><div className="toolbar"><label className="search-field"><MagnifyingGlass size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search teams" /></label><span className="result-count">{rows.length} teams in {season}</span></div><section className="panel table-panel"><SectionTitle eyebrow="Season table" title="Team rankings" note="Derived from completed fixtures" /><div className="table-scroll"><table><thead><tr>{columns.map(([key, label]) => <th key={key} className={key !== 'Team' ? 'numeric' : ''}><button className="sort-button" onClick={() => { if (sort === key) setAscending(!ascending); else { setSort(key); setAscending(false) } }}>{label}{sort === key && (ascending ? <ArrowUp size={13} /> : <ArrowDown size={13} />)}</button></th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={row.Team}><td><span className="table-rank">{index + 1}</span><strong>{row.Team}</strong></td><td className="numeric">{row.Matches}</td><td className="numeric">{row.Wins}</td><td className="numeric">{row.Draws}</td><td className="numeric">{row.Losses}</td><td className="numeric">{row.GoalsScored}</td><td className="numeric">{row.GoalsConceded}</td><td className="numeric">{row.GoalDifference > 0 ? `+${row.GoalDifference}` : row.GoalDifference}</td><td className="numeric emphasis">{row.Points}</td><td className="numeric">{formatNumber(row.PointsPerMatch, 2)}</td><td className="numeric">{row.CleanSheets}</td></tr>)}</tbody></table></div>{rows.length === 0 && <EmptyState title="No teams found" detail="Try a different team name or season." />}</section><p className="method-note"><span className="info-dot">i</span> Points use the standard 3–1–0 rule and are calculated from the completed fixture record. This is a historical analytical ranking, not a live league table.</p></>
}

function AttackDefense({ data, season }: { data: AnalyticsData; season: string }) {
  const rows = data.attacking_summary.filter((row) => row.Season === season).map((attack) => ({ ...attack, ...(data.defensive_summary.find((row) => row.Season === season && row.Team === attack.Team) || {}) })).sort((a, b) => Number(b.GoalsScoredPerMatch) - Number(a.GoalsScoredPerMatch))
  const chart = rows.slice(0, 10).map((row) => ({ team: String(row.Team).replace('Manchester ', 'Man '), attack: Number(row.GoalsScoredPerMatch), defence: Number(row.GoalsConcededPerMatch) }))
  return <><section className="panel chart-panel"><SectionTitle eyebrow="Efficiency profile" title="Attack against defensive control" note="Top ten by goals scored per match" /><div className="chart-box medium"><ResponsiveContainer width="100%" height="100%"><BarChart data={chart} layout="vertical" margin={{ left: 24, right: 18, top: 8, bottom: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" tickLine={false} axisLine={false} /><YAxis type="category" dataKey="team" tickLine={false} axisLine={false} width={90} tick={{ fontSize: 11 }} /><Tooltip formatter={(value: number, name: string) => [formatNumber(value, 2), name === 'attack' ? 'Goals scored / match' : 'Goals conceded / match']} /><Bar dataKey="attack" fill="var(--accent)" radius={[0, 3, 3, 0]} barSize={9} /><Bar dataKey="defence" fill="var(--muted-accent)" radius={[0, 3, 3, 0]} barSize={9} /></BarChart></ResponsiveContainer></div><div className="chart-legend"><span><i className="legend-swatch blue" />Goals scored / match</span><span><i className="legend-swatch muted" />Goals conceded / match</span></div></section><section className="panel table-panel compact-table"><SectionTitle eyebrow="Metric definitions" title="Attacking and defensive detail" note="Nulls remain unavailable" /><div className="table-scroll"><table><thead><tr><th>Team</th><th className="numeric">Shot accuracy</th><th className="numeric">Shot conversion</th><th className="numeric">Clean-sheet rate</th><th className="numeric">Conceded 2+</th><th className="numeric">Goals / SOT</th></tr></thead><tbody>{rows.map((row) => <tr key={row.Team}><td><strong>{row.Team}</strong></td><td className="numeric">{formatPercent(row.ShotAccuracyPct)}</td><td className="numeric">{formatPercent(row.ShotConversionPct)}</td><td className="numeric">{formatPercent(row.CleanSheetRatePct)}</td><td className="numeric">{formatPercent(row.Conceded2PlusRatePct)}</td><td className="numeric">{formatNumber(row.GoalsPerShotOnTarget, 2)}</td></tr>)}</tbody></table></div></section></>
}

function Dynamics({ data, season }: { data: AnalyticsData; season: string }) {
  const fixtures = data.cleaned_matches.filter((row) => row.Season === season); const result = [{ label: 'Home wins', value: fixtures.filter((row) => row.FTR === 'H').length }, { label: 'Draws', value: fixtures.filter((row) => row.FTR === 'D').length }, { label: 'Away wins', value: fixtures.filter((row) => row.FTR === 'A').length }]
  const transition = ['H', 'D', 'A'].map((halfTime) => ({ HTR: halfTime, H: fixtures.filter((row) => row.HTR === halfTime && row.FTR === 'H').length, D: fixtures.filter((row) => row.HTR === halfTime && row.FTR === 'D').length, A: fixtures.filter((row) => row.HTR === halfTime && row.FTR === 'A').length }))
  const total = transition.reduce((sum, row) => sum + Number(row.H || 0) + Number(row.D || 0) + Number(row.A || 0), 0)
  const dynamics = data.half_time_full_time_summary.filter((row) => row.Season === season).sort((a, b) => Number(b.ComebackSuccessRatePct) - Number(a.ComebackSuccessRatePct))
  const maxCell = Math.max(...transition.flatMap((row) => [row.H, row.D, row.A]), 1)
  const matrixRows = [{ key: 'H', label: 'Home ahead' }, { key: 'D', label: 'Level' }, { key: 'A', label: 'Away ahead' }]
  return <><div className="content-grid dynamics-grid"><section className="panel chart-panel"><SectionTitle eyebrow="Full-time outcomes" title="How results land" note={`${formatNumber(fixtures.length)} fixtures`} /><div className="outcome-bars">{result.map((item) => <div className="outcome-row" key={item.label}><div><span>{item.label}</span><b>{formatPercent(item.value / fixtures.length * 100)}</b></div><div className="track"><i style={{ width: `${item.value / fixtures.length * 100}%` }} /></div></div>)}</div><p className="chart-footnote">Shares are calculated from completed fixtures in the selected season.</p></section><section className="panel transition-card"><SectionTitle eyebrow="HALF-TIME TO FULL-TIME" title="How do match results change?" note={season} /><p className="chart-intro">Compare the result at half-time with the final outcome.</p><div className="transition-matrix"><div className="transition-matrix__corner" /><div className="transition-matrix__header">Home win</div><div className="transition-matrix__header">Draw</div><div className="transition-matrix__header">Away win</div>{matrixRows.map((row) => <Fragment key={row.key}><div className="transition-matrix__row-label">{row.label}</div>{(['H', 'D', 'A'] as const).map((outcome) => { const value = Number(transition.find((item) => item.HTR === row.key)?.[outcome] || 0); return <div className="transition-matrix__cell" key={outcome} style={{ '--heat': value / maxCell } as CSSProperties}>{value}</div> })}</Fragment>)}</div><div className="transition-footer"><span>{formatNumber(total)} completed matches with recorded half-time and full-time results</span><span className="heat-legend"><i />Lower count <b />Higher count</span></div></section></div><section className="panel table-panel"><SectionTitle eyebrow="Recovery and control" title="Comeback and lead preservation" note={`Season: ${season}`} /><div className="table-scroll"><table><thead><tr><th>Team</th><th className="numeric">Comeback wins</th><th className="numeric">Comeback rate</th><th className="numeric">Lost leads</th><th className="numeric">Lead preservation</th></tr></thead><tbody>{dynamics.slice(0, 10).map((row) => <tr key={row.Team}><td><strong>{row.Team}</strong></td><td className="numeric">{row.ComebackWins}</td><td className="numeric">{formatPercent(row.ComebackSuccessRatePct)}</td><td className="numeric">{row.LostLeads}</td><td className="numeric">{formatPercent(row.LeadPreservationRatePct)}</td></tr>)}</tbody></table></div></section></>
}

function Comparison({ data, season }: { data: AnalyticsData; season: string }) {
  const teams = teamsFrom(data, season); const [teamA, setTeamA] = useState(teams[0] || ''); const [teamB, setTeamB] = useState(teams[1] || '')
  useEffect(() => { if (!teams.includes(teamA)) setTeamA(teams[0] || ''); if (!teams.includes(teamB)) setTeamB(teams[1] || '') }, [season, teams.join('|')])
  const rows = [data.team_season_summary.find((row) => row.Season === season && row.Team === teamA), data.team_season_summary.find((row) => row.Season === season && row.Team === teamB)]
  const metrics = [['Points per match', 'PointsPerMatch', 2], ['Win rate', 'WinRatePct', 1], ['Goals scored / match', 'GoalsScoredPerMatch', 2], ['Goals conceded / match', 'GoalsConcededPerMatch', 2], ['Clean-sheet rate', 'CleanSheetRatePct', 1], ['Shot conversion', 'ShotConversionPct', 1]] as const
  const h2h = data.team_match.filter((row) => row.Team === teamA && row.Opponent === teamB)
  return <><div className="comparison-selects"><TeamSelect label="Team A" value={teamA} options={teams} onChange={setTeamA} /><div className="versus">vs</div><TeamSelect label="Team B" value={teamB} options={teams} onChange={setTeamB} /></div><section className="panel comparison-panel"><SectionTitle eyebrow="Season comparison" title="Same season, different profile" note={season} /><div className="compare-head"><div /><strong>{teamA}</strong><strong>{teamB}</strong></div>{metrics.map(([label, key, digits]) => <div className="compare-row" key={key}><span>{label}</span><b className={Number(rows[0]?.[key]) >= Number(rows[1]?.[key]) ? 'better' : ''}>{formatNumber(rows[0]?.[key], digits)}{key.includes('Rate') || key === 'ShotConversionPct' ? '%' : ''}</b><b className={Number(rows[1]?.[key]) >= Number(rows[0]?.[key]) ? 'better' : ''}>{formatNumber(rows[1]?.[key], digits)}{key.includes('Rate') || key === 'ShotConversionPct' ? '%' : ''}</b></div>)}<p className="comparison-note">Head-to-head: {formatNumber(h2h.length)} fixtures where {teamA} faced {teamB} in the available record. Overall season values above are not head-to-head values.</p></section></>
}

function TeamSelect({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) { return <label className="select-wrap wide"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option}>{option}</option>)}</select><CaretDown size={15} /></label> }

function Trends({ data }: { data: AnalyticsData }) {
  const seasons = data.season_summary.map((row) => ({ season: row.Season, goals: Number(row.GoalsPerMatch), home: Number(row.HomeWinRatePct), away: Number(row.AwayWinRatePct) })); const distribution = data.goal_distribution.map((row) => ({ bucket: String(row.GoalBucket), matches: Number(row.Matches) })); const corr = data.efficiency_correlations
  return <><div className="content-grid trends-grid"><section className="panel chart-panel"><SectionTitle eyebrow="Over time" title="League scoring and home edge" note="Completed season comparison" /><div className="chart-box medium"><ResponsiveContainer width="100%" height="100%"><LineChart data={seasons} margin={{ top: 16, right: 24, left: 16, bottom: 24 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="season" tickLine={false} axisLine={false} tickMargin={10} /><YAxis tickLine={false} axisLine={false} width={58} tickMargin={10} tickFormatter={(value) => Number(value).toFixed(2)} /><Tooltip formatter={(value: number, name: string) => [name === 'Home win rate' ? formatPercent(value) : formatNumber(value, 2), name]} /><Line dataKey="goals" name="Goals / match" stroke="var(--accent)" strokeWidth={2.5} /><Line dataKey="home" name="Home win rate" stroke="var(--muted-accent)" strokeWidth={2.5} /></LineChart></ResponsiveContainer></div><div className="chart-legend"><span><i className="legend-swatch blue" />Goals / match</span><span><i className="legend-swatch muted" />Home win rate (%)</span></div></section><section className="panel chart-panel"><SectionTitle eyebrow="Distribution" title="Goals per match" note="All exported fixtures" /><div className="chart-box medium"><ResponsiveContainer width="100%" height="100%"><BarChart data={distribution} margin={{ top: 16, right: 24, left: 16, bottom: 24 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="bucket" tickLine={false} axisLine={false} tickMargin={10} /><YAxis tickLine={false} axisLine={false} width={58} tickMargin={10} tickFormatter={(value) => Number(value).toFixed(0)} /><Tooltip formatter={(value: number) => [formatNumber(value), 'Matches']} /><Bar dataKey="matches" fill="var(--accent)" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></section></div><section className="panel table-panel"><SectionTitle eyebrow="Association, not causation" title="Match-statistic correlations" note="Pearson r" /><div className="correlation-grid">{corr.map((row) => <div className="correlation-row" key={row.Metric}><strong>{row.Metric.replace('Total', 'Total ')}</strong>{['TotalGoals', 'TotalShots', 'TotalShotsOnTarget', 'TotalCorners'].map((key) => <span className={Number(row[key]) > 0.5 ? 'positive' : Number(row[key]) < -0.2 ? 'negative' : ''} key={key}>{formatNumber(row[key], 2)}</span>)}</div>)}</div><p className="chart-footnote">Correlation describes statistical association in the match record. It does not establish causation.</p></section></> 
}

function Explorer({ data, season }: { data: AnalyticsData; season: string }) {
  const [team, setTeam] = useState('All teams'); const [venue, setVenue] = useState('All venues'); const [query, setQuery] = useState(''); const [page, setPage] = useState(1); const pageSize = 12
  const teams = teamsFrom(data, season); const rows = data.team_match.filter((row) => row.Season === season && (team === 'All teams' || row.Team === team) && (venue === 'All venues' || row.Venue === venue) && `${row.Team} ${row.Opponent}`.toLowerCase().includes(query.toLowerCase())); const totalPages = Math.max(1, Math.ceil(rows.length / pageSize)); const visible = rows.slice((page - 1) * pageSize, page * pageSize)
  useEffect(() => setPage(1), [season, team, venue, query])
  const resetFilters = () => { setTeam('All teams'); setVenue('All venues'); setQuery('') }
  return <><section className="explorer-filter-toolbar" aria-labelledby="explore-matches-title"><div className="explorer-filter-heading"><div><h2 id="explore-matches-title">Explore matches</h2><p>Find fixtures by team, opponent, or venue.</p></div><div className="explorer-filter-actions"><button className="reset-filters" type="button" onClick={resetFilters} disabled={!query && team === 'All teams' && venue === 'All venues'}>Reset filters</button><button className="button secondary export-button" type="button" onClick={() => downloadCsv(rows, `premier-intelligence-${season}.csv`)}><DownloadSimple size={17} />Export CSV</button></div></div><div className="explorer-filter-fields"><label className="filter-field filter-field-search"><span>Search matches</span><div className="filter-control"><MagnifyingGlass size={18} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search team or opponent" /></div></label><label className="filter-field"><span>Team</span><div className="filter-control"><select value={team} onChange={(event) => setTeam(event.target.value)}><option>All teams</option>{teams.map((value) => <option key={value}>{value}</option>)}</select><CaretDown size={16} aria-hidden="true" /></div></label><label className="filter-field"><span>Venue</span><div className="filter-control"><select value={venue} onChange={(event) => setVenue(event.target.value)}><option>All venues</option><option>Home</option><option>Away</option></select><CaretDown size={16} aria-hidden="true" /></div></label></div></section><section className="panel table-panel"><SectionTitle eyebrow="Canonical fact table" title="Data explorer" note={`${formatNumber(rows.length)} filtered records`} /><div className="table-scroll"><table><thead><tr><th>Date</th><th>Team</th><th>Opponent</th><th>Venue</th><th className="numeric">Result</th><th className="numeric">Score</th><th className="numeric">Shots</th><th className="numeric">SOT</th><th className="numeric">Points</th></tr></thead><tbody>{visible.map((row) => <tr key={`${row.MatchID}-${row.Team}`}><td>{String(row.Date).slice(0, 10)}</td><td><strong>{row.Team}</strong></td><td>{row.Opponent}</td><td><span className={`venue ${row.Venue.toLowerCase()}`}>{row.Venue}</span></td><td className={`numeric result-${row.Result}`}>{resultLabel[row.Result]}</td><td className="numeric score">{row.GoalsFor}–{row.GoalsAgainst}</td><td className="numeric">{row.ShotsFor ?? 'Unavailable'}</td><td className="numeric">{row.ShotsOnTargetFor ?? 'Unavailable'}</td><td className="numeric emphasis">{row.Points}</td></tr>)}</tbody></table></div>{visible.length === 0 && <EmptyState title="No matching fixtures" detail="Adjust the filters to widen the record set." />}<div className="pagination"><span>Page {page} of {totalPages}</span><div><button className="icon-button" disabled={page === 1} onClick={() => setPage(page - 1)} aria-label="Previous page"><ArrowUp size={17} /></button><button className="icon-button" disabled={page === totalPages} onClick={() => setPage(page + 1)} aria-label="Next page"><ArrowDown size={17} /></button></div></div></section></>
}

function EmptyState({ title, detail }: { title: string; detail: string }) { return <div className="empty-state"><Trophy size={22} /><strong>{title}</strong><span>{detail}</span></div> }

export default App

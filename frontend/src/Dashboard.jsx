
import { useEffect, useState } from 'react'
import {
    getFacilities,
    getReferrals,
    getFollowUps,
    getResourceSummary,
  } from './api'

  const initialStats = {
    facilities: 0,
    pendingReferrals: 0,
    completedReferrals: 0,
    scheduledFollowUps: 0,
    lowResources: 0,
    unavailableResources: 0,
  }

const cards = [
  {
    key: 'facilities',
    label: 'Healthcare Facilities',
    color: 'border-blue-500',
  },
  {
    key: 'pendingReferrals',
    label: 'Pending Referrals',
    color: 'border-amber-500',
  },
  {
    key: 'completedReferrals',
    label: 'Completed Referrals',
    color: 'border-emerald-500',
  },
  {
    key: 'scheduledFollowUps',
    label: 'Scheduled Follow-ups',
    color: 'border-violet-500',
  },
  {
    key: 'lowResources',
    label: 'Low-Stock Resources',
    color: 'border-amber-500',
  },
  {
    key: 'unavailableResources',
    label: 'Unavailable Resources',
    color: 'border-red-500',
  },
]

export default function Dashboard() {
  const [stats, setStats] = useState(initialStats)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadDashboard() {
      try {
        setLoading(true)
        setError('')

      const [facilityData, referralData, followUpData, resourceData] =
        await Promise.all([
          getFacilities(),
          getReferrals(),
          getFollowUps(),
          getResourceSummary(),
        ])   

        if (!active) return

        const referrals = referralData.referrals ?? []
        const followUps = followUpData.follow_ups ?? []

        setStats({
            lowResources: resourceData.low_resources ?? 0,
            unavailableResources: resourceData.unavailable_resources ?? 0,
          facilities: (facilityData.facilities ?? []).length,
          pendingReferrals: referrals.filter(
            (item) => item.status === 'pending',
          ).length,
          completedReferrals: referrals.filter(
            (item) => item.status === 'completed',
          ).length,
          scheduledFollowUps: followUps.filter(
            (item) => item.status === 'scheduled',
          ).length,
        })
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load dashboard data.')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    loadDashboard()

    return () => {
      active = false
    }
  }, [])

  return (
    <section className="mb-8">
      <div className="mb-4">
        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-700">
          RuralCare Connect
        </p>
        <h2 className="mt-1 text-2xl font-bold text-slate-900">
          Rural Healthcare Overview
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          One view of facilities, referrals, and patient follow-ups.
        </p>
      </div>

      {error && (
        <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <article
            key={card.key}
            className={`rounded-xl border border-slate-200 border-l-4 ${card.color} bg-white p-5 shadow-sm`}
          >
            <p className="text-sm font-medium text-slate-600">
              {card.label}
            </p>
            <p className="mt-3 text-3xl font-bold text-slate-900">
              {loading ? '—' : stats[card.key]}
            </p>
          </article>
        ))}
      </div>

      <p className="mt-3 text-xs text-slate-500">
        {loading
          ? 'Loading live database statistics…'
          : 'Statistics calculated from current database records.'}
      </p>
    </section>
  )
}


import { useCallback, useEffect, useState } from 'react'
import {
    createFollowUp,
    getFollowUps,
    getReferrals,
    updateFollowUpStatus,
  } from './api'
export default function FollowUpSection() {
  const [followUps, setFollowUps] = useState([])
  const [referrals, setReferrals] = useState([])
  const [referralId, setReferralId] = useState('')
  const [dueAt, setDueAt] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  
  const loadFollowUps = useCallback(async () => {
    setLoading(true)
    setError('')
  
    try {
      const [followUpData, referralData] = await Promise.all([
        getFollowUps(),
        getReferrals(),
      ])
  
      setFollowUps(followUpData.follow_ups ?? [])
      setReferrals(referralData.referrals ?? [])
    } catch (err) {
      setError(err.message || 'Could not load follow-ups and referrals.')
    } finally {
      setLoading(false)
    }
  }, [])
  

  useEffect(() => {
    loadFollowUps()
  }, [loadFollowUps])

  async function handleCreate(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setMessage('')

    try {
      await createFollowUp({
        referral_id: Number(referralId),
        due_at: new Date(dueAt).toISOString(),
        notes: notes.trim() || null,
        assigned_to_user_id: null,
      })
      setReferralId('')
      setDueAt('')
      setNotes('')
      setMessage('Follow-up created successfully.')
      await loadFollowUps()
    } catch (err) {
      setError(err.message || 'Could not create follow-up.')
    } finally {
      setSaving(false)
    }
  }

  async function handleStatusChange(id, status) {
    setError('')
    setMessage('')
    try {
      await updateFollowUpStatus(id, status)
      setMessage('Follow-up updated successfully.')
      await loadFollowUps()
    } catch (err) {
      setError(err.message || 'Could not update follow-up.')
    }
  }

  return (
    <section className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wider text-teal-700">
          Continuity of care
        </p>
        <h2 className="mt-1 text-2xl font-bold text-slate-900">
          Follow-up Management
        </h2>
        <p className="mt-2 text-slate-600">
          Schedule and track follow-ups linked to referrals.
        </p>
      </div>

      {error && (
        <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-red-700">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="mb-4 rounded-lg bg-green-50 p-3 text-green-800">
          {message}
        </p>
      )}

      <form
        onSubmit={handleCreate}
        className="mb-8 grid gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-2"
      >
        <h3 className="text-lg font-semibold text-slate-900 md:col-span-2">
          Schedule a follow-up
        </h3>
       
<label className="text-sm font-medium text-slate-700">
  Select Referral
  <select
    required
    value={referralId}
    onChange={(event) => setReferralId(event.target.value)}
    className="mt-1 block w-full rounded-lg border border-slate-300 p-2.5"
  >
    <option value="">Choose a referral</option>
    {referrals.map((referral) => (
      <option key={referral.id} value={referral.id}>
        Referral #{referral.id} — {referral.patient_name} ({referral.status})
      </option>
    ))}
  </select>
</label>


        <label className="text-sm font-medium text-slate-700">
          Due date and time
          <input
            type="datetime-local"
            required
            value={dueAt}
            onChange={(event) => setDueAt(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-300 p-2.5"
          />
        </label>

        <label className="text-sm font-medium text-slate-700 md:col-span-2">
          Notes (optional)
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            maxLength={1000}
            rows={2}
            placeholder="Add a follow-up note"
            className="mt-1 block w-full rounded-lg border border-slate-300 p-2.5"
          />
        </label>

        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-teal-700 px-5 py-3 font-semibold text-white hover:bg-teal-800 disabled:opacity-60 md:col-span-2"
        >
          {saving ? 'Saving...' : 'Schedule Follow-up'}
        </button>
      </form>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-200 p-4">
          <h3 className="font-semibold text-slate-900">Scheduled and past follow-ups</h3>
          <button
            type="button"
            onClick={loadFollowUps}
            className="text-sm font-medium text-teal-700 hover:underline"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <p className="p-5 text-slate-600">Loading follow-ups...</p>
        ) : followUps.length === 0 ? (
          <p className="p-5 text-slate-600">No follow-ups found yet.</p>
        ) : (
          <div className="divide-y divide-slate-200">
            {followUps.map((item) => (
              <div key={item.id} className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-slate-900">
                    Follow-up #{item.id} · Referral #{item.referral_id}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    Due: {new Date(item.due_at).toLocaleString()}
                  </p>
                  {item.notes && (
                    <p className="mt-1 text-sm text-slate-600">{item.notes}</p>
                  )}
                  <p className="mt-1 text-sm">
                    Status:{' '}
                    <span className="font-semibold capitalize">{item.status}</span>
                  </p>
                </div>

                {item.status === 'scheduled' && (
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => handleStatusChange(item.id, 'completed')}
                      className="rounded-lg bg-teal-700 px-3 py-2 text-sm font-medium text-white hover:bg-teal-800"
                    >
                      Mark completed
                    </button>
                    <button
                      type="button"
                      onClick={() => handleStatusChange(item.id, 'missed')}
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                    >
                      Mark missed
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

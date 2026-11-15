
import { useEffect, useState } from 'react'
import {
  getFacilities,
  getReferrals,
  createReferral,
  updateReferralStatus,
} from './api.js'

const STATUS_LABELS = {
  pending: 'Pending',
  accepted: 'Accepted',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

const NEXT_STATUSES = {
  pending: ['accepted', 'cancelled'],
  accepted: ['completed', 'cancelled'],
  completed: [],
  cancelled: [],
}

export default function ReferralSection() {
  const [facilities, setFacilities] = useState([])
  const [referrals, setReferrals] = useState([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [updatingId, setUpdatingId] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [form, setForm] = useState({
    patient_name: '',
    patient_age: '',
    from_facility_id: '',
    to_facility_id: '',
    notes: '',
  })

  async function loadData() {
    setLoading(true)
    setError('')

    try {
      const [facilityData, referralData] = await Promise.all([
        getFacilities(),
        getReferrals(),
      ])

      setFacilities(facilityData.facilities ?? [])
      setReferrals(referralData.referrals ?? [])
    } catch (err) {
      setError(err.message || 'Could not load referral data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
  
    async function fetchData() {
      try {
        const [facilityData, referralData] = await Promise.all([
          getFacilities(),
          getReferrals(),
        ])
  
        if (!cancelled) {
          setFacilities(facilityData.facilities ?? [])
          setReferrals(referralData.referrals ?? [])
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Could not load referral data.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
  
    fetchData()
  
    return () => {
      cancelled = true
    }
  }, [])

  function handleChange(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')

    if (
      !form.patient_name.trim() ||
      !form.from_facility_id ||
      !form.to_facility_id
    ) {
      setError('Enter a patient name and select both facilities.')
      return
    }

    if (form.from_facility_id === form.to_facility_id) {
      setError('Source and destination facilities must be different.')
      return
    }

    const referral = {
      patient_name: form.patient_name.trim(),
      from_facility_id: Number(form.from_facility_id),
      to_facility_id: Number(form.to_facility_id),
      ...(form.patient_age !== ''
        ? { patient_age: Number(form.patient_age) }
        : {}),
      ...(form.notes.trim() ? { notes: form.notes.trim() } : {}),
    }

    setSubmitting(true)

    try {
      await createReferral(referral)
      setForm({
        patient_name: '',
        patient_age: '',
        from_facility_id: '',
        to_facility_id: '',
        notes: '',
      })
      setMessage('Referral created successfully.')
      await loadData()
    } catch (err) {
      setError(err.message || 'Could not create referral.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleStatusUpdate(referralId, status) {
    setError('')
    setMessage('')
    setUpdatingId(referralId)

    try {
      await updateReferralStatus(referralId, status)
      setMessage(`Referral #${referralId} updated to ${STATUS_LABELS[status]}.`)
      await loadData()
    } catch (err) {
      setError(err.message || 'Could not update referral status.')
    } finally {
      setUpdatingId(null)
    }
  }

  const visibleReferrals =
    statusFilter === 'all'
      ? referrals
      : referrals.filter((referral) => referral.status === statusFilter)

  function facilityName(id) {
    return facilities.find((facility) => facility.id === id)?.name ?? `Facility #${id}`
  }

  return (
    <section className="my-10 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:p-7">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900">
          Referral Management
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Create referrals and track their progress between healthcare facilities.
        </p>
      </div>

      {error && (
        <div role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {message && (
        <div role="status" className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-700">
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mb-8 rounded-xl bg-slate-50 p-4 md:p-5">
        <h3 className="mb-4 text-lg font-semibold text-slate-800">
          Create New Referral
        </h3>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">
            Patient name (use fictional demo data)
            <input
              name="patient_name"
              value={form.patient_name}
              onChange={handleChange}
              required
              maxLength={120}
              placeholder="Fictional Demo Patient"
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal"
            />
          </label>

          <label className="text-sm font-medium text-slate-700">
            Patient age (optional)
            <input
              name="patient_age"
              type="number"
              min="0"
              max="120"
              value={form.patient_age}
              onChange={handleChange}
              placeholder="35"
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal"
            />
          </label>

          <label className="text-sm font-medium text-slate-700">
            Referring facility
            <select
              name="from_facility_id"
              value={form.from_facility_id}
              onChange={handleChange}
              required
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal"
            >
              <option value="">Select source facility</option>
              {facilities.map((facility) => (
                <option key={facility.id} value={facility.id}>
                  {facility.name}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-slate-700">
            Destination facility
            <select
              name="to_facility_id"
              value={form.to_facility_id}
              onChange={handleChange}
              required
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal"
            >
              <option value="">Select destination facility</option>
              {facilities.map((facility) => (
                <option key={facility.id} value={facility.id}>
                  {facility.name}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-slate-700 md:col-span-2">
            Notes (optional)
            <textarea
              name="notes"
              value={form.notes}
              onChange={handleChange}
              rows={2}
              maxLength={1000}
              placeholder="Demo referral notes"
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal"
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={submitting || loading || facilities.length < 2}
          className="mt-4 rounded-lg bg-blue-700 px-5 py-2.5 font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? 'Creating...' : 'Create Referral'}
        </button>
      </form>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-800">
          Referral Records ({visibleReferrals.length})
        </h3>

        <select
          aria-label="Filter referrals by status"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {loading ? (
        <p className="py-6 text-slate-500">Loading referral records...</p>
      ) : visibleReferrals.length === 0 ? (
        <p className="rounded-lg bg-slate-50 p-5 text-slate-600">
          No referrals found for this filter.
        </p>
      ) : (
        <div className="space-y-4">
          {visibleReferrals.map((referral) => (
            <article
              key={referral.id}
              className="rounded-xl border border-slate-200 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-slate-900">
                    Referral #{referral.id} — {referral.patient_name}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    Age: {referral.patient_age ?? 'Not specified'}
                  </p>
                </div>

                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                  {STATUS_LABELS[referral.status] ?? referral.status}
                </span>
              </div>

              <div className="mt-3 grid gap-3 text-sm md:grid-cols-2">
                <div>
                  <p className="text-slate-500">From</p>
                  <p className="font-medium text-slate-800">
                    {facilityName(referral.from_facility_id)}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">To</p>
                  <p className="font-medium text-slate-800">
                    {facilityName(referral.to_facility_id)}
                  </p>
                </div>
              </div>

              {referral.notes && (
                <p className="mt-3 text-sm text-slate-600">
                  Notes: {referral.notes}
                </p>
              )}

              {NEXT_STATUSES[referral.status]?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {NEXT_STATUSES[referral.status].map((nextStatus) => (
                    <button
                      key={nextStatus}
                      type="button"
                      disabled={updatingId === referral.id}
                      onClick={() => handleStatusUpdate(referral.id, nextStatus)}
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
                    >
                      {updatingId === referral.id
                        ? 'Updating...'
                        : `Mark ${STATUS_LABELS[nextStatus]}`}
                    </button>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      <p className="mt-6 text-xs text-slate-500">
        Demo only: use fictional data. This prototype is not for real patient records or clinical decisions.
      </p>
    </section>
  )
}

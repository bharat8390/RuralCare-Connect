
import { useEffect, useState } from 'react'
import {
  getFacilities,
  getResources,
  saveResource,
} from './api'

export default function ResourceSection() {
  const [facilities, setFacilities] = useState([])
  const [resources, setResources] = useState([])
  const [facilityId, setFacilityId] = useState('')
  const [resourceName, setResourceName] = useState('')
  const [quantity, setQuantity] = useState('0')
  const [status, setStatus] = useState('available')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function loadData() {
    setLoading(true)
    setError('')

    try {
      const [facilityData, resourceData] = await Promise.all([
        getFacilities(),
        getResources(),
      ])

      const facilityList = facilityData.facilities ?? []
      setFacilities(facilityList)
      setResources(resourceData.resources ?? [])

      setFacilityId((current) => {
        if (current && facilityList.some(
          (facility) => String(facility.id) === current
        )) {
          return current
        }

        return facilityList.length
          ? String(facilityList[0].id)
          : ''
      })
    } catch (err) {
      setError(err.message || 'Unable to load resources.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')

    if (!facilityId) {
      setError('Please select a facility.')
      return
    }

    if (!resourceName.trim()) {
      setError('Please enter a resource name.')
      return
    }

    const parsedQuantity = Number(quantity)

    if (
      !Number.isInteger(parsedQuantity) ||
      parsedQuantity < 0
    ) {
      setError('Quantity must be a non-negative whole number.')
      return
    }

    setSaving(true)

    try {
      await saveResource({
        facility_id: Number(facilityId),
        resource_name: resourceName.trim(),
        quantity: parsedQuantity,
        status,
      })

      setMessage('Resource saved successfully.')
      setResourceName('')
      setQuantity('0')
      await loadData()
    } catch (err) {
      setError(err.message || 'Unable to save resource.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="mb-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-xl font-bold text-slate-800">
          Resource Management
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Track essential resources and availability at each facility.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
      >
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Healthcare facility
          </label>
          <select
            value={facilityId}
            onChange={(event) => setFacilityId(event.target.value)}
            className="w-full rounded-lg border border-slate-300 p-2.5"
            required
          >
            <option value="">Select facility</option>
            {facilities.map((facility) => (
              <option key={facility.id} value={facility.id}>
                {facility.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Resource name
          </label>
          <input
            value={resourceName}
            onChange={(event) => setResourceName(event.target.value)}
            placeholder="e.g. Diagnostic test kits"
            maxLength={100}
            className="w-full rounded-lg border border-slate-300 p-2.5"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Quantity
          </label>
          <input
            type="number"
            min="0"
            step="1"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            className="w-full rounded-lg border border-slate-300 p-2.5"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Availability status
          </label>
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="w-full rounded-lg border border-slate-300 p-2.5"
          >
            <option value="available">Available</option>
            <option value="low">Low stock</option>
            <option value="unavailable">Unavailable</option>
          </select>
        </div>

        <div className="md:col-span-2 lg:col-span-4">
          <button
            type="submit"
            disabled={saving || loading || facilities.length === 0}
            className="rounded-lg bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Resource'}
          </button>
        </div>
      </form>

      {error && (
        <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {message && (
        <p role="status" className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-700">
          {message}
        </p>
      )}

      <h3 className="mb-3 text-lg font-semibold text-slate-800">
        Facility Resource Inventory
      </h3>

      {loading ? (
        <p className="text-sm text-slate-500">Loading resources...</p>
      ) : resources.length === 0 ? (
        <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">
          No resources recorded yet. Add your first resource above.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[650px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="p-3">Facility</th>
                <th className="p-3">Resource</th>
                <th className="p-3">Quantity</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {resources.map((resource) => (
                <tr
                  key={`${resource.facility_id}-${resource.resource_name}`}
                  className="border-b border-slate-100"
                >
                  <td className="p-3">{resource.facility_name}</td>
                  <td className="p-3 font-medium">{resource.resource_name}</td>
                  <td className="p-3">{resource.quantity}</td>
                  <td className="p-3">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                        resource.status === 'available'
                          ? 'bg-green-100 text-green-700'
                          : resource.status === 'low'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {resource.status === 'low'
                        ? 'Low stock'
                        : resource.status === 'unavailable'
                          ? 'Unavailable'
                          : 'Available'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

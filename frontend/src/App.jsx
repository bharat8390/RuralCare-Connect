import ResourceSection from './ResourceSection'
import Dashboard from './Dashboard'
import FollowUpSection from './FollowUpSection'
import ReferralSection from './ReferralSection.jsx'
import { useEffect, useState } from 'react'
import { getFacilities, getFacility } from './api.js'

const FACILITY_TYPES = [
  {
    value: 'sub_centre',
    en: 'Sub-Centre',
    mr: 'उपकेंद्र',
  },
  {
    value: 'phc',
    en: 'Primary Health Centre',
    mr: 'प्राथमिक आरोग्य केंद्र',
  },
  {
    value: 'chc',
    en: 'Community Health Centre',
    mr: 'सामुदायिक आरोग्य केंद्र',
  },
  {
    value: 'rural_hospital',
    en: 'Rural Hospital',
    mr: 'ग्रामीण रुग्णालय',
  },
]

function typeLabel(value) {
  return FACILITY_TYPES.find((item) => item.value === value)
}

function statusLabel(status) {
  if (status === 'available') {
    return { en: 'Available', mr: 'उपलब्ध', className: 'bg-green-100 text-green-800' }
  }
  return { en: 'Unavailable', mr: 'अनुपलब्ध', className: 'bg-rose-100 text-rose-800' }
}

function App() {
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [district, setDistrict] = useState('')
  const [facilityType, setFacilityType] = useState('')
  const [districts, setDistricts] = useState([])
  const [facilities, setFacilities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [details, setDetails] = useState(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [detailsError, setDetailsError] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    const controller = new AbortController()

    async function loadFacilities() {
      setLoading(true)
      setError('')
      try {
        const data = await getFacilities({
          q: search,
          district,
          facilityType,
          signal: controller.signal,
        })
        setFacilities(data.facilities)
        setDistricts(data.districts)
      } catch (err) {
        if (err.name === 'AbortError') return
        setFacilities([])
        setError(err.message || 'Could not load facilities.')
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadFacilities()
    return () => controller.abort()
  }, [search, district, facilityType])

  useEffect(() => {
    if (selectedId == null) {
      return
    }

    const controller = new AbortController()

    async function loadDetails() {
      setDetailsLoading(true)
      setDetailsError('')
      try {
        const data = await getFacility(selectedId, { signal: controller.signal })
        setDetails(data)
      } catch (err) {
        if (err.name === 'AbortError') return
        setDetails(null)
        setDetailsError(err.message || 'Could not load facility details.')
      } finally {
        if (!controller.signal.aborted) {
          setDetailsLoading(false)
        }
      }
    }

    loadDetails()
    return () => controller.abort()
  }, [selectedId])
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        <header className="mb-8">
          <h1 className="text-3xl font-bold">RuralCare Connect</h1>
          <p className="mt-1 text-xl" lang="mr">
            ग्रामीण आरोग्य सेवा जोडणी
          </p>
          <p className="mt-4 text-slate-600">
            Public healthcare facility directory
          </p>
          <p className="mt-1 text-slate-600" lang="mr">
            सार्वजनिक आरोग्य केंद्र निर्देशिका
          </p>
        </header>
        <Dashboard />
        <ResourceSection />
        <ReferralSection />
        <FollowUpSection />

        <form
          className="mb-6 grid gap-4 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-3"
          onSubmit={(event) => event.preventDefault()}
        >
          <label className="block sm:col-span-3 md:col-span-1">
            <span className="block text-sm font-medium">Search</span>
            <span className="block text-sm text-slate-500" lang="mr">
              शोधा
            </span>
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Name, village, or service"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>

          <label className="block">
            <span className="block text-sm font-medium">District</span>
            <span className="block text-sm text-slate-500" lang="mr">
              जिल्हा
            </span>
            <select
              value={district}
              onChange={(event) => setDistrict(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="">All districts / सर्व जिल्हे</option>
              {districts.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="block text-sm font-medium">Facility type</span>
            <span className="block text-sm text-slate-500" lang="mr">
              केंद्र प्रकार
            </span>
            <select
              value={facilityType}
              onChange={(event) => setFacilityType(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="">All types / सर्व प्रकार</option>
              {FACILITY_TYPES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.en} / {item.mr}
                </option>
              ))}
            </select>
          </label>
        </form>

        {loading ? (
          <p className="rounded-xl border border-slate-200 bg-white p-6 text-slate-600">
            Loading facilities...
            <span className="mt-1 block" lang="mr">
              केंद्रे लोड होत आहेत...
            </span>
          </p>
        ) : null}

        {error ? (
          <p className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
            {error}
            <span className="mt-1 block" lang="mr">
              केंद्रे दाखवता आली नाहीत. कृपया बॅकएंड चालू आहे का ते तपासा.
            </span>
          </p>
        ) : null}

        {!loading && !error && facilities.length === 0 ? (
          <p className="rounded-xl border border-slate-200 bg-white p-6 text-slate-600">
            No facilities match these filters.
            <span className="mt-1 block" lang="mr">
              या शोध निकषांशी जुळणारे केंद्र नाही.
            </span>
          </p>
        ) : null}

        <div className="grid gap-4">
          {facilities.map((facility) => {
            const type = typeLabel(facility.facility_type)
            const isOpen = selectedId === facility.id
            return (
              <article
                key={facility.id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">{facility.name}</h2>
                    {facility.name_mr ? (
                      <p className="text-slate-700" lang="mr">
                        {facility.name_mr}
                      </p>
                    ) : null}
                    <p className="mt-2 text-sm text-slate-600">
                      {type ? `${type.en} / ${type.mr}` : facility.facility_type}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      <span className="font-medium">District / </span>
                      <span lang="mr">जिल्हा: </span>
                      {facility.district || '—'}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      <span className="font-medium">Address / </span>
                      <span lang="mr">पत्ता: </span>
                      {facility.address}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
                    onClick={() => {
                      if (selectedId === facility.id) {
                        setSelectedId(null)
                        setDetails(null)
                        setDetailsError('')
                        return
                      }
                      setSelectedId(facility.id)
                    }}
                  >
                    {isOpen ? 'Hide details / तपशील लपवा' : 'View details / तपशील पहा'}
                  </button>
                </div>

                <div className="mt-4">
                  <h3 className="text-sm font-medium">
                    Services / <span lang="mr">सेवा</span>
                  </h3>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {facility.services.map((service) => {
                      const status = statusLabel(service.status)
                      return (
                        <li
                          key={service.id}
                          className="rounded-full bg-slate-100 px-3 py-1 text-sm"
                        >
                          {service.name}
                          {service.name_mr ? (
                            <span lang="mr"> / {service.name_mr}</span>
                          ) : null}
                          <span
                            className={`ml-2 rounded-full px-2 py-0.5 text-xs ${status.className}`}
                          >
                            {status.en} / {status.mr}
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                </div>

                {isOpen ? (
                  <div className="mt-4 border-t border-slate-200 pt-4">
                    {detailsLoading ? (
                      <p className="text-sm text-slate-600">
                        Loading details...
                        <span className="block" lang="mr">
                          तपशील लोड होत आहेत...
                        </span>
                      </p>
                    ) : null}
                    {detailsError ? (
                      <p className="text-sm text-rose-700">{detailsError}</p>
                    ) : null}
                    {details && details.id === facility.id ? (
                      <div className="text-sm text-slate-700">
                        {details.phone ? (
                          <p>
                            Phone / <span lang="mr">दूरध्वनी:</span> {details.phone}
                          </p>
                        ) : null}
                        <ul className="mt-3 grid gap-2">
                          {details.services.map((service) => {
                            const status = statusLabel(service.status)
                            return (
                              <li
                                key={service.id}
                                className="rounded-lg bg-slate-50 p-3"
                              >
                                <p className="font-medium">
                                  {service.name}
                                  {service.name_mr ? (
                                    <span lang="mr"> / {service.name_mr}</span>
                                  ) : null}
                                </p>
                                {service.description ? (
                                  <p className="mt-1 text-slate-600">
                                    {service.description}
                                  </p>
                                ) : null}
                                <p className={`mt-2 inline-block rounded-full px-2 py-0.5 text-xs ${status.className}`}>
                                  {status.en} / {status.mr}
                                </p>
                              </li>
                            )
                          })}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </article>
            )
          })}
        </div>
      </div>
    </main>
  )
}

export default App

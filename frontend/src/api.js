export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001/api/v1'

async function readJson(response, fallbackMessage) {
  if (!response.ok) {
    throw new Error(fallbackMessage)
  }
  return response.json()
}

export async function getFacilities({ q, district, facilityType, signal } = {}) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (district) params.set('district', district)
  if (facilityType) params.set('facility_type', facilityType)

  const query = params.toString()
  const url = query
    ? `${API_BASE_URL}/facilities?${query}`
    : `${API_BASE_URL}/facilities`

  const response = await fetch(url, { signal })
  return readJson(response, 'Could not load facilities.')
}

export async function getFacility(facilityId, { signal } = {}) {
  const response = await fetch(`${API_BASE_URL}/facilities/${facilityId}`, {
    signal,
  })
  if (response.status === 404) {
    throw new Error('Facility not found.')
  }
  return readJson(response, 'Could not load facility details.')
}


export async function getReferrals({ status, signal } = {}) {
  const params = new URLSearchParams()

  if (status) params.set('status', status)

  const query = params.toString()
  const url = query
    ? `${API_BASE_URL}/referrals?${query}`
    : `${API_BASE_URL}/referrals`

  const response = await fetch(url, { signal })
  return readJson(response, 'Could not load referrals.')
}

export async function createReferral(referral) {
  const response = await fetch(`${API_BASE_URL}/referrals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(referral),
  })

  return readJson(response, 'Could not create referral. Check the submitted details.')
}

export async function updateReferralStatus(referralId, status) {
  const response = await fetch(
    `${API_BASE_URL}/referrals/${referralId}/status`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    },
  )

  return readJson(response, 'Could not update referral status.')
}


export async function getFollowUps({ status, signal } = {}) {
  const params = new URLSearchParams()

  if (status) params.set('status', status)

  const query = params.toString()
  const url = query
    ? `${API_BASE_URL}/follow-ups?${query}`
    : `${API_BASE_URL}/follow-ups`

  const response = await fetch(url, { signal })
  return readJson(response, 'Could not load follow-ups.')
}

export async function createFollowUp(followUp) {
  const response = await fetch(`${API_BASE_URL}/follow-ups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(followUp),
  })

  return readJson(response, 'Could not create follow-up. Check the submitted details.')
}

export async function updateFollowUpStatus(followUpId, status) {
  const response = await fetch(
    `${API_BASE_URL}/follow-ups/${followUpId}/status`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    },
  )

  return readJson(response, 'Could not update follow-up status.')
}


export async function getResources({ facilityId, signal } = {}) {
  const params = new URLSearchParams();

  if (facilityId != null) {
    params.set('facility_id', facilityId);
  }

  const query = params.toString();
  const url = `${API_BASE_URL}/resources${query ? `?${query}` : ''}`;

  const response = await fetch(url, { signal });
  return readJson(response, 'Unable to load resources.');
}

export async function getResourceSummary({ signal } = {}) {
  const response = await fetch(`${API_BASE_URL}/resources/summary`, {
    signal,
  });

  return readJson(response, 'Unable to load resource summary.');
}

export async function saveResource(resource) {
  const response = await fetch(`${API_BASE_URL}/resources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(resource),
  });

  return readJson(response, 'Unable to save resource.');
}


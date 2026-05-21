export const BAMENDA_FACILITIES = [
  {
    id: 1,
    name: 'Bamenda Regional Hospital',
    type: 'Regional / Government Hospital',
    address: 'X43V+WH7, Bamenda, Cameroon',
    phone: '+237 2 33 36 11 08',
    hours: 'Open 24 hours',
    coords: [5.95462, 10.144],
    services: ['Emergency', 'Maternity', 'Surgery', 'Laboratory', 'Radiology', 'Paediatrics'],
    mapQuery: 'Bamenda+Regional+Hospital+Cameroon',
    emergency: true,
    rating: 'Regional referral hospital',
    color: 'border-red-400',
    headerBg: 'bg-red-50 dark:bg-red-950/30',
    sourceName: 'AfricaBizInfo / WorldPlaces',
    sourceUrl: 'https://www.africabizinfo.com/fr-CM/bamenda-regional-hospital-2-33-36-11-08',
  },
  {
    id: 2,
    name: 'Nkwen Baptist Hospital Bamenda',
    type: 'CBC Mission Hospital',
    address: 'Finance Junction, Bamenda II, Mezam Division',
    phone: '+237 675 205 729 / +237 683 158 210',
    hours: 'Open 24 hours',
    coords: [5.9832, 10.1588],
    services: ['Emergency', 'Maternity', 'Surgery', 'Paediatrics', 'Dental', 'Laboratory'],
    mapQuery: 'Nkwen+Baptist+Hospital+Bamenda+Cameroon',
    emergency: true,
    rating: 'CBC Health Services hospital',
    color: 'border-blue-400',
    headerBg: 'bg-blue-50 dark:bg-blue-950/30',
    sourceName: 'CBC Health Services',
    sourceUrl: 'https://cbchealthservices.org/health-centers/north-west-region/nkwen-baptist-hospital/',
  },
  {
    id: 3,
    name: 'Mezam Polyclinic',
    type: 'Private Polyclinic',
    address: 'Azire / W4XW+G5V, Bamenda, Cameroon',
    phone: '+237 6 77 68 48 78 / +237 2 33 36 34 31',
    hours: 'Open 24 hours',
    coords: [5.948872, 10.1454174],
    services: ['General Practice', 'Paediatrics', 'Obstetrics', 'Gynaecology', 'Surgery', 'Dentistry'],
    mapQuery: 'Mezam+Polyclinic+Bamenda+Cameroon',
    emergency: true,
    rating: 'Private clinic serving Bamenda',
    color: 'border-orange-400',
    headerBg: 'bg-orange-50 dark:bg-orange-950/30',
    sourceName: 'Maligah / Near Place',
    sourceUrl: 'https://maligah.com/entreprises/details/mezam-polyclinic?id=46091',
  },
  {
    id: 4,
    name: 'Mbingo Baptist Hospital',
    type: 'CBC Referral / Teaching Hospital',
    address: 'Belo Subdivision, North West Region, via Bamenda',
    phone: '+237 677 671 621 / +237 676 221 260',
    hours: 'Open 24 hours',
    coords: [6.176, 10.158],
    services: ['Referral Care', 'Surgery', 'Internal Medicine', 'HIV/AIDS Care', 'Training Centre'],
    mapQuery: 'Mbingo+Baptist+Hospital+Cameroon',
    emergency: true,
    rating: 'CBC referral hospital',
    color: 'border-teal-400',
    headerBg: 'bg-teal-50 dark:bg-teal-950/30',
    sourceName: 'BIHS / VFMatch',
    sourceUrl: 'https://bihs.mbingo.org/en/contact/',
  },
  {
    id: 5,
    name: 'Banso Baptist Hospital',
    type: 'CBC Mission Hospital',
    address: 'P.O. Box 9, Banso / Kumbo, Bui Division',
    phone: '+237 677 720 005 / +237 678 479 628',
    hours: 'Open 24 hours',
    coords: [6.21365, 10.68953],
    services: ['Emergency', 'Maternity', 'Surgery', 'Ophthalmology', 'Paediatrics', 'Cardiology'],
    mapQuery: 'Banso+Baptist+Hospital+Kumbo+Cameroon',
    emergency: true,
    rating: 'CBC district hospital',
    color: 'border-green-400',
    headerBg: 'bg-green-50 dark:bg-green-950/30',
    sourceName: 'CBC Health Services',
    sourceUrl: 'https://cbchealthservices.org/hospitals/banso-baptist-hospital/',
  },
  {
    id: 6,
    name: 'St. Martin de Porres Catholic Mission Hospital',
    type: 'Catholic Mission Hospital',
    address: 'Njinikom, North West Region',
    phone: '+237 6 65 84 26 16 / +237 6 65 84 26 19',
    hours: 'Open 24 hours',
    coords: [6.235, 10.284],
    services: ['General Care', 'Maternity', 'Surgery', 'Laboratory', 'Inpatient Care'],
    mapQuery: 'St+Martin+de+Porres+Catholic+Mission+Hospital+Njinikom+Cameroon',
    emergency: true,
    rating: 'Catholic mission hospital',
    color: 'border-purple-400',
    headerBg: 'bg-purple-50 dark:bg-purple-950/30',
    sourceName: 'Cybo',
    sourceUrl: 'https://www.cybo.com/CM-biz/st-martin-de-porres-catholic-mission',
  },
];

export const facilityDirectionsUrl = (facility, userLocation = null) => {
  const destination = facility.mapQuery || (facility.coords ? `${facility.coords[0]},${facility.coords[1]}` : facility.name);
  if (userLocation) {
    const lat = userLocation.lat ?? userLocation[0];
    const lng = userLocation.lng ?? userLocation[1];
    return `https://www.google.com/maps/dir/?api=1&origin=${lat},${lng}&destination=${destination}`;
  }
  return `https://www.google.com/maps/dir/?api=1&destination=${destination}`;
};

export const facilityMapsUrl = (facility) =>
  `https://www.google.com/maps/search/?api=1&query=${facility.mapQuery || encodeURIComponent(facility.name)}`;

export const facilityEmbedUrl = (facility) =>
  `https://maps.google.com/maps?q=${facility.mapQuery || encodeURIComponent(facility.name)}&output=embed&z=16&hl=en`;

export const facilityDistanceKm = (facility, userLocation = null) => {
  if (!facility?.coords || !userLocation) return null;
  const [facilityLat, facilityLng] = facility.coords;
  const userLat = userLocation.lat ?? userLocation[0];
  const userLng = userLocation.lng ?? userLocation[1];
  if ([facilityLat, facilityLng, userLat, userLng].some((value) => Number.isNaN(Number(value)))) {
    return null;
  }
  const toRad = (value) => (Number(value) * Math.PI) / 180;
  const earthKm = 6371;
  const dLat = toRad(facilityLat - userLat);
  const dLng = toRad(facilityLng - userLng);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(userLat)) * Math.cos(toRad(facilityLat)) * Math.sin(dLng / 2) ** 2;
  return earthKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

export const facilityDistanceLabel = (facility, userLocation = null) => {
  const km = facilityDistanceKm(facility, userLocation);
  if (km == null) return null;
  return km < 1 ? `${Math.round(km * 1000)} m away` : `${km.toFixed(1)} km away`;
};

const facilityTypeFromTags = (tags = {}) => {
  if (tags.healthcare === 'hospital' || tags.amenity === 'hospital') return 'Hospital';
  if (tags.healthcare === 'clinic' || tags.amenity === 'clinic') return 'Clinic';
  if (tags.healthcare === 'doctors') return 'Doctors / Medical Practice';
  if (tags.healthcare === 'pharmacy' || tags.amenity === 'pharmacy') return 'Pharmacy';
  return 'Health Facility';
};

const addressFromTags = (tags = {}) => {
  const parts = [
    tags['addr:housenumber'],
    tags['addr:street'],
    tags['addr:suburb'],
    tags['addr:city'],
    tags['addr:state'],
    tags['addr:country'],
  ].filter(Boolean);
  return parts.length ? parts.join(', ') : tags.address || 'Address not listed';
};

export const fetchNearbyFacilities = async ({ lat, lng, radius = 12000, limit = 20 }) => {
  const query = `
    [out:json][timeout:25];
    (
      node(around:${radius},${lat},${lng})["amenity"~"hospital|clinic|doctors"];
      way(around:${radius},${lat},${lng})["amenity"~"hospital|clinic|doctors"];
      relation(around:${radius},${lat},${lng})["amenity"~"hospital|clinic|doctors"];
      node(around:${radius},${lat},${lng})["healthcare"~"hospital|clinic|doctor|doctors"];
      way(around:${radius},${lat},${lng})["healthcare"~"hospital|clinic|doctor|doctors"];
      relation(around:${radius},${lat},${lng})["healthcare"~"hospital|clinic|doctor|doctors"];
    );
    out center tags ${limit};
  `;

  const response = await fetch('https://overpass-api.de/api/interpreter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
    body: new URLSearchParams({ data: query }),
  });

  if (!response.ok) {
    throw new Error('Nearby facility search failed.');
  }

  const data = await response.json();
  const userLocation = { lat, lng };
  const seen = new Set();
  return (data.elements || [])
    .map((element) => {
      const tags = element.tags || {};
      const facilityLat = element.lat ?? element.center?.lat;
      const facilityLng = element.lon ?? element.center?.lon;
      const name = tags.name || tags.operator || 'Unnamed health facility';
      if (!facilityLat || !facilityLng || !name) return null;
      const dedupeKey = `${name.toLowerCase()}-${facilityLat.toFixed(4)}-${facilityLng.toFixed(4)}`;
      if (seen.has(dedupeKey)) return null;
      seen.add(dedupeKey);
      const facility = {
        id: `osm-${element.type}-${element.id}`,
        name,
        type: facilityTypeFromTags(tags),
        address: addressFromTags(tags),
        phone: tags.phone || tags['contact:phone'] || tags.mobile || '',
        hours: tags.opening_hours || 'Hours not listed',
        coords: [facilityLat, facilityLng],
        services: ['Nearby care', facilityTypeFromTags(tags), tags.emergency === 'yes' ? 'Emergency' : null].filter(Boolean),
        mapQuery: `${facilityLat},${facilityLng}`,
        emergency: tags.emergency === 'yes' || tags.amenity === 'hospital' || tags.healthcare === 'hospital',
        rating: 'Live OpenStreetMap result',
        color: 'border-primary/50',
        headerBg: 'bg-primary/5',
        sourceName: 'OpenStreetMap / Overpass',
        sourceUrl: `https://www.openstreetmap.org/${element.type}/${element.id}`,
        live: true,
      };
      return {
        ...facility,
        distanceKm: facilityDistanceKm(facility, userLocation),
      };
    })
    .filter(Boolean)
    .sort((a, b) => (a.distanceKm ?? Number.MAX_SAFE_INTEGER) - (b.distanceKm ?? Number.MAX_SAFE_INTEGER))
    .slice(0, limit);
};

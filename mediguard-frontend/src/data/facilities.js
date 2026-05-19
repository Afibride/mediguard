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
  const destination = facility.mapQuery;
  if (userLocation) {
    const lat = userLocation.lat ?? userLocation[0];
    const lng = userLocation.lng ?? userLocation[1];
    return `https://www.google.com/maps/dir/?api=1&origin=${lat},${lng}&destination=${destination}`;
  }
  return `https://www.google.com/maps/dir/?api=1&destination=${destination}`;
};

export const facilityMapsUrl = (facility) =>
  `https://www.google.com/maps/search/?api=1&query=${facility.mapQuery}`;

export const facilityEmbedUrl = (facility) =>
  `https://maps.google.com/maps?q=${facility.mapQuery}&output=embed&z=16&hl=en`;

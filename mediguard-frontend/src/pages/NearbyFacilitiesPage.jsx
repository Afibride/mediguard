import React, { useEffect, useRef, useState } from 'react';
import { Helmet } from 'react-helmet';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  Building2,
  Clock,
  ExternalLink,
  Locate,
  MapPin,
  Navigation,
  Phone,
  Star,
} from 'lucide-react';
import {
  BAMENDA_FACILITIES,
  facilityDirectionsUrl,
  facilityDistanceKm,
  facilityDistanceLabel,
  facilityEmbedUrl,
  facilityMapsUrl,
} from '@/data/facilities';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

function FacilityMapEmbed({ facility, large = false }) {
  return (
    <div className={`w-full overflow-hidden rounded-lg border bg-muted ${large ? 'h-[340px] sm:h-[420px] md:h-[520px]' : 'h-48 sm:h-56 md:h-72'}`}>
      <iframe
        title={`${facility.name} map preview`}
        src={facilityEmbedUrl(facility)}
        width="100%"
        height="100%"
        style={{ border: 0 }}
        allowFullScreen
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
      />
    </div>
  );
}

const NearbyFacilitiesPage = () => {
  const [selectedId, setSelectedId] = useState(BAMENDA_FACILITIES[0].id);
  const [userLocation, setUserLocation] = useState(null);
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState('');
  const cardRefs = useRef({});

  const selected = BAMENDA_FACILITIES.find((facility) => facility.id === selectedId) || BAMENDA_FACILITIES[0];
  const orderedFacilities = [...BAMENDA_FACILITIES].sort((a, b) => {
    if (a.id === selectedId) return -1;
    if (b.id === selectedId) return 1;
    if (userLocation) {
      return (facilityDistanceKm(a, userLocation) ?? Number.MAX_SAFE_INTEGER) - (facilityDistanceKm(b, userLocation) ?? Number.MAX_SAFE_INTEGER);
    }
    return a.id - b.id;
  });

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Location is not supported by this browser.');
      return;
    }

    setLocating(true);
    setLocationError('');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      (error) => {
        setLocationError(
          error.code === error.PERMISSION_DENIED
            ? 'Allow location access in your browser to sort hospitals by distance.'
            : 'Could not get your location. Check GPS/network and try again.'
        );
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
    );
  };

  useEffect(() => {
    requestLocation();
  }, []);

  const selectFacility = (facility) => {
    setSelectedId(facility.id);
    window.requestAnimationFrame(() => {
      cardRefs.current[facility.id]?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
    });
  };

  return (
    <>
      <Helmet>
        <title>Nearby Health Facilities - MediGuard Bamenda</title>
        <meta
          name="description"
          content="Find nearby hospitals and clinics in Bamenda with in-app maps, phone numbers, services, and directions."
        />
      </Helmet>

      <div className="min-h-screen bg-muted/30">
        <div className="border-b bg-background px-4 py-4 md:py-6">
          <div className="container mx-auto max-w-6xl">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="flex items-center gap-2 text-xl font-bold sm:text-2xl md:text-3xl">
                  <MapPin className="h-6 w-6 text-primary md:h-7 md:w-7" />
                  Nearby Health Facilities
                </h1>
                <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                  {BAMENDA_FACILITIES.length} trusted facilities with maps, contacts, and directions
                </p>
              </div>
              <Button
                variant="outline"
                onClick={requestLocation}
                disabled={locating}
                className="w-full gap-2 text-sm sm:w-auto"
                size="sm"
              >
                <Locate className={`h-4 w-4 ${locating ? 'animate-spin' : ''}`} />
                {userLocation ? 'Location ready' : locating ? 'Locating...' : 'Use my location'}
              </Button>
            </div>
            {userLocation && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-2 text-xs text-green-600 dark:text-green-400">
                Facilities are now sorted by distance from your current location.
              </motion.p>
            )}
            {locationError && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-2 text-xs text-red-600 dark:text-red-400">
                {locationError}
              </motion.p>
            )}
          </div>
        </div>

        <div className="container mx-auto max-w-6xl px-4 py-4 md:py-6">
          <div className="flex flex-col-reverse gap-5 lg:grid lg:grid-cols-5 lg:gap-6">
            <div className="lg:col-span-2">
              <div className="mb-2 flex items-center justify-between lg:hidden">
                <h2 className="text-sm font-semibold text-muted-foreground">
                  Available Facilities ({BAMENDA_FACILITIES.length})
                </h2>
                <p className="text-xs text-muted-foreground">Tap to view details</p>
              </div>

              <div className="grid grid-flow-col grid-rows-2 auto-cols-[minmax(250px,84vw)] gap-3 overflow-x-auto pb-3 lg:block lg:space-y-3 lg:overflow-visible lg:pb-0">
                {orderedFacilities.map((facility, index) => {
                  const isSelected = facility.id === selectedId;
                  const distance = facilityDistanceLabel(facility, userLocation);
                  return (
                    <motion.div
                      key={facility.id}
                      ref={(el) => {
                        cardRefs.current[facility.id] = el;
                      }}
                      layout
                      initial={{ opacity: 0, x: -16 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                    >
                      <Card
                        className={`cursor-pointer overflow-hidden border-2 transition-all duration-200 ${
                          isSelected ? `${facility.color} shadow-md ring-2 ring-primary/20` : 'border-border hover:border-primary/40'
                        }`}
                        onClick={() => selectFacility(facility)}
                      >
                        <div className={`p-3 sm:p-4 ${isSelected ? facility.headerBg : ''}`}>
                          <div className="flex items-start gap-2">
                            <Building2 className={`mt-0.5 h-4 w-4 flex-shrink-0 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                            <div className="min-w-0 flex-1">
                              <div className="mb-1.5 flex flex-wrap gap-1">
                                {facility.emergency && (
                                  <Badge variant="destructive" className="px-1.5 py-0 text-[10px]">
                                    <AlertCircle className="mr-0.5 h-2.5 w-2.5" />
                                    24/7 Emergency
                                  </Badge>
                                )}
                                {isSelected && <Badge variant="secondary" className="px-1.5 py-0 text-[10px]">Selected first</Badge>}
                              </div>
                              <p className="text-sm font-bold leading-snug sm:text-base">{facility.name}</p>
                              <p className="text-xs text-muted-foreground sm:text-sm">{facility.type}</p>
                              {distance && <p className="mt-0.5 text-xs font-semibold text-primary">{distance}</p>}
                              <p className="mt-1 flex items-start gap-1 text-xs text-muted-foreground line-clamp-2">
                                <MapPin className="mt-0.5 h-3 w-3 flex-shrink-0" />
                                <span className="flex-1">{facility.address}</span>
                              </p>
                              <a
                                href={`tel:${facility.phone.split('/')[0].trim()}`}
                                className="mt-1 flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                                onClick={(event) => event.stopPropagation()}
                              >
                                <Phone className="h-3 w-3" />
                                <span className="truncate">{facility.phone}</span>
                              </a>
                            </div>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            <div className="lg:col-span-3">
              <div className="mb-3 overflow-x-auto pb-2 lg:hidden">
                <div className="flex gap-2">
                  {orderedFacilities.map((facility) => (
                    <button
                      key={facility.id}
                      type="button"
                      onClick={() => selectFacility(facility)}
                      className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition-all whitespace-nowrap ${
                        facility.id === selectedId
                          ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                          : 'border-border bg-background hover:border-primary/50'
                      }`}
                    >
                      {facility.name}
                    </button>
                  ))}
                </div>
              </div>

              <Card className="mb-4 overflow-hidden">
                <FacilityMapEmbed facility={selected} large />
                <div className="border-t bg-background px-3 py-2 sm:px-4 sm:py-3">
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {orderedFacilities.map((facility) => (
                      <button
                        key={facility.id}
                        type="button"
                        onClick={() => selectFacility(facility)}
                        className={`shrink-0 rounded-full border px-2 py-1 text-[11px] font-medium transition-colors sm:px-3 sm:py-1.5 sm:text-xs whitespace-nowrap ${
                          facility.id === selectedId
                            ? 'border-primary bg-primary text-primary-foreground'
                            : 'border-border bg-muted/40 hover:border-primary/50'
                        }`}
                      >
                        {facility.name}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="border-t bg-muted/30 px-3 py-2 sm:px-4">
                  <p className="text-[11px] text-muted-foreground sm:text-xs">
                    This is the main map. Select any facility to move the map to that location.
                  </p>
                </div>
              </Card>

              <motion.div key={selected.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                <Card className={`border-2 ${selected.color}`}>
                  <CardHeader className={`p-4 pb-3 sm:p-6 ${selected.headerBg}`}>
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="flex-1">
                        {selected.emergency && (
                          <Badge variant="destructive" className="mb-2 text-xs">
                            <AlertCircle className="mr-1 h-3 w-3" />
                            24/7 Emergency Care
                          </Badge>
                        )}
                        <CardTitle className="flex items-center gap-2 text-lg sm:text-xl md:text-2xl">
                          <Building2 className="h-5 w-5 flex-shrink-0" />
                          <span className="break-words">{selected.name}</span>
                        </CardTitle>
                        <p className="mt-0.5 text-xs text-muted-foreground sm:text-sm">{selected.type}</p>
                        <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                          <Star className="h-3 w-3 fill-current text-yellow-500" />
                          {selected.rating}
                        </p>
                        {facilityDistanceLabel(selected, userLocation) && (
                          <p className="mt-1 text-xs font-semibold text-primary">{facilityDistanceLabel(selected, userLocation)}</p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <a
                          href={facilityDirectionsUrl(selected, userLocation)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex flex-1 items-center justify-center gap-1 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 sm:flex-initial"
                        >
                          <Navigation className="h-4 w-4" />
                          <span className="text-xs sm:text-sm">Directions</span>
                        </a>
                        <a
                          href={facilityMapsUrl(selected)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex flex-1 items-center justify-center gap-1 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted sm:flex-initial"
                        >
                          <ExternalLink className="h-4 w-4" />
                          <span className="text-xs sm:text-sm">Maps</span>
                        </a>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4 p-4 sm:p-6">
                    <div className="grid gap-3 text-sm sm:grid-cols-2">
                      <div className="flex items-start gap-2">
                        <MapPin className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
                        <span className="break-words text-xs sm:text-sm">{selected.address}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                        <a href={`tel:${selected.phone.split('/')[0].trim()}`} className="break-all text-xs font-medium text-primary hover:underline sm:text-sm">
                          {selected.phone}
                        </a>
                      </div>
                      <div className="flex items-center gap-2 sm:col-span-2">
                        <Clock className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                        <span className="text-xs sm:text-sm">{selected.hours}</span>
                      </div>
                    </div>

                    <div>
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Services Available</p>
                      <div className="flex flex-wrap gap-1.5">
                        {selected.services.map((service) => (
                          <Badge key={service} variant="secondary" className="text-xs">
                            {service}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-lg border bg-muted/30 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-xs text-muted-foreground">
                          The main map above is focused on {selected.name}.
                        </p>
                        <a href={selected.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-xs font-medium text-primary hover:underline">
                          Source: {selected.sourceName}
                        </a>
                      </div>
                    </div>

                    <div className="flex gap-2 pt-2 sm:hidden">
                      <a
                        href={`tel:${selected.phone.split('/')[0].trim()}`}
                        className="flex flex-1 items-center justify-center gap-2 rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700"
                      >
                        <Phone className="h-4 w-4" />
                        Call Now
                      </a>
                      <a
                        href={facilityDirectionsUrl(selected, userLocation)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex flex-1 items-center justify-center gap-2 rounded-md border border-primary bg-primary/10 px-3 py-2 text-sm font-medium text-primary hover:bg-primary/20"
                      >
                        <Navigation className="h-4 w-4" />
                        Get Route
                      </a>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              <div className="mt-4 rounded-lg bg-blue-50 p-3 dark:bg-blue-950/20">
                <p className="text-xs text-blue-800 dark:text-blue-300">
                  <span className="font-semibold">Pro tip:</span> Enable location services to sort facilities by nearest distance and start direction links from your current position.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default NearbyFacilitiesPage;

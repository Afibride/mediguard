import React, { useRef, useState } from 'react';
import { Helmet } from 'react-helmet';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  Building2,
  ChevronDown,
  ChevronUp,
  Clock,
  ExternalLink,
  Locate,
  MapPin,
  Navigation,
  Phone,
  Star,
} from 'lucide-react';
import { BAMENDA_FACILITIES, facilityDirectionsUrl, facilityEmbedUrl, facilityMapsUrl } from '@/data/facilities';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

function FacilityMapEmbed({ facility }) {
  return (
    <div className="h-48 w-full overflow-hidden rounded-lg border bg-muted sm:h-56 md:h-72">
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

function FacilitiesMapOverview() {
  return (
    <div className="h-[280px] w-full overflow-hidden bg-muted sm:h-[360px] md:h-[430px]">
      <iframe
        title="Nearby health facilities in Bamenda map"
        src="https://maps.google.com/maps?q=hospitals%20and%20clinics%20in%20Bamenda%20Cameroon&output=embed&z=13&hl=en"
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
  const [expandedId, setExpandedId] = useState(null);
  const cardRefs = useRef({});

  const selected = BAMENDA_FACILITIES.find((facility) => facility.id === selectedId) || BAMENDA_FACILITIES[0];

  const requestLocation = () => {
    if (!navigator.geolocation) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => setLocating(false),
      { timeout: 8000 }
    );
  };

  const selectFacility = (facility) => {
    setSelectedId(facility.id);
    setExpandedId(null); // Close expanded card on mobile when selecting new facility
    if (window.innerWidth < 1024) {
      cardRefs.current[facility.id]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const toggleExpand = (facilityId, event) => {
    event.stopPropagation();
    setExpandedId(expandedId === facilityId ? null : facilityId);
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
        {/* Header Section */}
        <div className="border-b bg-background px-4 py-4 md:py-6">
          <div className="container mx-auto max-w-6xl">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="flex items-center gap-2 text-xl font-bold sm:text-2xl md:text-3xl">
                  <MapPin className="h-6 w-6 md:h-7 md:w-7 text-primary" />
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
                className="gap-2 w-full sm:w-auto text-sm"
                size="sm"
              >
                <Locate className={`h-4 w-4 ${locating ? 'animate-spin' : ''}`} />
                {userLocation ? '📍 Location ready' : locating ? 'Locating...' : 'Use my location'}
              </Button>
            </div>
            {userLocation && (
              <motion.p 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }} 
                className="mt-2 text-xs text-green-600 dark:text-green-400"
              >
                ✓ Directions will start from your current location
              </motion.p>
            )}
          </div>
        </div>

        <div className="container mx-auto max-w-6xl px-4 py-4 md:py-6">
          {/* Mobile: Show list first, then selected facility details */}
          {/* Desktop: Side-by-side layout */}
          <div className="flex flex-col-reverse gap-5 lg:grid lg:grid-cols-5 lg:gap-6">
            
            {/* Facilities List - Takes 2 columns on desktop, full width on mobile */}
            <div className="space-y-3 lg:col-span-2">
              <div className="mb-2 flex items-center justify-between lg:hidden">
                <h2 className="text-sm font-semibold text-muted-foreground">
                  Available Facilities ({BAMENDA_FACILITIES.length})
                </h2>
                <p className="text-xs text-muted-foreground">Tap to view details</p>
              </div>
              
              {BAMENDA_FACILITIES.map((facility, index) => {
                const isSelected = facility.id === selectedId;
                const isExpanded = expandedId === facility.id;
                return (
                  <motion.div
                    key={facility.id}
                    ref={(el) => {
                      cardRefs.current[facility.id] = el;
                    }}
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card
                      className={`cursor-pointer overflow-hidden border-2 transition-all duration-200 ${
                        isSelected ? `${facility.color} shadow-md ring-2 ring-primary/20` : 'border-border hover:border-primary/40'
                      }`}
                      onClick={() => selectFacility(facility)}
                    >
                      <div className={`p-3 sm:p-4 ${isSelected ? facility.headerBg : ''}`}>
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            {facility.emergency && (
                              <Badge variant="destructive" className="mb-1.5 px-1.5 py-0 text-[10px] sm:mb-2">
                                <AlertCircle className="mr-0.5 h-2.5 w-2.5" />
                                24/7 Emergency
                              </Badge>
                            )}
                            <p className="text-sm font-bold leading-snug sm:text-base">{facility.name}</p>
                            <p className="text-xs text-muted-foreground sm:text-sm">{facility.type}</p>
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
                          <button
                            type="button"
                            onClick={(event) => toggleExpand(facility.id, event)}
                            className="flex-shrink-0 rounded p-1 hover:bg-muted/50 transition-colors"
                            aria-label={isExpanded ? 'Collapse facility' : 'Expand facility'}
                          >
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </button>
                        </div>

                        {/* Expanded Content - Shows map and more details */}
                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-3 border-t border-border/50 pt-3"
                          >
                            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                              <p className="flex items-center gap-1 text-xs font-semibold">
                                <Star className="h-3 w-3 text-yellow-500" />
                                {facility.rating}
                              </p>
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                <span className="text-[11px]">{facility.hours}</span>
                              </div>
                            </div>
                            
                            <div className="mb-3 flex flex-wrap gap-1">
                              {facility.services.slice(0, 4).map((service) => (
                                <Badge key={service} variant="outline" className="px-1.5 py-0 text-[10px]">
                                  {service}
                                </Badge>
                              ))}
                              {facility.services.length > 4 && (
                                <Badge variant="outline" className="px-1.5 py-0 text-[10px]">
                                  +{facility.services.length - 4} more
                                </Badge>
                              )}
                            </div>
                            
                            <div className="mb-3">
                              <FacilityMapEmbed facility={facility} />
                            </div>
                            
                            <div className="flex flex-wrap gap-2">
                              <a
                                href={facilityDirectionsUrl(facility, userLocation)}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(event) => event.stopPropagation()}
                                className="flex flex-1 items-center justify-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                              >
                                <Navigation className="h-3 w-3" />
                                Directions
                              </a>
                              <a
                                href={facilityMapsUrl(facility)}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(event) => event.stopPropagation()}
                                className="flex flex-1 items-center justify-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium hover:bg-muted"
                              >
                                <ExternalLink className="h-3 w-3" />
                                Maps
                              </a>
                              <a
                                href={facility.sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(event) => event.stopPropagation()}
                                className="flex flex-1 items-center justify-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium hover:bg-muted"
                              >
                                <ExternalLink className="h-3 w-3" />
                                Source
                              </a>
                            </div>
                          </motion.div>
                        )}
                      </div>
                    </Card>
                  </motion.div>
                );
              })}
            </div>

            {/* Selected Facility Details - Takes 3 columns on desktop, shown below list on mobile */}
            <div className="lg:col-span-3">
              {/* Mobile: Quick facility chips */}
              <div className="mb-3 overflow-x-auto pb-2 lg:hidden">
                <div className="flex gap-2">
                  {BAMENDA_FACILITIES.map((facility) => (
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

              {/* Overview Map - Hidden on mobile, shown on tablet/desktop */}
              <Card className="overflow-hidden mb-4 hidden sm:block">
                <FacilitiesMapOverview />
                <div className="border-t bg-background px-3 py-2 sm:px-4 sm:py-3">
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {BAMENDA_FACILITIES.map((facility) => (
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
                    📍 Click any facility chip to view detailed information below
                  </p>
                </div>
              </Card>

              {/* Selected Facility Detailed Card */}
              <motion.div 
                key={selected.id} 
                initial={{ opacity: 0, y: 8 }} 
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className={`border-2 ${selected.color}`}>
                  <CardHeader className={`pb-3 ${selected.headerBg} p-4 sm:p-6`}>
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
                          <Star className="h-3 w-3 text-yellow-500 fill-current" />
                          {selected.rating}
                        </p>
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
                    {/* Contact & Address Information */}
                    <div className="grid gap-3 text-sm sm:grid-cols-2">
                      <div className="flex items-start gap-2">
                        <MapPin className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
                        <span className="text-xs sm:text-sm break-words">{selected.address}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                        <a href={`tel:${selected.phone.split('/')[0].trim()}`} className="text-xs sm:text-sm font-medium text-primary hover:underline break-all">
                          {selected.phone}
                        </a>
                      </div>
                      <div className="flex items-center gap-2 sm:col-span-2">
                        <Clock className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                        <span className="text-xs sm:text-sm">{selected.hours}</span>
                      </div>
                    </div>

                    {/* Services Available */}
                    <div>
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Services Available
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {selected.services.map((service) => (
                          <Badge key={service} variant="secondary" className="text-xs">
                            {service}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Map Preview */}
                    <div>
                      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Location Preview
                        </p>
                        <a
                          href={selected.sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-medium text-primary hover:underline"
                        >
                          Source: {selected.sourceName}
                        </a>
                      </div>
                      <FacilityMapEmbed facility={selected} />
                    </div>

                    {/* Quick Actions for Mobile */}
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

              {/* Helpful Tip */}
              <div className="mt-4 rounded-lg bg-blue-50 p-3 dark:bg-blue-950/20">
                <p className="text-xs text-blue-800 dark:text-blue-300">
                  💡 <span className="font-semibold">Pro tip:</span> Enable location services to get turn-by-turn directions from your current position.
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
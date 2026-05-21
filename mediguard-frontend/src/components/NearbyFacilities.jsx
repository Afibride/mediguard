import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Building2, ExternalLink, Locate, MapPin, Navigation, Phone } from 'lucide-react';
import { BAMENDA_FACILITIES, facilityDirectionsUrl, facilityMapsUrl } from '@/data/facilities';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const NearbyFacilities = ({ compact = false }) => {
  const [userLocation, setUserLocation] = useState(null);
  const [locating, setLocating] = useState(false);

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

  useEffect(() => {
    requestLocation();
  }, []);

  const displayed = compact ? BAMENDA_FACILITIES.slice(0, 4) : BAMENDA_FACILITIES;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <MapPin className="h-5 w-5 text-primary" />
              Nearby Health Facilities
            </CardTitle>
            <CardDescription className="mt-0.5">
              Sourced hospitals and clinics with maps, phone numbers, and directions
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={requestLocation} disabled={locating} className="gap-1.5 text-xs">
              <Locate className={`h-3.5 w-3.5 ${locating ? 'animate-spin' : ''}`} />
              {userLocation ? 'Location set' : locating ? 'Locating...' : 'Use my location'}
            </Button>
            <Button asChild size="sm" className="gap-1.5 text-xs">
              <Link to="/nearby-facilities">
                <MapPin className="h-3.5 w-3.5" />
                Open map
              </Link>
            </Button>
          </div>
        </div>
        {userLocation && (
          <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} className="mt-1 text-xs text-green-600 dark:text-green-400">
            Location detected. Direction links will start from your position.
          </motion.p>
        )}
      </CardHeader>

      <CardContent>
        <div className={
          compact
            ? "grid grid-flow-col grid-rows-2 auto-cols-[minmax(230px,82vw)] gap-3 overflow-x-auto pb-2 sm:grid-flow-row sm:grid-rows-none sm:grid-cols-2 sm:auto-cols-auto sm:overflow-visible sm:pb-0"
            : "grid gap-3 sm:grid-cols-2"
        }>
          {displayed.map((facility, index) => (
            <motion.div
              key={facility.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`rounded-lg border p-3 ${facility.id === 1 ? 'border-primary/40 bg-primary/5' : 'bg-muted/30'}`}
            >
              <div className="flex items-start gap-2">
                <Building2 className={`mt-0.5 h-4 w-4 flex-shrink-0 ${facility.id === 1 ? 'text-primary' : 'text-muted-foreground'}`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold leading-snug">{facility.name}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{facility.type}</p>
                  <p className="text-xs text-muted-foreground">{facility.address}</p>

                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {facility.services.slice(0, 3).map((service) => (
                      <Badge key={service} variant="outline" className="px-1.5 py-0 text-[10px]">
                        {service}
                      </Badge>
                    ))}
                    {facility.services.length > 3 && (
                      <Badge variant="outline" className="px-1.5 py-0 text-[10px] text-muted-foreground">
                        +{facility.services.length - 3}
                      </Badge>
                    )}
                  </div>

                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <a href={`tel:${facility.phone.split('/')[0].trim()}`} className="flex items-center gap-1 text-xs text-primary hover:underline">
                      <Phone className="h-3 w-3" />
                      {facility.phone}
                    </a>
                    <a
                      href={facilityMapsUrl(facility)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-blue-600 hover:underline dark:text-blue-400"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Maps
                    </a>
                    <a
                      href={facilityDirectionsUrl(facility, userLocation)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-emerald-600 hover:underline dark:text-emerald-400"
                    >
                      <Navigation className="h-3 w-3" />
                      Directions
                    </a>
                  </div>
                  <a
                    href={facility.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 block text-[11px] text-muted-foreground hover:text-primary"
                  >
                    Source: {facility.sourceName}
                  </a>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {compact && BAMENDA_FACILITIES.length > displayed.length && (
          <div className="mt-3 text-center">
            <Button asChild variant="link" size="sm" className="text-xs">
              <Link to="/nearby-facilities">View all {BAMENDA_FACILITIES.length} facilities on the map</Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default NearbyFacilities;

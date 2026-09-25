import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
} from "react-simple-maps";

interface FraudMapPoint {
  location?: string;
  risk_score?: number;
  latitude?: number;
  longitude?: number;
  lat?: number;
  lon?: number;
  lng?: number;
}

interface MapMarker {
  location: string;
  riskScore: number;
  coordinates: [number, number];
}

const cityCoordinates: Record<string, [number, number]> = {
  mumbai: [72.8777, 19.076],
  delhi: [77.1025, 28.7041],
  bengaluru: [77.5946, 12.9716],
  bangalore: [77.5946, 12.9716],
  chennai: [80.2707, 13.0827],
  hyderabad: [78.4867, 17.385],
  kolkata: [88.3639, 22.5726],
  pune: [73.8567, 18.5204],
  ahmedabad: [72.5714, 23.0225],
  jaipur: [75.7873, 26.9124],
  surat: [72.8311, 21.1702],
  lucknow: [80.9462, 26.8467],
};

const worldUrl =
  "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

function getCoordinates(point: FraudMapPoint): [number, number] | null {
  const longitude = point.longitude ?? point.lon ?? point.lng;
  const latitude = point.latitude ?? point.lat;

  if (typeof longitude === "number" && typeof latitude === "number") {
    return [longitude, latitude];
  }

  const location = point.location?.toLowerCase().trim() ?? "";

  const city = Object.keys(cityCoordinates).find((name) =>
    location.includes(name),
  );

  return city ? cityCoordinates[city] : null;
}

export const GeoFraudMap = () => {
  const [markers, setMarkers] = useState<MapMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMapData = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/analytics/fraud_map",
        );

        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }

        const payload = await response.json();

        const data: FraudMapPoint[] = Array.isArray(payload)
          ? payload
          : payload.points ?? payload.locations ?? payload.data ?? [];

        const mappedMarkers = data
          .map((point) => {
            const coordinates = getCoordinates(point);

            if (!coordinates) return null;

            return {
              location: point.location ?? "Unknown location",
              riskScore: Number(point.risk_score ?? 70),
              coordinates,
            };
          })
          .filter((marker): marker is MapMarker => marker !== null);

        setMarkers(mappedMarkers);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load map data",
        );
      } finally {
        setLoading(false);
      }
    };

    loadMapData();
  }, []);

  return (
    <Card className="border-border shadow-soft">
      <CardHeader>
        <CardTitle>Geographic Fraud Map</CardTitle>
        <CardDescription>
          Fraud-risk hotspots based on transaction locations
        </CardDescription>
      </CardHeader>

      <CardContent>
        {loading && (
          <div className="py-10 text-center text-muted-foreground">
            Loading map data...
          </div>
        )}

        {error && (
          <div className="py-10 text-center text-destructive">{error}</div>
        )}

        {!loading && !error && (
          <>
            <div className="mb-2 text-sm text-muted-foreground">
              Risk locations: {markers.length}
            </div>

            {markers.length === 0 && (
              <div className="mb-3 text-sm text-muted-foreground">
                No location data is currently available.
              </div>
            )}

            <div className="h-96 w-full overflow-hidden rounded bg-slate-950">
              <ComposableMap
                projection="geoMercator"
                projectionConfig={{
                  center: [78.9629, 22.5937],
                  scale: 900,
                }}
                width={800}
                height={420}
                style={{ width: "100%", height: "100%" }}
              >
                <ZoomableGroup center={[78.9629, 22.5937]} zoom={1}>
                  <Geographies geography={worldUrl}>
                    {({ geographies }) =>
                      geographies.map((geo) => (
                        <Geography
                          key={geo.rsmKey}
                          geography={geo}
                          fill="#172033"
                          stroke="#334155"
                          strokeWidth={0.5}
                        />
                      ))
                    }
                  </Geographies>

                  {markers.map((marker, index) => {
                    const radius = Math.max(
                      5,
                      Math.min(14, marker.riskScore / 7),
                    );

                    return (
                      <Marker
                        key={`${marker.location}-${index}`}
                        coordinates={marker.coordinates}
                      >
                        <circle
                          r={radius}
                          fill="#ef4444"
                          fillOpacity={0.75}
                          stroke="#fecaca"
                          strokeWidth={1.5}
                        />
                        <title>
                          {marker.location}: risk score {marker.riskScore}
                        </title>
                      </Marker>
                    );
                  })}
                </ZoomableGroup>
              </ComposableMap>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};



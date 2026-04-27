'use client';

import React, { useState } from 'react';
import { APIProvider, Map, AdvancedMarker, Marker, Pin, InfoWindow } from '@vis.gl/react-google-maps';
import { Pothole } from '../types';

interface MapComponentProps {
    potholes: Pothole[];
    className?: string;
}

export default function PotholeMap({ potholes, className }: MapComponentProps) {
    const [selectedPothole, setSelectedPothole] = useState<Pothole | null>(null);
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY || '';
    const mapId = process.env.NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID || '';

    // Default center (can be dynamic based on potholes)
    const defaultCenter = { lat: 0, lng: 0 };
    const center = potholes.length > 0
        ? { lat: potholes[0].latitude, lng: potholes[0].longitude }
        : defaultCenter;

    if (!apiKey) {
        return (
            <div className="flex items-center justify-center h-full bg-gray-100 rounded-lg border-2 border-dashed border-gray-300">
                <p className="text-gray-500">
                    Please add <code className="bg-gray-200 px-1 rounded">NEXT_PUBLIC_GOOGLE_MAPS_KEY</code> to your .env.local file.
                </p>
            </div>
        );
    }

    return (
        <APIProvider apiKey={apiKey}>
            <div className={`h-full w-full rounded-xl overflow-hidden shadow-lg ${className}`}>
                <Map
                    defaultCenter={defaultCenter}
                    center={center}
                    defaultZoom={15}
                    mapId={mapId || undefined}
                    gestureHandling={'greedy'}
                    disableDefaultUI={false}
                >
                    {potholes.map((pothole) => (
                        mapId ? (
                            <AdvancedMarker
                                key={pothole.id}
                                position={{ lat: pothole.latitude, lng: pothole.longitude }}
                                onClick={() => setSelectedPothole(pothole)}
                            >
                                <Pin
                                    background={
                                        pothole.severity === 'Large' ? '#EF4444' :
                                            pothole.severity === 'Medium' ? '#F59E0B' : '#EAB308'
                                    }
                                    borderColor={'#1F2937'}
                                    glyphColor={'#FFF'}
                                />
                            </AdvancedMarker>
                        ) : (
                            <Marker
                                key={pothole.id}
                                position={{ lat: pothole.latitude, lng: pothole.longitude }}
                                onClick={() => setSelectedPothole(pothole)}
                            />
                        )
                    ))}

                    {selectedPothole && (
                        <InfoWindow
                            position={{ lat: selectedPothole.latitude, lng: selectedPothole.longitude }}
                            onCloseClick={() => setSelectedPothole(null)}
                        >
                            <div className="p-2 max-w-xs">
                                <h3 className="font-bold text-gray-900">Pothole #{selectedPothole.id}</h3>
                                <p className="text-sm text-gray-600">Severity: <span className={`font-semibold ${selectedPothole.severity === 'Large' ? 'text-red-600' :
                                        selectedPothole.severity === 'Medium' ? 'text-orange-500' : 'text-yellow-600'
                                    }`}>{selectedPothole.severity}</span></p>
                                <p className="text-xs text-gray-500 mt-1">Conf: {selectedPothole.confidence}</p>
                                <p className="text-xs text-gray-400">{new Date(selectedPothole.timestamp).toLocaleString()}</p>
                            </div>
                        </InfoWindow>
                    )}
                </Map>
            </div>
        </APIProvider>
    );
}

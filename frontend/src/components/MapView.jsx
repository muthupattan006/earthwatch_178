import React, { useEffect, useRef } from 'react';
import {
  GoogleMap,
  MarkerF,
  CircleF,
  useJsApiLoader
} from '@react-google-maps/api';

import { NODES } from '../data';

const center = {
  lat: 11.38,
  lng: 76.63
};

const libraries = [];

export default function MapView({ node, onNodeSelect }) {

  const {
    isLoaded,
    loadError
  } = useJsApiLoader({
    googleMapsApiKey:
      import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '',
    libraries
  });

  const mapRef = useRef(null);

  /*
   * This is the container that will actually become fullscreen.
   * Therefore the map + popup + legend + caption all remain visible.
   */
  const mapStageRef = useRef(null);

  useEffect(() => {

    if (mapRef.current && node) {

      mapRef.current.panTo({
        lat: node.lat,
        lng: node.lng
      });

      mapRef.current.setZoom(12);
    }

  }, [node]);


  const toggleFullscreen = async () => {

  // Fullscreen the entire dashboard map stage,
  // not just the Google Maps element.
  const element =
    mapStageRef.current?.closest('.map-stage');

  if (!element) return;

  try {

    if (!document.fullscreenElement) {

      await element.requestFullscreen();

    } else {

      await document.exitFullscreen();

    }

  } catch (error) {

    console.error(
      'Fullscreen error:',
      error
    );

  }
};

  if (loadError) {

    return (
      <div className="map-error">
        Google Maps failed to load.
        Check
        <code>
          VITE_GOOGLE_MAPS_API_KEY
        </code>.
      </div>
    );

  }


  if (!isLoaded) {

    return (
      <div className="map-loading">
        Loading Earthwatch map…
      </div>
    );

  }


  return (
    <div
      ref={mapStageRef}
      className="map-fullscreen-container"
    >

      {/* Google Map */}

      <GoogleMap
  mapContainerClassName="map"
  center={center}
  zoom={10}

  onLoad={(map) => {
    mapRef.current = map;
  }}

  options={{
    mapTypeId: 'satellite',
    streetViewControl: false,
    fullscreenControl: false,
    mapTypeControl: true,

    zoomControl: true,
    scrollwheel: true,
    draggable: true,
    gestureHandling: 'greedy',

    minZoom: 3,
    maxZoom: 20
  }}
>

        {NODES.map((n) => (

          <MarkerF
            key={n.id}

            position={{
              lat: n.lat,
              lng: n.lng
            }}

            label={{
              text: n.name,
              className: 'node-label'
            }}

            onClick={() => {
              onNodeSelect(n.id);
            }}
          />

        ))}


        <CircleF
          center={{
            lat: node.lat,
            lng: node.lng
          }}

          radius={
            (node.radiusKm || 8.33) * 1000
          }

          options={{
            fillOpacity: 0.08,
            strokeOpacity: 0.55,
            clickable: false
          }}
        />

      </GoogleMap>


      {/* OUR FULLSCREEN BUTTON */}

      <button
        className="earthwatch-fullscreen-button"
        onClick={toggleFullscreen}
        title="Toggle fullscreen"
        aria-label="Toggle fullscreen"
      >
        ⛶
      </button>

    </div>
  );
}

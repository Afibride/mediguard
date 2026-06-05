import React, { useEffect, useState } from 'react';

const SEGMENTS = [
  { clip: 'inset(0 50% 50% 0)', from: { x: 0, y: -90 } },
  { clip: 'inset(50% 50% 0 0)', from: { x: -110, y: 0 } },
  { clip: 'inset(0 0 50% 50%)', from: { x: 110, y: 0 } },
  { clip: 'inset(50% 0 0 50%)', from: { x: 0, y: 90 } },
];

const APPEAR_AT = [80, 220, 360, 500];
const EXIT_AT = 1900;
const UNMOUNT_AT = 2460;

export default function SplashScreen({ onDone }) {
  const [activeSegs, setActiveSegs] = useState([]);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const timers = [
      ...APPEAR_AT.map((ms, i) =>
        setTimeout(() => setActiveSegs((prev) => [...prev, i]), ms)
      ),
      setTimeout(() => setExiting(true), EXIT_AT),
      setTimeout(() => onDone?.(), UNMOUNT_AT),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onDone]);

  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#ffffff',
        opacity: exiting ? 0 : 1,
        transition: exiting ? 'opacity 0.52s cubic-bezier(0.4,0,0.2,1)' : 'none',
        pointerEvents: exiting ? 'none' : 'auto',
      }}
    >
      <div
        style={{
          position: 'relative',
          width: 'min(360px, 78vw)',
          transform: activeSegs.length > 0 ? 'scale(1)' : 'scale(0.9)',
          transition: 'transform 0.55s cubic-bezier(0.34,1.4,0.64,1)',
        }}
      >
        <img
          src="/mediguard.png"
          alt="MediGuard"
          draggable={false}
          style={{ width: '100%', display: 'block', visibility: 'hidden' }}
        />

        {SEGMENTS.map((segment, i) => {
          const on = activeSegs.includes(i);
          return (
            <div
              key={segment.clip}
              style={{
                position: 'absolute',
                inset: 0,
                clipPath: segment.clip,
                opacity: on ? 1 : 0,
                transform: on
                  ? 'translate3d(0, 0, 0)'
                  : `translate3d(${segment.from.x}px, ${segment.from.y}px, 0)`,
                transition:
                  'opacity 0.36s ease, transform 0.68s cubic-bezier(0.16,1,0.3,1)',
                willChange: 'transform, opacity',
              }}
            >
              <img
                src="/mediguard.png"
                alt=""
                draggable={false}
                style={{ width: '100%', display: 'block' }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

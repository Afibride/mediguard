import React, { useEffect, useState } from 'react';

// Approximate left-edge % where each visual section of the logo begins.
// Segment 1 → circle icon (0–33%)
// Segment 2 → "Medi"      (33–57%)
// Segment 3 → "Guard" + tagline right half (57–100%)
const CLIPS = [
  'inset(0 67% 0 0)',    // left 33%
  'inset(0 43% 0 33%)',  // 33–57%
  'inset(0 0 0 57%)',    // 57–100%
];

// ms after mount when each segment becomes visible
const APPEAR_AT = [80, 420, 750];

// ms after mount when exit fade starts / component unmounts
const EXIT_AT   = 1800;
const UNMOUNT_AT = 2380;

export default function SplashScreen({ onDone }) {
  const [activeSegs, setActiveSegs] = useState([]);
  const [exiting,    setExiting]    = useState(false);

  useEffect(() => {
    const timers = [
      ...APPEAR_AT.map((ms, i) =>
        setTimeout(() => setActiveSegs(prev => [...prev, i]), ms)
      ),
      setTimeout(() => setExiting(true),  EXIT_AT),
      setTimeout(() => onDone?.(),        UNMOUNT_AT),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onDone]);

  return (
    <div
      aria-hidden="true"
      style={{
        position:       'fixed',
        inset:          0,
        zIndex:         9999,
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'center',
        background:     '#ffffff',
        opacity:        exiting ? 0 : 1,
        transition:     exiting
          ? 'opacity 0.52s cubic-bezier(0.4,0,0.2,1)'
          : 'none',
        pointerEvents: exiting ? 'none' : 'auto',
      }}
    >
      {/* Logo container — the hidden img sets the natural height */}
      <div
        style={{
          position:   'relative',
          width:      360,
          transform:  activeSegs.length > 0 ? 'scale(1)' : 'scale(0.88)',
          transition: 'transform 0.55s cubic-bezier(0.34,1.4,0.64,1)',
        }}
      >
        {/* Invisible reference image that sizes the container */}
        <img
          src="/mediguard.png"
          alt="MediGuard"
          draggable={false}
          style={{ width: '100%', display: 'block', visibility: 'hidden' }}
        />

        {/* Three animated clip layers stacked on top */}
        {CLIPS.map((clip, i) => {
          const on = activeSegs.includes(i);
          return (
            <div
              key={i}
              style={{
                position:   'absolute',
                inset:      0,
                clipPath:   clip,
                opacity:    on ? 1 : 0,
                transform:  on ? 'translateY(0px)' : 'translateY(18px)',
                transition: 'opacity 0.38s ease, transform 0.42s cubic-bezier(0.34,1.4,0.64,1)',
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

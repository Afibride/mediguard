/**
 * SplashScreen — MediGuard startup animation
 *
 * The logo is split into 4 quadrants that enter one at a time, slowly:
 *   1. Top-left    — drops from above
 *   2. Bottom-left — slides in from the left
 *   3. Top-right   — slides in from the right
 *   4. Bottom-right— rises from below
 *
 * After all four assemble, they hold briefly, then fly back out to their
 * original positions. The cycle repeats until the app is ready.
 */
import React, { useEffect, useState } from 'react';

// Quadrant definitions
// clip: inset(top right bottom left)
const SEGS = [
  { id: 'tl', clip: 'inset(0 50% 50% 0)',  tx: 0,   ty: -100 }, // top-left    → drops from above
  { id: 'bl', clip: 'inset(50% 50% 0 0)',   tx: -100, ty: 0   }, // bottom-left → from left
  { id: 'tr', clip: 'inset(0 0 50% 50%)',   tx: 100,  ty: 0   }, // top-right   → from right
  { id: 'br', clip: 'inset(50% 0 0 50%)',   tx: 0,   ty: 100  }, // bottom-right→ rises from below
];

// Timing constants (all in ms)
const SEG_GAP  = 580;   // delay between each piece appearing
const HOLD     = 980;   // how long the full logo stays assembled
const EXIT_DUR = 420;   // how long the exit transition takes (fly back out)
const GAP      = 360;   // dark gap before the next cycle starts
const CYCLES   = 3;     // number of full assemble → disassemble loops

// Total cycle duration
const CYCLE = SEG_GAP * (SEGS.length - 1) + HOLD + EXIT_DUR + GAP;
// = 580*3 + 980 + 420 + 360 = 1740+980+420+360 = 3500 ms

// Whole splash duration before exit begins
const SPLASH_DURATION = CYCLE * CYCLES; // 3500 * 3 = 10 500 ms

// Whether a segment is entering (true) or exiting back out (false)
// On exit we want the pieces to fly back to their original positions
// (the same as how they entered but reversed) so we just clear activeSegs.

export default function SplashScreen({ onDone }) {
  // Set of segment indices currently visible/assembled
  const [shown, setShown]     = useState(new Set());
  // True while transition is the fast "exit" direction
  const [exiting, setExiting] = useState(false);
  // True when the whole overlay is fading out
  const [leaving, setLeaving] = useState(false);

  // Lock body scroll for the entire duration of the splash so the page
  // behind cannot be scrolled on mobile (pull-to-refresh, swipe, etc.)
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    // Also lock html element for iOS Safari which ignores body overflow
    document.documentElement.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
      document.documentElement.style.overflow = '';
    };
  }, []);

  useEffect(() => {
    const timers = [];
    const add = (fn, ms) => timers.push(setTimeout(fn, ms));

    for (let c = 0; c < CYCLES; c++) {
      const base = c * CYCLE;

      // 1. Pieces appear one by one
      SEGS.forEach((_, i) => {
        add(() => {
          setExiting(false);
          setShown(prev => {
            const next = new Set(prev);
            next.add(i);
            return next;
          });
        }, base + i * SEG_GAP);
      });

      // 2. After hold: fly back out
      const flyOutAt = base + (SEGS.length - 1) * SEG_GAP + HOLD;
      add(() => {
        setExiting(true);          // switch to fast-exit transition
        setShown(new Set());       // remove all → each piece animates back to its origin
      }, flyOutAt);
    }

    // 3. Fade entire overlay out after all cycles finish
    add(() => setLeaving(true),  SPLASH_DURATION);
    add(() => onDone?.(),        SPLASH_DURATION + 540);

    return () => timers.forEach(clearTimeout);
  }, [onDone]);

  return (
    <div
      aria-hidden="true"
      onTouchMove={e => e.preventDefault()}
      style={{
        position:          'fixed',
        inset:             0,
        zIndex:            9999,
        display:           'flex',
        alignItems:        'center',
        justifyContent:    'center',
        background:        '#ffffff',
        opacity:           leaving ? 0 : 1,
        transition:        leaving ? 'opacity 0.52s cubic-bezier(0.4,0,0.2,1)' : 'none',
        pointerEvents:     leaving ? 'none' : 'auto',
        touchAction:       'none',          // blocks all touch gestures
        overscrollBehavior:'none',          // blocks pull-to-refresh on Android
        userSelect:        'none',          // prevents text selection on long-press
      }}
    >
      {/* Logo container — sized to the image, keeps all quadrant clips aligned */}
      <div style={{ position: 'relative', width: 'min(340px, 72vw)' }}>

        {/* Invisible placeholder keeps the container at the correct height */}
        <img
          src="/mediguard.png"
          alt="MediGuard"
          draggable={false}
          style={{ width: '100%', display: 'block', visibility: 'hidden' }}
        />

        {/* Each quadrant renders the full logo but reveals only its quarter */}
        {SEGS.map((seg, i) => {
          const visible = shown.has(i);
          return (
            <div
              key={seg.id}
              style={{
                position:  'absolute',
                inset:     0,
                clipPath:  seg.clip,
                opacity:   visible ? 1 : 0,
                transform: visible
                  ? 'translate3d(0,0,0)'
                  : `translate3d(${seg.tx}px,${seg.ty}px,0)`,
                transition: exiting
                  // Fast, tight exit — pieces snap back to their origins
                  ? `opacity ${EXIT_DUR * 0.9}ms ease-in,
                     transform ${EXIT_DUR}ms cubic-bezier(0.4,0,0.8,0.2)`
                  // Slow, springy entrance
                  : `opacity 0.38s ease,
                     transform 0.82s cubic-bezier(0.16,1,0.3,1)`,
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

      {/* Subtle pulsing tagline while assembling */}
      <div
        style={{
          position:   'absolute',
          bottom:     '12%',
          left:       0,
          right:      0,
          textAlign:  'center',
          fontSize:   '0.78rem',
          fontWeight: 600,
          letterSpacing: '0.12em',
          color:      '#0ea5e9',
          opacity:    leaving ? 0 : 0.7,
          transition: 'opacity 0.4s ease',
          fontFamily: 'system-ui, sans-serif',
          userSelect: 'none',
          animation:  'mg-pulse 1.8s ease-in-out infinite',
        }}
      >
        Smart Diagnosis · Fast Care · Safe Health
      </div>

      {/* Keyframe for tagline pulse — injected once */}
      <style>{`
        @keyframes mg-pulse {
          0%, 100% { opacity: 0.45; }
          50%       { opacity: 0.85; }
        }
      `}</style>
    </div>
  );
}

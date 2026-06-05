/**
 * MediGuard startup animation.
 *
 * The logo is split into 4 quadrants:
 * top-left drops from above, bottom-left enters from the left,
 * top-right enters from the right, and bottom-right rises from below.
 * It loops until the app reports that startup checks are ready.
 */
import React, { useEffect, useRef, useState } from 'react';

const SEGS = [
  { id: 'tl', clip: 'inset(0 50% 50% 0)', tx: 0, ty: -100 },
  { id: 'bl', clip: 'inset(50% 50% 0 0)', tx: -100, ty: 0 },
  { id: 'tr', clip: 'inset(0 0 50% 50%)', tx: 100, ty: 0 },
  { id: 'br', clip: 'inset(50% 0 0 50%)', tx: 0, ty: 100 },
];

const SEG_GAP = 580;
const HOLD = 980;
const EXIT_DUR = 420;
const GAP = 360;

export default function SplashScreen({ ready = false, onDone }) {
  const [shown, setShown] = useState(new Set());
  const [exiting, setExiting] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const readyRef = useRef(ready);

  useEffect(() => {
    readyRef.current = ready;
  }, [ready]);

  useEffect(() => {
    const prevBody = document.body.style.overflow;
    const prevHtml = document.documentElement.style.overflow;
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prevBody;
      document.documentElement.style.overflow = prevHtml;
    };
  }, []);

  useEffect(() => {
    const timers = [];
    const add = (fn, ms) => timers.push(window.setTimeout(fn, ms));
    let stopped = false;

    const finish = () => {
      setLeaving(true);
      add(() => onDone?.(), 540);
    };

    const runCycle = () => {
      if (stopped) return;
      setExiting(false);
      setShown(new Set());

      SEGS.forEach((_, i) => {
        add(() => {
          if (stopped) return;
          setExiting(false);
          setShown(prev => {
            const next = new Set(prev);
            next.add(i);
            return next;
          });
        }, i * SEG_GAP);
      });

      const flyOutAt = (SEGS.length - 1) * SEG_GAP + HOLD;
      add(() => {
        if (stopped) return;
        setExiting(true);
        setShown(new Set());
      }, flyOutAt);

      add(() => {
        if (stopped) return;
        if (readyRef.current) finish();
        else runCycle();
      }, flyOutAt + EXIT_DUR + GAP);
    };

    runCycle();

    return () => {
      stopped = true;
      timers.forEach(window.clearTimeout);
    };
  }, [onDone]);

  return (
    <div
      aria-hidden="true"
      onTouchMove={e => e.preventDefault()}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#ffffff',
        opacity: leaving ? 0 : 1,
        transition: leaving ? 'opacity 0.52s cubic-bezier(0.4,0,0.2,1)' : 'none',
        pointerEvents: leaving ? 'none' : 'auto',
        touchAction: 'none',
        overscrollBehavior: 'none',
        userSelect: 'none',
      }}
    >
      <div style={{ position: 'relative', width: 'min(340px, 72vw)' }}>
        <img
          src="/mediguard.png"
          alt="MediGuard"
          draggable={false}
          style={{ width: '100%', display: 'block', visibility: 'hidden' }}
        />

        {SEGS.map((seg, i) => {
          const visible = shown.has(i);
          return (
            <div
              key={seg.id}
              style={{
                position: 'absolute',
                inset: 0,
                clipPath: seg.clip,
                opacity: visible ? 1 : 0,
                transform: visible
                  ? 'translate3d(0,0,0)'
                  : `translate3d(${seg.tx}px,${seg.ty}px,0)`,
                transition: exiting
                  ? `opacity ${EXIT_DUR * 0.9}ms ease-in,
                     transform ${EXIT_DUR}ms cubic-bezier(0.4,0,0.8,0.2)`
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

      <div
        style={{
          position: 'absolute',
          bottom: '12%',
          left: 0,
          right: 0,
          textAlign: 'center',
          fontSize: '0.78rem',
          fontWeight: 600,
          letterSpacing: '0.12em',
          color: '#0ea5e9',
          opacity: leaving ? 0 : 0.7,
          transition: 'opacity 0.4s ease',
          fontFamily: 'system-ui, sans-serif',
          userSelect: 'none',
          animation: 'mg-pulse 1.8s ease-in-out infinite',
        }}
      >
        Smart Diagnosis - Fast Care - Safe Health
      </div>

      <style>{`
        @keyframes mg-pulse {
          0%, 100% { opacity: 0.45; }
          50% { opacity: 0.85; }
        }
      `}</style>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { Crosshair, ShieldCheck, Wifi, Radio } from 'lucide-react';

const statusSteps = [
  { text: 'Connecting to RTSP camera feed...', pct: 14 },
  { text: 'Loading YOLOv8 AI Inference Core...', pct: 38 },
  { text: 'Calibrating Virtual Tripwire mesh...', pct: 64 },
  { text: 'Syncing Sector 04 telemetry...', pct: 88 },
  { text: 'Perimeter Defense Grid Online.', pct: 100 }
];

export default function TacticalSplashScreen({ onComplete }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [clock, setClock] = useState('00:00:00 UTC');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setClock(now.toISOString().substring(11, 19) + ' UTC');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => {
        if (prev < statusSteps.length - 1) {
          return prev + 1;
        } else {
          clearInterval(interval);
          setTimeout(() => {
            if (onComplete) onComplete();
          }, 700);
          return prev;
        }
      });
    }, 700);
    return () => clearInterval(interval);
  }, [onComplete]);

  const currentStep = statusSteps[stepIndex];

  return (
    <div className="relative w-full h-screen bg-[#0B1120] overflow-hidden flex flex-col justify-between items-center px-6 py-8 select-none text-slate-200">
      {/* Background Military Tactical Grid */}
      <div className="absolute inset-0 bg-grid-tactical pointer-events-none"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.08)_0%,transparent_70%)] pointer-events-none"></div>

      {/* Top Tactical Header */}
      <div className="w-full max-w-6xl flex justify-between items-center text-xs font-mono text-slate-500 tracking-wider z-10">
        <div className="flex items-center space-x-3">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-semibold bg-blue-950/60 text-blue-400 border border-blue-800/40">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse mr-1.5"></span>
            SYS-ACTIVE
          </span>
          <span className="hidden sm:inline text-slate-400">SECTOR 04-NORTH // SECURE FEED</span>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-slate-300 font-mono font-semibold">{clock}</span>
          <span className="hidden md:inline text-slate-500">PROTOCOL: AES-256-GCM</span>
        </div>
      </div>

      {/* Center Radar Scanner & Title */}
      <div className="flex flex-col items-center justify-center my-auto w-full max-w-md relative z-10">
        {/* Targeting corner brackets */}
        <div className="absolute -top-6 -left-6 w-4 h-4 border-t-2 border-l-2 border-blue-500/60"></div>
        <div className="absolute -top-6 -right-6 w-4 h-4 border-t-2 border-r-2 border-blue-500/60"></div>
        <div className="absolute -bottom-6 -left-6 w-4 h-4 border-b-2 border-l-2 border-blue-500/60"></div>
        <div className="absolute -bottom-6 -right-6 w-4 h-4 border-b-2 border-r-2 border-blue-500/60"></div>

        {/* Logo & Subtitle */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center space-x-3 mb-2">
            <div className="w-9 h-9 rounded-lg border border-blue-500/40 bg-blue-950/40 flex items-center justify-center text-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
              <Crosshair className="w-5 h-5 text-blue-400" />
            </div>
            <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-white uppercase font-sans">
              Border<span className="text-blue-500 font-light">Vision</span>
            </h1>
          </div>
          <p className="text-xs sm:text-sm font-mono tracking-widest uppercase text-slate-400 font-medium">
            AI Eyes on Existing CCTV
          </p>
        </div>

        {/* Animated Concentric Radar Scanner */}
        <div className="relative w-52 h-52 flex items-center justify-center mb-8">
          <div className="absolute inset-0 rounded-full border border-blue-900/30"></div>
          <div className="absolute inset-4 rounded-full border border-blue-800/40"></div>
          <div className="absolute inset-10 rounded-full border border-blue-600/30"></div>
          <div className="absolute inset-16 rounded-full border border-blue-500/40 border-dashed"></div>

          {/* Crosshair lines */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
            <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-blue-500 to-transparent"></div>
          </div>
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
            <div className="h-full w-[1px] bg-gradient-to-b from-transparent via-blue-500 to-transparent"></div>
          </div>

          {/* Pulsing rings */}
          <div className="absolute w-28 h-28 rounded-full border border-blue-500/60 pulse-ring-1"></div>
          <div className="absolute w-28 h-28 rounded-full border border-blue-400/50 pulse-ring-2"></div>
          <div className="absolute w-28 h-28 rounded-full border border-blue-300/40 pulse-ring-3"></div>

          {/* Rotating radar sweep */}
          <svg className="absolute inset-0 w-full h-full radar-sweep pointer-events-none" viewBox="0 0 200 200">
            <defs>
              <linearGradient id="sweepGrad" x1="100" y1="100" x2="200" y2="100" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0" />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.4" />
              </linearGradient>
            </defs>
            <path d="M 100 100 L 200 100 A 100 100 0 0 0 170.7 29.3 Z" fill="url(#sweepGrad)" />
            <line x1="100" y1="100" x2="200" y2="100" stroke="#3B82F6" strokeWidth="1.5" strokeOpacity="0.9" />
          </svg>

          {/* Thermal Target Blips */}
          <div className="absolute top-12 right-14 w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_10px_#3b82f6] animate-pulse"></div>
          <div className="absolute bottom-16 left-12 w-1.5 h-1.5 rounded-full bg-slate-400 opacity-60"></div>

          {/* Center core */}
          <div className="relative z-10 w-8 h-8 rounded-full bg-[#0B1120] border border-blue-400 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.6)]">
            <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-ping"></div>
            <div className="absolute w-2 h-2 rounded-full bg-blue-400"></div>
          </div>
        </div>

        {/* Progress & Telemetry */}
        <div className="w-full space-y-3">
          <div className="flex items-center justify-between font-mono text-xs text-slate-300">
            <div className="flex items-center space-x-2">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
              <span className="font-medium text-slate-200">{currentStep.text}</span>
            </div>
            <span className="text-blue-400 font-bold font-mono">{currentStep.pct}%</span>
          </div>

          <div className="w-full h-1.5 bg-slate-800/80 rounded-full overflow-hidden border border-slate-700/40 relative">
            <div
              className="h-full bg-blue-500 transition-all duration-500 ease-out shadow-[0_0_10px_#3B82F6]"
              style={{ width: `${currentStep.pct}%` }}
            ></div>
          </div>

          <div className="flex justify-between items-center pt-1 font-mono text-[10px] text-slate-400">
            <div className="flex space-x-1.5">
              {statusSteps.map((_, i) => (
                <div
                  key={i}
                  className={`w-3 h-1 rounded-sm transition-colors duration-300 ${
                    i <= stepIndex ? 'bg-blue-500' : 'bg-slate-700'
                  }`}
                ></div>
              ))}
            </div>
            <span className="tracking-widest">ENCRYPTED STREAM // RTSP 4K</span>
          </div>
        </div>

        {/* Direct Enter Button */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={onComplete}
            className="px-5 py-2 bg-blue-600/80 hover:bg-blue-500 text-white font-mono text-xs font-semibold rounded-md border border-blue-400/40 shadow-[0_0_15px_rgba(59,130,246,0.4)] transition flex items-center gap-2 group"
          >
            <ShieldCheck className="w-4 h-4 text-blue-200 group-hover:scale-110 transition-transform" />
            ENTER COMMAND CENTER
          </button>
        </div>
      </div>

      {/* Footer Info */}
      <div className="w-full max-w-6xl flex justify-between items-center text-[10px] font-mono text-slate-400 border-t border-slate-800/60 pt-4 z-10">
        <div className="flex items-center space-x-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span>NOC BUILD 2.4-TACTICAL</span>
        </div>
        <div className="flex items-center space-x-4">
          <span>LATENCY: 18ms</span>
          <span>EDGE AI ACCELERATED</span>
        </div>
      </div>
    </div>
  );
}

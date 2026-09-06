import React, { useState } from 'react';
import { 
  X, AlertTriangle, Shield, Radio, Navigation, Clock, 
  CheckCircle2, Users, Send, MapPin, Zap, Crosshair, Eye
} from 'lucide-react';

export default function AlertDispatchModal({ alert, onClose, onDispatch }) {
  const [selectedUnit, setSelectedUnit] = useState('alpha');
  const [isDispatching, setIsDispatching] = useState(false);
  const [dispatched, setDispatched] = useState(false);

  if (!alert) return null;

  const handleDispatch = () => {
    setIsDispatching(true);
    setTimeout(() => {
      setIsDispatching(false);
      setDispatched(true);
      if (onDispatch) onDispatch(selectedUnit);
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fadeIn">
      {/* Modal Card */}
      <div className="bg-[#131E35] border border-slate-700/90 rounded-xl shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden text-slate-100">
        
        {/* Modal Header */}
        <div className="px-6 py-4 bg-[#0F172A] border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded bg-red-500/20 border border-red-500/50 flex items-center justify-center text-red-400">
              <AlertTriangle className="w-5 h-5 text-red-500 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-wider uppercase text-white font-mono">
                  {alert.title || 'BREACH INCIDENT REPORT'}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800/80 font-bold">
                  PRIORITY 1 // CRITICAL
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                EVENT ID: #{alert.id || 'EV-49201'} · SECTOR 04-NORTH
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left: Snapshot & AI Classification */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            <div className="relative rounded-lg overflow-hidden border border-slate-700 bg-black aspect-video flex items-center justify-center">
              <img
                src={alert.image || "https://lh3.googleusercontent.com/aida-public/AB6AXuCumfyk0VITQQhCi4VRbB6Ra_80yobpm3tx3tRvbC5If2U4QFwJXR2LNXSPycdk9z8QdkUGw0DjIoVypH4kusiVPBqS8dCzJU0VRvNgFUZ8uitNB-A5SXs89tdvg4H6dbTED0v8MHKzRiucen7u8uZhhLvhLykP3dauxH3kK2gy5wS0pOip7XaKooLhHhE0FKAx5R0WfP5MQArkHR-ER4aVNSl2bubJSmeHaKUoGdkbm85tRkrsLzM"}
                alt="Breach Snapshot"
                className="w-full h-full object-cover"
              />
              {/* Tripwire & Bounding Overlays */}
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute left-0 right-0 top-[60%] h-[2px] tripwire-line"></div>
                <div className="absolute right-[24%] top-[50%] w-[90px] h-[170px] border-2 border-red-500 bbox-person bg-red-500/10">
                  <div className="absolute -top-6 left-0 bg-red-600 text-white font-mono text-[10px] px-1.5 py-0.5 font-bold">
                    Target #1 94%
                  </div>
                </div>
              </div>

              {/* Timestamp Stamp */}
              <div className="absolute bottom-3 left-3 px-2 py-1 bg-black/80 font-mono text-[11px] text-red-400 rounded border border-red-500/40">
                REC: 2026-03-29 06:24:12 UTC · 4K RTSP
              </div>
            </div>

            {/* AI Diagnostics Box */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-4 space-y-2 font-mono text-xs">
              <div className="text-slate-400 flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-blue-400" />
                  AI INFERENCE METRICS
                </span>
                <span className="text-emerald-400">YOLOv8x-TACTICAL</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-300 pt-1">
                <div>
                  <span className="text-slate-400">Class:</span> <span className="text-white font-bold">Person (Armed/Suspicious)</span>
                </div>
                <div>
                  <span className="text-slate-400">Confidence:</span> <span className="text-emerald-400 font-bold">94.2%</span>
                </div>
                <div>
                  <span className="text-slate-400">Velocity:</span> 1.4 m/s (Inbound)
                </div>
                <div>
                  <span className="text-slate-400">Tripwire:</span> <span className="text-red-400 font-bold">ZONE 4A VIOLATED</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: GPS Telemetry & QRT Dispatch Action */}
          <div className="lg:col-span-5 flex flex-col justify-between gap-4">
            
            {/* GPS & Sector Coordinates */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-lg p-4 font-mono text-xs space-y-2.5">
              <div className="flex items-center gap-2 text-slate-300 font-semibold border-b border-slate-800 pb-2">
                <MapPin className="w-4 h-4 text-amber-400" />
                <span>LOCATION TELEMETRY</span>
              </div>
              <div className="space-y-1 text-slate-400">
                <div className="flex justify-between">
                  <span>Sector:</span>
                  <span className="text-white font-semibold">Sector 04-North (Forward Base)</span>
                </div>
                <div className="flex justify-between">
                  <span>Coordinates:</span>
                  <span className="text-blue-400 font-semibold">31.4392° N, 74.3298° E</span>
                </div>
                <div className="flex justify-between">
                  <span>Perimeter Distance:</span>
                  <span className="text-amber-400 font-semibold">42 meters inside zone</span>
                </div>
                <div className="flex justify-between">
                  <span>Radio Band:</span>
                  <span className="text-slate-300">VHF 142.850 MHz</span>
                </div>
              </div>
            </div>

            {/* QRT Unit Selection */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-bold text-slate-300 uppercase flex items-center gap-2">
                <Users className="w-3.5 h-3.5 text-blue-400" />
                SELECT QUICK REACTION TEAM (QRT)
              </label>

              <div className="space-y-2">
                <div
                  onClick={() => setSelectedUnit('alpha')}
                  className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                    selectedUnit === 'alpha'
                      ? 'bg-blue-600/20 border-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.3)]'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></div>
                    <div>
                      <div className="font-mono text-xs font-bold text-white">QRT ALPHA (STATION 4)</div>
                      <div className="text-[11px] text-slate-400">4 Personnel · Heavy Armored Vehicle</div>
                    </div>
                  </div>
                  <span className="text-xs font-mono font-semibold text-emerald-400">ETA 2m</span>
                </div>

                <div
                  onClick={() => setSelectedUnit('bravo')}
                  className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                    selectedUnit === 'bravo'
                      ? 'bg-blue-600/20 border-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.3)]'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400"></div>
                    <div>
                      <div className="font-mono text-xs font-bold text-white">QRT BRAVO (STATION 2)</div>
                      <div className="text-[11px] text-slate-400">4 Personnel · Tactical Patrol</div>
                    </div>
                  </div>
                  <span className="text-xs font-mono font-semibold text-amber-400">ETA 5m</span>
                </div>

                <div
                  onClick={() => setSelectedUnit('drone')}
                  className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                    selectedUnit === 'drone'
                      ? 'bg-blue-600/20 border-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.3)]'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping"></div>
                    <div>
                      <div className="font-mono text-xs font-bold text-white">UAV DRONE INTERCEPTOR</div>
                      <div className="text-[11px] text-slate-400">Thermal FLIR · Spotlight Enabled</div>
                    </div>
                  </div>
                  <span className="text-xs font-mono font-semibold text-blue-400">ETA 45s</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-2">
              {dispatched ? (
                <div className="p-3 bg-emerald-950/80 border border-emerald-500 text-emerald-300 rounded-lg flex items-center justify-center gap-2 font-mono text-xs font-bold animate-bounce">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  QRT DISPATCHED & ACKNOWLEDGED // EN ROUTE
                </div>
              ) : (
                <button
                  onClick={handleDispatch}
                  disabled={isDispatching}
                  className="w-full py-3 bg-red-600 hover:bg-red-500 active:scale-[0.99] text-white font-mono font-bold text-xs uppercase tracking-wider rounded-lg border border-red-400 shadow-[0_0_20px_rgba(239,68,68,0.5)] transition flex items-center justify-center gap-2"
                >
                  {isDispatching ? (
                    <>
                      <Radio className="w-4 h-4 animate-spin text-white" />
                      TRANSMITTING DISPATCH ORDERS...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 text-white" />
                      CONFIRM DISPATCH QRT TO SECTOR 04
                    </>
                  )}
                </button>
              )}
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}

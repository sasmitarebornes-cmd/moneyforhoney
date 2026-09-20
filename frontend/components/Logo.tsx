import React from "react";

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
  showTagline?: boolean;
}

export const Logo: React.FC<LogoProps> = ({
  className = "",
  size = "md",
  showTagline = true,
}) => {
  // Dimension scales
  const dimensions = {
    sm: { icon: 38, title: "text-base", tagline: "text-[9px]" },
    md: { icon: 48, title: "text-xl", tagline: "text-[11px]" },
    lg: { icon: 60, title: "text-2xl", tagline: "text-xs" },
    xl: { icon: 76, title: "text-3xl", tagline: "text-sm" },
  }[size];

  return (
    <div
      id="money-for-honey-brand"
      className={`flex items-center gap-3.5 select-none group cursor-pointer ${className}`}
    >
      {/* Dynamic Radar Scanner + Quantum Honeycomb Nexus Icon */}
      <div className="relative shrink-0 flex items-center justify-center">
        {/* Multilayer Radial Ambient Glow Pulsing in the Background */}
        <div className="absolute inset-0 bg-gradient-to-tr from-amber-500/25 via-yellow-400/20 to-emerald-400/25 rounded-2xl blur-lg -z-10 animate-pulse duration-1000" />
        <div className="absolute -inset-1 bg-gradient-to-r from-amber-500/10 via-emerald-500/20 to-cyan-500/10 rounded-full blur-md -z-10 animate-ping opacity-25 duration-1000" />

        <svg
          width={dimensions.icon}
          height={dimensions.icon}
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="drop-shadow-[0_0_16px_rgba(245,158,11,0.45)] transition-transform duration-300 group-hover:scale-105"
        >
          <defs>
            {/* Hexagon Shield Metallic Gold Border */}
            <linearGradient id="mfhGoldMetallic" x1="10" y1="10" x2="90" y2="90" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFFBEB" />
              <stop offset="25%" stopColor="#FDE047" />
              <stop offset="60%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#B45309" />
            </linearGradient>

            {/* Futuristic Deep Space Canvas Fill */}
            <radialGradient id="mfhDarkNexus" cx="50" cy="50" r="45" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#0B132B" />
              <stop offset="65%" stopColor="#050811" />
              <stop offset="100%" stopColor="#020408" />
            </radialGradient>

            {/* Radar Beam Conical Sweep Gradient */}
            <linearGradient id="mfhRadarBeamGrad" x1="50" y1="50" x2="88" y2="28" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.0" />
              <stop offset="70%" stopColor="#10B981" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#34D399" stopOpacity="0.85" />
            </linearGradient>

            {/* High-Growth Profit Surge Line */}
            <linearGradient id="mfhSurgeGrad" x1="20" y1="78" x2="85" y2="18" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#F59E0B" />
              <stop offset="50%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#06B6D4" />
            </linearGradient>

            {/* Quantum Core Amber Glow */}
            <radialGradient id="mfhCoreGlow" cx="50" cy="50" r="8" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="40%" stopColor="#FDE047" />
              <stop offset="80%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#D97706" />
            </radialGradient>

            {/* Glow Filter */}
            <filter id="mfhIntenseGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="mfhRadarPuddle" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Hexagonal Outer Chamber Wall */}
          <polygon
            points="50,6 88,28 88,72 50,94 12,72 12,28"
            stroke="url(#mfhGoldMetallic)"
            strokeWidth="2.5"
            fill="url(#mfhDarkNexus)"
            strokeLinejoin="round"
          />

          {/* Precision Corner Tech Notches */}
          <circle cx="50" cy="6" r="2" fill="#FDE047" />
          <circle cx="88" cy="28" r="2" fill="#F59E0B" />
          <circle cx="88" cy="72" r="2" fill="#F59E0B" />
          <circle cx="50" cy="94" r="2" fill="#D97706" />
          <circle cx="12" cy="72" r="2" fill="#F59E0B" />
          <circle cx="12" cy="28" r="2" fill="#F59E0B" />

          {/* Concentric Sonar Radar Circles (Opportunity Radar Grid) */}
          <circle cx="50" cy="50" r="34" stroke="#10B981" strokeWidth="0.8" strokeOpacity="0.22" strokeDasharray="3 3" />
          <circle cx="50" cy="50" r="23" stroke="#F59E0B" strokeWidth="0.9" strokeOpacity="0.28" strokeDasharray="2 2" />
          <circle cx="50" cy="50" r="13" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.35" />

          {/* Radar Reticle Crosshair Calibration Axes */}
          <line x1="50" y1="16" x2="50" y2="84" stroke="#34D399" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="4 4" />
          <line x1="16" y1="50" x2="84" y2="50" stroke="#34D399" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="4 4" />

          {/* SWEEPING RADAR BEAM (Rotating 360° to scan for high-yield alpha opportunities) */}
          <g className="origin-[50px_50px] animate-[spin_4s_linear_infinite]">
            {/* Cone of radar illumination */}
            <path
              d="M50 50 L84 28 A34 34 0 0 1 84 72 Z"
              fill="url(#mfhRadarBeamGrad)"
              opacity="0.65"
              filter="url(#mfhRadarPuddle)"
            />
            {/* Leading scanning laser beam */}
            <line
              x1="50"
              y1="50"
              x2="84"
              y2="28"
              stroke="#34D399"
              strokeWidth="2"
              strokeLinecap="round"
              filter="url(#mfhIntenseGlow)"
            />
            {/* Detected alpha target blip at the scanning edge */}
            <circle cx="78" cy="32" r="3.2" fill="#34D399" className="animate-ping" opacity="0.8" />
            <circle cx="78" cy="32" r="2" fill="#FFFFFF" />
          </g>

          {/* Secondary Counter-Rotating Honeycomb Ring */}
          <g className="origin-[50px_50px] animate-[spin_16s_linear_infinite_reverse] opacity-40">
            <polygon
              points="50,22 74,36 74,64 50,78 26,64 26,36"
              stroke="url(#mfhGoldMetallic)"
              strokeWidth="1.2"
              strokeDasharray="4 6"
              fill="none"
            />
          </g>

          {/* Inner Golden Honeycomb Synthesis Cell */}
          <polygon
            points="50,33 65,41.5 65,58.5 50,67 35,58.5 35,41.5"
            stroke="url(#mfhGoldMetallic)"
            strokeWidth="1.6"
            fill="#090E17"
            fillOpacity="0.85"
            strokeLinejoin="round"
          />

          {/* Exponential Alpha Surge Trajectory (Financial breakout vector) */}
          <path
            d="M24 68 Q 42 62, 52 46 T 78 24"
            stroke="url(#mfhSurgeGrad)"
            strokeWidth="3.2"
            strokeLinecap="round"
            filter="url(#mfhIntenseGlow)"
          />

          {/* Breakthrough Apex Alpha Beacon */}
          <circle cx="78" cy="24" r="4.5" fill="#06B6D4" filter="url(#mfhIntenseGlow)" />
          <circle cx="78" cy="24" r="2.2" fill="#FFFFFF" />

          {/* Opportunity Signal Targets (Detected arbitrage & confluence blips) */}
          <circle cx="32" cy="40" r="1.8" fill="#F59E0B" className="animate-ping duration-1000" />
          <circle cx="68" cy="62" r="2.2" fill="#10B981" className="animate-pulse duration-700" />
          <circle cx="68" cy="62" r="1" fill="#FFFFFF" />

          {/* Quantum Golden Honey Core (Pulsing Nuclear Wealth Seed) */}
          <circle cx="50" cy="50" r="6" fill="url(#mfhCoreGlow)" className="animate-pulse" filter="url(#mfhIntenseGlow)" />
          <circle cx="50" cy="50" r="2.5" fill="#FFFFFF" />
        </svg>
      </div>

      {/* Brand Title & Cute Hanging Hive + Honey Bee Mascot Animation */}
      <div className="flex flex-col justify-center">
        <div className="flex items-center gap-2.5">
          <span
            className={`font-black tracking-wider uppercase bg-gradient-to-r from-amber-300 via-yellow-100 to-amber-500 bg-clip-text text-transparent font-sans drop-shadow-sm ${dimensions.title}`}
          >
            MONEY For HONEY
          </span>

          {/* Cute Animated Hanging Beehive & Happy Honey Bee Badge */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-gradient-to-r from-amber-500/15 via-yellow-500/20 to-amber-400/15 border border-amber-400/35 shadow-[0_0_12px_rgba(245,158,11,0.25)] group-hover:border-amber-400/60 transition-all duration-300"
            title="Honey Bee & Hanging Hive — Gathering Alpha Nectar"
          >
            {/* Cute Hanging Beehive SVG with Gentle Pendulum Sway */}
            <div className="relative w-5 h-7 flex items-center justify-center">
              <svg
                viewBox="0 0 24 32"
                className="w-5 h-7 overflow-visible origin-top animate-[swing_3s_ease-in-out_infinite]"
              >
                <defs>
                  <linearGradient id="hiveGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FDE047" />
                    <stop offset="40%" stopColor="#F59E0B" />
                    <stop offset="100%" stopColor="#B45309" />
                  </linearGradient>
                  <linearGradient id="honeyDropGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FEF08A" />
                    <stop offset="100%" stopColor="#F59E0B" />
                  </linearGradient>
                </defs>

                {/* Hanging Branch & Twig String */}
                <path d="M2 2 Q 12 5, 22 2" stroke="#854D0E" strokeWidth="1.8" strokeLinecap="round" />
                <path d="M12 3.5 L12 7" stroke="#78350F" strokeWidth="1.2" strokeLinecap="round" />
                {/* Tiny Green Leaf */}
                <path d="M14 3 Q 18 1, 19 4 Q 16 6, 14 3" fill="#22C55E" />

                {/* Hanging Hive - Top Tier */}
                <ellipse cx="12" cy="9" rx="4.5" ry="2.2" fill="url(#hiveGrad)" stroke="#B45309" strokeWidth="0.6" />
                {/* Hive - Middle Tier */}
                <ellipse cx="12" cy="13" rx="6.5" ry="3" fill="url(#hiveGrad)" stroke="#B45309" strokeWidth="0.6" />
                {/* Hive - Lower Tier */}
                <ellipse cx="12" cy="18" rx="8" ry="3.6" fill="url(#hiveGrad)" stroke="#B45309" strokeWidth="0.6" />
                {/* Hive - Base Tier */}
                <ellipse cx="12" cy="23" rx="5.5" ry="2.8" fill="url(#hiveGrad)" stroke="#B45309" strokeWidth="0.6" />

                {/* Hive Doorway (Cozy Entrance) */}
                <ellipse cx="12" cy="18.5" rx="2.4" ry="2.8" fill="#451A03" />
                <ellipse cx="12" cy="19.2" rx="1.6" ry="1.2" fill="#D97706" opacity="0.8" />

                {/* Delicious Honey Droplet dripping from base */}
                <path
                  d="M12 25 C10.8 25, 10.5 27, 12 29.5 C13.5 27, 13.2 25, 12 25 Z"
                  fill="url(#honeyDropGrad)"
                  className="animate-pulse"
                />
              </svg>
            </div>

            {/* Cute Little Flying Honey Bee with Fluttering Wings */}
            <div className="relative w-6 h-6 flex items-center justify-center">
              <svg
                viewBox="0 0 32 32"
                className="w-6 h-6 overflow-visible animate-[bounce_2s_ease-in-out_infinite]"
              >
                <defs>
                  <linearGradient id="beeBody" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#FEF08A" />
                    <stop offset="50%" stopColor="#FBBF24" />
                    <stop offset="100%" stopColor="#F59E0B" />
                  </linearGradient>
                  <linearGradient id="wingGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#E0F2FE" stopOpacity="0.95" />
                    <stop offset="100%" stopColor="#BAE6FD" stopOpacity="0.4" />
                  </linearGradient>
                </defs>

                {/* Left Translucent Shimmering Wing */}
                <ellipse
                  cx="12"
                  cy="9"
                  rx="4.5"
                  ry="7"
                  transform="rotate(-28 12 9)"
                  fill="url(#wingGrad)"
                  stroke="#38BDF8"
                  strokeWidth="0.6"
                  className="origin-[16px_16px] animate-[pulse_0.4s_ease-in-out_infinite]"
                />
                {/* Right Translucent Wing */}
                <ellipse
                  cx="20"
                  cy="9"
                  rx="4.5"
                  ry="7"
                  transform="rotate(28 20 9)"
                  fill="url(#wingGrad)"
                  stroke="#38BDF8"
                  strokeWidth="0.6"
                  className="origin-[16px_16px] animate-[pulse_0.4s_ease-in-out_infinite]"
                />

                {/* Cute Chubby Bee Body */}
                <ellipse cx="16" cy="17" rx="8" ry="6.2" fill="url(#beeBody)" stroke="#78350F" strokeWidth="0.7" />

                {/* Black Cuddly Fur Stripes */}
                <path d="M13.5 11.2 Q 13 17, 13.5 22.8" stroke="#1F2937" strokeWidth="2.2" strokeLinecap="round" />
                <path d="M17.5 11.2 Q 17 17, 17.5 22.8" stroke="#1F2937" strokeWidth="2.2" strokeLinecap="round" />

                {/* Tiny Sweet Stinger */}
                <path d="M7.8 17 L5.5 17" stroke="#1F2937" strokeWidth="1.2" strokeLinecap="round" />

                {/* Big Cute Chibi Eye with Sparkle Highlight */}
                <circle cx="21" cy="15.5" r="2" fill="#0F172A" />
                <circle cx="21.6" cy="14.9" r="0.8" fill="#FFFFFF" />

                {/* Rosy Blush Cheek */}
                <circle cx="20.5" cy="18.2" r="1.2" fill="#F43F5E" opacity="0.6" />

                {/* Cute Antennae */}
                <path d="M22 12 Q 24 9, 26 10" stroke="#1F2937" strokeWidth="0.9" strokeLinecap="round" fill="none" />
                <circle cx="26" cy="10" r="0.9" fill="#F59E0B" />
                <path d="M20 11.5 Q 21 8, 23 8.5" stroke="#1F2937" strokeWidth="0.9" strokeLinecap="round" fill="none" />
                <circle cx="23" cy="8.5" r="0.9" fill="#F59E0B" />
              </svg>
            </div>

            {/* Micro Caption */}
            <span className="text-[10px] font-mono font-bold tracking-tight text-amber-300 pr-1">
              Pure Alpha
            </span>
          </div>
        </div>

        {showTagline && (
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping inline-block shrink-0" />
            <span
              className={`font-mono font-medium tracking-tight text-slate-400 whitespace-nowrap ${dimensions.tagline}`}
            >
              autonomous Trading system and build self wealth engine for the future
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default Logo;

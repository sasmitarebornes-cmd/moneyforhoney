import React, { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { Download, Copy, Share2, Check, Sparkles, Send, MessageCircle } from "lucide-react";
import { PnLCardConfig } from "../types";

interface PnLCardProps {
  config: PnLCardConfig;
  onDownloaded?: () => void;
  className?: string;
  showControls?: boolean;
}

export const PnLCard: React.FC<PnLCardProps> = ({
  config,
  onDownloaded,
  className = "",
  showControls = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [qrDataUrl, setQrDataUrl] = useState<string>("");
  const [isRendering, setIsRendering] = useState<boolean>(false);

  const isLandscape = config.aspectRatio === "16:9";
  const canvasWidth = isLandscape ? 1280 : 720;
  const canvasHeight = isLandscape ? 720 : 1280;

  // Generate QR Code data URL when referral link changes
  useEffect(() => {
    let isMounted = true;
    const genQR = async () => {
      try {
        const url = config.referralLink || `https://t.me/${config.botHandle.replace("@", "")}`;
        const dataUrl = await QRCode.toDataURL(url, {
          width: 240,
          margin: 1,
          color: {
            dark: "#020617",
            light: "#FFFFFF",
          },
          errorCorrectionLevel: "M",
        });
        if (isMounted) setQrDataUrl(dataUrl);
      } catch (err) {
        console.error("QR Code generation error:", err);
      }
    };
    genQR();
    return () => {
      isMounted = false;
    };
  }, [config.referralLink, config.botHandle]);

  // Render to canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    setIsRendering(true);

    const w = canvasWidth;
    const h = canvasHeight;
    canvas.width = w;
    canvas.height = h;

    // 1. Draw Background Theme
    drawThemeBackground(ctx, w, h, config.theme, isLandscape);

    // 2. Draw Bot Tag in Top Right
    ctx.save();
    ctx.font = `600 ${isLandscape ? "32px" : "30px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = "#FFFFFF";
    ctx.textAlign = "right";
    ctx.shadowColor = "rgba(0, 0, 0, 0.7)";
    ctx.shadowBlur = 12;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 3;
    const botText = config.botHandle.startsWith("@") ? config.botHandle : `@${config.botHandle}`;
    ctx.fillText(botText, w - (isLandscape ? 60 : 40), isLandscape ? 70 : 80);
    ctx.restore();

    // 3. Draw Main Trade Content (Right side in landscape, centered-upper in portrait)
    const isPositive = config.roiPct >= 0;
    const roiSign = isPositive ? "+" : "";
    const profitSign = config.profitUsdt >= 0 ? "+" : "";
    const primaryColor = isPositive ? "#10FF85" : "#FF3366"; // Vivid neon green like screenshot or neon rose
    const contentX = isLandscape ? w * 0.76 : w / 2;
    const contentY = isLandscape ? h * 0.38 : h * 0.42;
    const textAlign = isLandscape ? "center" : "center";

    // Symbol / Pair Title (e.g. JOD/CNY OTC)
    ctx.save();
    ctx.font = `800 ${isLandscape ? "44px" : "42px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = "#FFFFFF";
    ctx.textAlign = textAlign;
    ctx.shadowColor = "rgba(0, 0, 0, 0.85)";
    ctx.shadowBlur = 16;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 4;
    ctx.fillText(config.symbol.toUpperCase(), contentX, contentY);
    ctx.restore();

    // Big Neon ROI Text (e.g. +512%)
    ctx.save();
    ctx.font = `900 ${isLandscape ? "118px" : "106px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = primaryColor;
    ctx.textAlign = textAlign;
    // Neon glow effect
    ctx.shadowColor = isPositive ? "rgba(16, 255, 133, 0.65)" : "rgba(255, 51, 102, 0.65)";
    ctx.shadowBlur = 28;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    const roiStr = `${roiSign}${config.roiPct}%`;
    ctx.fillText(roiStr, contentX, contentY + (isLandscape ? 104 : 96));
    ctx.restore();

    // Profit & Stake Subtitle (e.g. +$51.20 to stake $10)
    ctx.save();
    ctx.font = `800 ${isLandscape ? "38px" : "34px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = "#FFFFFF";
    ctx.textAlign = textAlign;
    ctx.shadowColor = "rgba(0, 0, 0, 0.85)";
    ctx.shadowBlur = 12;
    const profitText = `${profitSign}$${Math.abs(config.profitUsdt).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
    const stakeText = `$${config.stakeUsdt.toLocaleString("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    })}`;
    ctx.fillText(`${profitText} to stake ${stakeText}`, contentX, contentY + (isLandscape ? 172 : 160));
    ctx.restore();

    // Strategy & Duration Meta Tag (e.g. 2m 51s · Aggressive · 5/5)
    ctx.save();
    ctx.font = `500 ${isLandscape ? "26px" : "24px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = "rgba(226, 232, 240, 0.95)";
    ctx.textAlign = textAlign;
    ctx.shadowColor = "rgba(0, 0, 0, 0.8)";
    ctx.shadowBlur = 10;
    const metaText = `${config.duration} · ${config.riskProfile} · ${config.winScore}`;
    ctx.fillText(metaText, contentX, contentY + (isLandscape ? 222 : 208));
    ctx.restore();

    // 4. Draw QR Code and Referral Badge in Bottom Left
    if (config.showQrCode && qrDataUrl) {
      const qrImg = new Image();
      qrImg.onload = () => {
        const qrSize = isLandscape ? 140 : 130;
        const qrX = isLandscape ? 60 : 40;
        const qrY = isLandscape ? h - qrSize - 50 : h - qrSize - 60;

        ctx.save();
        // QR Code white frame with rounded edges
        ctx.fillStyle = "#FFFFFF";
        ctx.shadowColor = "rgba(0, 0, 0, 0.7)";
        ctx.shadowBlur = 16;
        ctx.shadowOffsetY = 4;
        roundRect(ctx, qrX - 6, qrY - 6, qrSize + 12, qrSize + 12, 10);
        ctx.fill();
        ctx.restore();

        // Draw the QR Code image
        ctx.drawImage(qrImg, qrX, qrY, qrSize, qrSize);

        // QR Code Side Texts
        ctx.save();
        ctx.textAlign = "left";
        ctx.shadowColor = "rgba(0, 0, 0, 0.9)";
        ctx.shadowBlur = 12;

        const textX = qrX + qrSize + 22;
        const textBaseY = qrY + (qrSize * 0.28);

        // Line 1: Your referral link:
        ctx.font = `500 ${isLandscape ? "22px" : "20px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
        ctx.fillStyle = "rgba(203, 213, 225, 0.9)";
        ctx.fillText("Your referral link:", textX, textBaseY);

        // Line 2: @BotHandle (bold white)
        ctx.font = `800 ${isLandscape ? "30px" : "28px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
        ctx.fillStyle = "#FFFFFF";
        ctx.fillText(botText, textX, textBaseY + 36);

        // Line 3: scan & invite friends
        ctx.font = `500 ${isLandscape ? "20px" : "18px"} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
        ctx.fillStyle = "rgba(203, 213, 225, 0.85)";
        ctx.fillText("scan & invite friends", textX, textBaseY + 70);

        ctx.restore();
        setIsRendering(false);
      };
      qrImg.src = qrDataUrl;
    } else {
      setIsRendering(false);
    }
  }, [config, qrDataUrl, isLandscape, canvasWidth, canvasHeight]);

  // Helper: Draw themes
  const drawThemeBackground = (
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    theme: string,
    landscape: boolean
  ) => {
    ctx.save();

    if (theme === "golden_wave_surfer") {
      // 1. SKY GRADIENT (Sunset from deep dusky golden twilight down to glowing horizon)
      const skyGrad = ctx.createLinearGradient(0, 0, 0, h);
      skyGrad.addColorStop(0, "#080b11");
      skyGrad.addColorStop(0.2, "#181309");
      skyGrad.addColorStop(0.42, "#4a2d04");
      skyGrad.addColorStop(0.55, "#a15c03");
      skyGrad.addColorStop(0.68, "#f59e0b");
      skyGrad.addColorStop(0.78, "#fbbf24");
      skyGrad.addColorStop(0.9, "#1e293b");
      skyGrad.addColorStop(1, "#030712");
      ctx.fillStyle = skyGrad;
      ctx.fillRect(0, 0, w, h);

      // Distant radiant sunset glow center
      const sunX = landscape ? w * 0.46 : w * 0.5;
      const sunY = h * 0.65;
      const sunGlow = ctx.createRadialGradient(sunX, sunY, 10, sunX, sunY, w * 0.5);
      sunGlow.addColorStop(0, "rgba(254, 240, 138, 0.95)");
      sunGlow.addColorStop(0.2, "rgba(245, 158, 11, 0.7)");
      sunGlow.addColorStop(0.5, "rgba(180, 83, 9, 0.3)");
      sunGlow.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = sunGlow;
      ctx.fillRect(0, 0, w, h);

      // Ocean Water Surface & Golden Reflections
      const oceanGrad = ctx.createLinearGradient(0, h * 0.66, 0, h);
      oceanGrad.addColorStop(0, "#b45309");
      oceanGrad.addColorStop(0.15, "#78350f");
      oceanGrad.addColorStop(0.4, "#1e1b18");
      oceanGrad.addColorStop(0.8, "#090d16");
      oceanGrad.addColorStop(1, "#02040a");
      ctx.fillStyle = oceanGrad;
      ctx.fillRect(0, h * 0.66, w, h * 0.34);

      // Golden shimmer ripples on water
      for (let i = 0; i < 28; i++) {
        const yPos = h * 0.67 + (i * (h * 0.31 / 28));
        const widthSpread = (i / 28) * (w * 0.7);
        const ripGrad = ctx.createLinearGradient(sunX - widthSpread, yPos, sunX + widthSpread, yPos);
        ripGrad.addColorStop(0, "rgba(245, 158, 11, 0)");
        ripGrad.addColorStop(0.5, `rgba(253, 230, 138, ${0.45 - (i * 0.01)})`);
        ripGrad.addColorStop(1, "rgba(245, 158, 11, 0)");
        ctx.fillStyle = ripGrad;
        ctx.fillRect(sunX - widthSpread, yPos, widthSpread * 2, 2.5);
      }

      // 2. GIANT GOLDEN BARREL WAVE (Left into center, curling over like screenshot)
      const waveGrad = ctx.createRadialGradient(
        landscape ? w * 0.18 : w * 0.12,
        h * 0.48,
        30,
        landscape ? w * 0.25 : w * 0.2,
        h * 0.45,
        w * 0.55
      );
      waveGrad.addColorStop(0, "rgba(254, 243, 199, 0.95)"); // Bright golden sunlight inside tube
      waveGrad.addColorStop(0.18, "rgba(245, 158, 11, 0.85)");
      waveGrad.addColorStop(0.4, "rgba(180, 83, 9, 0.75)");
      waveGrad.addColorStop(0.7, "rgba(69, 26, 3, 0.65)");
      waveGrad.addColorStop(1, "rgba(15, 23, 42, 0.4)");

      ctx.fillStyle = waveGrad;
      ctx.beginPath();
      // Wave outline curling
      ctx.moveTo(0, h * 0.85);
      ctx.bezierCurveTo(w * 0.08, h * 0.72, w * 0.02, h * 0.35, w * 0.14, h * 0.15);
      ctx.bezierCurveTo(w * 0.22, 0, w * 0.38, h * 0.08, w * 0.42, h * 0.28);
      ctx.bezierCurveTo(w * 0.44, h * 0.45, w * 0.32, h * 0.62, w * 0.28, h * 0.75);
      ctx.lineTo(0, h * 0.85);
      ctx.fill();

      // Tube interior shadow & luminous lip
      ctx.strokeStyle = "rgba(254, 240, 138, 0.85)";
      ctx.lineWidth = 14;
      ctx.beginPath();
      ctx.arc(landscape ? w * 0.18 : w * 0.15, h * 0.42, landscape ? 190 : 160, -0.6 * Math.PI, 0.7 * Math.PI);
      ctx.stroke();

      // Water spray particles & froth
      for (let p = 0; p < 320; p++) {
        const px = Math.random() * (w * 0.48);
        const py = Math.random() * (h * 0.78);
        const pSize = Math.random() * 3.5 + 0.5;
        const opacity = Math.random() * 0.75 + 0.15;
        ctx.fillStyle = `rgba(254, 243, 199, ${opacity})`;
        ctx.beginPath();
        ctx.arc(px, py, pSize, 0, Math.PI * 2);
        ctx.fill();
      }

      // 3. SILHOUETTED SURFER CARVING THE WAVE (like in the screenshot)
      drawSurferSilhouette(ctx, landscape ? w * 0.12 : w * 0.14, h * 0.52, landscape ? 1.25 : 1.1);

      // Dark cinematic vignette on right side so text pops with extreme contrast
      const rightVignette = ctx.createLinearGradient(w * 0.4, 0, w, 0);
      rightVignette.addColorStop(0, "rgba(3, 7, 18, 0)");
      rightVignette.addColorStop(0.45, "rgba(3, 7, 18, 0.45)");
      rightVignette.addColorStop(0.85, "rgba(3, 7, 18, 0.85)");
      rightVignette.addColorStop(1, "rgba(3, 7, 18, 0.94)");
      ctx.fillStyle = rightVignette;
      ctx.fillRect(w * 0.4, 0, w * 0.6, h);
    } else if (theme === "money_for_honey_hive") {
      // Golden Cyber Hive Theme
      const grad = ctx.createLinearGradient(0, 0, w, h);
      grad.addColorStop(0, "#09090b");
      grad.addColorStop(0.5, "#171206");
      grad.addColorStop(1, "#040301");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // Draw Honeycomb grid
      ctx.strokeStyle = "rgba(245, 158, 11, 0.16)";
      ctx.lineWidth = 1.5;
      const hexR = 38;
      const hexW = Math.sqrt(3) * hexR;
      const hexH = 2 * hexR * 0.75;
      for (let row = 0; row < h / hexH + 2; row++) {
        for (let col = 0; col < (w * 0.5) / hexW + 2; col++) {
          const xOff = (row % 2) * (hexW / 2);
          drawHexagon(ctx, col * hexW + xOff, row * hexH, hexR);
        }
      }

      // Ascending Green Candlestick Wave
      ctx.strokeStyle = "rgba(16, 255, 133, 0.4)";
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(0, h * 0.75);
      ctx.bezierCurveTo(w * 0.2, h * 0.7, w * 0.35, h * 0.4, w * 0.6, h * 0.25);
      ctx.stroke();
    } else if (theme === "midnight_neon_bull") {
      // Midnight Neon Bull / Wall St Quant
      const grad = ctx.createLinearGradient(0, 0, w, h);
      grad.addColorStop(0, "#020617");
      grad.addColorStop(0.6, "#090f1d");
      grad.addColorStop(1, "#030712");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // Laser Matrix Grid
      ctx.strokeStyle = "rgba(16, 185, 129, 0.12)";
      ctx.lineWidth = 1;
      for (let x = 0; x < w * 0.55; x += 50) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += 50) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w * 0.55, y);
        ctx.stroke();
      }
    } else if (theme === "cosmic_nebula") {
      // Deep Cosmic Nebula & Galaxy Stars
      const grad = ctx.createRadialGradient(w * 0.3, h * 0.5, 40, w * 0.5, h * 0.5, w);
      grad.addColorStop(0, "#2e1065");
      grad.addColorStop(0.4, "#0f172a");
      grad.addColorStop(1, "#020617");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      for (let s = 0; s < 180; s++) {
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.random() * 0.8 + 0.2})`;
        ctx.beginPath();
        ctx.arc(Math.random() * w, Math.random() * h, Math.random() * 2, 0, Math.PI * 2);
        ctx.fill();
      }
    } else if (theme === "matrix_alpha") {
      // Matrix Alpha Terminal
      ctx.fillStyle = "#020805";
      ctx.fillRect(0, 0, w, h);

      ctx.fillStyle = "rgba(16, 255, 133, 0.1)";
      ctx.font = "14px monospace";
      for (let c = 0; c < 25; c++) {
        for (let r = 0; r < 35; r++) {
          ctx.fillText(Math.random() > 0.5 ? "1" : "0", c * 24 + 10, r * 22 + 20);
        }
      }
    } else {
      // Luxury Dark Gold Minimal
      const grad = ctx.createLinearGradient(0, 0, w, h);
      grad.addColorStop(0, "#0b0c10");
      grad.addColorStop(0.5, "#1f242d");
      grad.addColorStop(1, "#0b0c10");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      ctx.strokeStyle = "rgba(245, 158, 11, 0.25)";
      ctx.lineWidth = 2;
      ctx.strokeRect(30, 30, w - 60, h - 60);
    }

    ctx.restore();
  };

  // Draw surfer silhouette with board and spray
  const drawSurferSilhouette = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    scale: number
  ) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);

    // Dark silhouette color with slight warm backlighting
    ctx.fillStyle = "#0b0f19";
    ctx.strokeStyle = "rgba(254, 240, 138, 0.6)";
    ctx.lineWidth = 1.2;

    // Surfboard (angled dynamically)
    ctx.beginPath();
    ctx.ellipse(5, 52, 58, 11, -0.32, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Surfer body crouching deep in the barrel
    // Torso
    ctx.beginPath();
    ctx.ellipse(0, 8, 15, 24, -0.22, 0, Math.PI * 2);
    ctx.fill();

    // Head with sun-kissed rim light
    ctx.beginPath();
    ctx.arc(-8, -26, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Left Arm extended back touching the wall of water
    ctx.lineWidth = 6.5;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#0b0f19";
    ctx.beginPath();
    ctx.moveTo(-6, -8);
    ctx.lineTo(-38, -14);
    ctx.lineTo(-65, -8);
    ctx.stroke();

    // Right Arm forward for balance
    ctx.beginPath();
    ctx.moveTo(8, -6);
    ctx.lineTo(26, 12);
    ctx.lineTo(48, 8);
    ctx.stroke();

    // Front Bent Leg
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(8, 22);
    ctx.lineTo(24, 38);
    ctx.lineTo(26, 48);
    ctx.stroke();

    // Back Squatting Leg
    ctx.beginPath();
    ctx.moveTo(-10, 20);
    ctx.lineTo(-24, 34);
    ctx.lineTo(-14, 48);
    ctx.stroke();

    // Board wake spray
    for (let s = 0; s < 45; s++) {
      ctx.fillStyle = `rgba(254, 243, 199, ${Math.random() * 0.6 + 0.2})`;
      ctx.beginPath();
      ctx.arc(
        -30 - Math.random() * 60,
        50 + (Math.random() - 0.5) * 20,
        Math.random() * 3 + 1,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }

    ctx.restore();
  };

  // Helper: Hexagon for honeycomb theme
  const drawHexagon = (ctx: CanvasRenderingContext2D, x: number, y: number, r: number) => {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i;
      const hx = x + r * Math.cos(angle);
      const hy = y + r * Math.sin(angle);
      if (i === 0) ctx.moveTo(hx, hy);
      else ctx.lineTo(hx, hy);
    }
    ctx.closePath();
    ctx.stroke();
  };

  // Helper: Rounded Rectangle
  const roundRect = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    w: number,
    h: number,
    radius: number
  ) => {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + w - radius, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    ctx.lineTo(x + w, y + h - radius);
    ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    ctx.lineTo(x + radius, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  };

  // Download High-Res PNG
  const handleDownloadPng = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cleanSym = config.symbol.replace(/[^a-zA-Z0-9]/g, "_");
    const filename = `PNL_CARD_${cleanSym}_${config.roiPct > 0 ? "WIN" : "LOSS"}_${Math.abs(
      config.roiPct
    )}PCT.png`;

    const link = document.createElement("a");
    link.download = filename;
    link.href = canvas.toDataURL("image/png");
    link.click();

    if (onDownloaded) onDownloaded();
  };

  // Copy Image to Clipboard
  const handleCopyImage = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        try {
          await navigator.clipboard.write([
            new ClipboardItem({
              "image/png": blob,
            }),
          ]);
          setCopied(true);
          setTimeout(() => setCopied(false), 2500);
        } catch {
          // Fallback: Copy data url or link text
          await navigator.clipboard.writeText(
            `🚀 ${config.symbol} ${config.roiPct >= 0 ? "+" : ""}${config.roiPct}% | Realized: +$${
              config.profitUsdt
            } USDT on stake $${config.stakeUsdt} via ${config.botHandle}! Join: ${config.referralLink}`
          );
          setCopied(true);
          setTimeout(() => setCopied(false), 2500);
        }
      }, "image/png");
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  // Share to Telegram
  const handleShareTelegram = () => {
    const text = encodeURIComponent(
      `🔥 AUTONOMOUS QUANT PROFIT SIGNAL FILLED!\n\n` +
      `⚡ Pair: #${config.symbol.replace(/[^a-zA-Z0-9]/g, "")}\n` +
      `📈 Return: ${config.roiPct >= 0 ? "+" : ""}${config.roiPct}%\n` +
      `💰 Harvested: +$${config.profitUsdt} USDT (Stake: $${config.stakeUsdt})\n` +
      `⏱ Duration: ${config.duration} | Mode: ${config.riskProfile}\n\n` +
      `🤖 Powered by @MoneyForHoneyBot & ${config.botHandle}\n` +
      `🔗 Join VIP Quant Signals: ${config.referralLink}`
    );
    window.open(`https://t.me/share/url?url=${encodeURIComponent(config.referralLink)}&text=${text}`, "_blank");
  };

  // Share to WhatsApp
  const handleShareWhatsApp = () => {
    const text = encodeURIComponent(
      `🔥 *MONEY For HONEY Trade Result*\n\n` +
      `📈 *${config.symbol}*: *+${config.roiPct}%* ROI\n` +
      `💰 Realized: *+$${config.profitUsdt} USDT* (Stake: $${config.stakeUsdt})\n` +
      `⏱ Time: ${config.duration} · ${config.riskProfile}\n\n` +
      `Join autonomous trading: ${config.referralLink}`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  };

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {/* Live Canvas Viewport */}
      <div
        className={`relative w-full overflow-hidden rounded-2xl border border-slate-800 shadow-2xl bg-slate-950 transition-all ${
          isLandscape ? "aspect-video max-w-[860px]" : "aspect-[9/16] max-w-[420px]"
        }`}
      >
        <canvas
          ref={canvasRef}
          className="w-full h-full object-contain block"
          style={{ imageRendering: "auto" }}
        />

        {isRendering && (
          <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center">
            <span className="text-xs font-mono text-amber-400 animate-pulse">
              Generating High-Res Card...
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      {showControls && (
        <div className="flex flex-wrap items-center justify-center gap-2.5 w-full max-w-[860px]">
          {/* Download PNG Button */}
          <button
            onClick={handleDownloadPng}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-mono text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-lg shadow-amber-500/20 transition-all active:scale-95"
            title="Download razor-sharp PNG image"
          >
            <Download className="w-4 h-4" />
            <span>Download PNG (1280p)</span>
          </button>

          {/* Copy Image Button */}
          <button
            onClick={handleCopyImage}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-mono text-xs font-bold border transition-all active:scale-95 ${
              copied
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "bg-slate-900 hover:bg-slate-800 text-slate-200 border-slate-700"
            }`}
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? "Image Copied to Clipboard!" : "Copy Image"}</span>
          </button>

          {/* Share to Telegram */}
          <button
            onClick={handleShareTelegram}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-mono text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-600/20 transition-all active:scale-95"
          >
            <Send className="w-4 h-4" />
            <span>Share to Telegram</span>
          </button>

          {/* Share to WhatsApp */}
          <button
            onClick={handleShareWhatsApp}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-mono text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all active:scale-95"
          >
            <MessageCircle className="w-4 h-4" />
            <span>Share to WhatsApp</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default PnLCard;

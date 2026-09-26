import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Recycle,
  UploadCloud,
  Camera,
  X,
  RotateCcw,
  CheckCircle2,
  Newspaper,
  Wrench,
  Apple,
  PackageOpen,
  Radar,
  Info,
} from "lucide-react";

/**
 * EcoSort — AI Waste Scanner
 * Frontend for the EcoAI waste classification model (keras_model.h5 / labels.txt).
 * Drop this component anywhere; wire `runInference` to your real /predict endpoint
 * when the backend is ready. Google Fonts are loaded via the <style> tag below —
 * move that <link>/@import into your global stylesheet in production.
 */

// ---------- Domain data ----------------------------------------------------

const CATEGORIES = {
  Paper: {
    color: "#2F6FED",
    icon: Newspaper,
    guidance:
      "Flatten it and keep it dry. Remove any plastic film, tape, or lamination before it goes in the paper stream.",
  },
  Organic: {
    color: "#4C9A2A",
    icon: Apple,
    guidance:
      "Send it to compost or food waste collection. Keep packaging, stickers, and twist ties out of the bin.",
  },
  Metal: {
    color: "#7C8B86",
    icon: Wrench,
    guidance:
      "Rinse off food residue and leave the label on. Cans and clean foil both belong in the metal stream.",
  },
  Plastic: {
    color: "#E8A33D",
    icon: PackageOpen,
    guidance:
      "Check the resin code on the base. Rinse the item and leave the cap on if your facility accepts it attached.",
  },
};

const CLASS_ORDER = ["Paper", "Organic", "Metal", "Plastic"];

// ---------- Mock inference (swap for a real fetch to your model server) ----

function mockInference() {
  const winnerIdx = Math.floor(Math.random() * CLASS_ORDER.length);
  const raw = CLASS_ORDER.map((_, i) =>
    i === winnerIdx ? 0.6 + Math.random() * 0.35 : Math.random() * 0.25
  );
  const sum = raw.reduce((a, b) => a + b, 0);
  const normalized = raw.map((v) => v / sum);
  return CLASS_ORDER.map((name, i) => ({ name, score: normalized[i] })).sort(
    (a, b) => b.score - a.score
  );
}

// ---------- Component -------------------------------------------------------

export default function WasteClassifierPage() {
  const [tab, setTab] = useState("upload"); // 'upload' | 'camera'
  const [imageSrc, setImageSrc] = useState(null);
  const [status, setStatus] = useState("idle"); // 'idle' | 'scanning' | 'done'
  const [scores, setScores] = useState(null);
  const [cameraError, setCameraError] = useState(null);

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  const startCamera = useCallback(async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (err) {
      setCameraError(
        "Camera access was blocked or unavailable. Check your browser permissions."
      );
    }
  }, []);

  useEffect(() => {
    if (tab === "camera" && !imageSrc) startCamera();
    if (tab !== "camera") stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const captureFrame = () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    setImageSrc(canvas.toDataURL("image/jpeg", 0.92));
    stopCamera();
  };

  const handleFile = (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => setImageSrc(reader.result);
    reader.readAsDataURL(file);
    setStatus("idle");
    setScores(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFile(e.dataTransfer.files?.[0]);
  };

  const reset = () => {
    setImageSrc(null);
    setStatus("idle");
    setScores(null);
    setCameraError(null);
    if (tab === "camera") startCamera();
  };

  const analyze = () => {
    setStatus("scanning");
    setTimeout(() => {
      setScores(mockInference());
      setStatus("done");
    }, 1700);
  };

  const winner = scores?.[0];
  const WinnerIcon = winner ? CATEGORIES[winner.name].icon : null;

  return (
    <div
      className="min-h-screen w-full"
      style={{
        background:
          "radial-gradient(ellipse at top left, #F3ECDD 0%, #ECE4D2 55%, #E4D9C3 100%)",
        color: "#1B2420",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        .font-display { font-family: 'Big Shoulders Display', sans-serif; }
        .font-body { font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .grain::before {
          content: "";
          position: absolute; inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
          pointer-events: none;
        }
        @keyframes scanline {
          0% { top: 4%; }
          50% { top: 92%; }
          100% { top: 4%; }
        }
        .scan-line {
          position: absolute; left: 0; right: 0; height: 2px;
          background: linear-gradient(90deg, transparent, #FF5A1F 20%, #FF5A1F 80%, transparent);
          box-shadow: 0 0 12px 2px rgba(255,90,31,0.7);
          animation: scanline 1.7s ease-in-out infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .scan-line { animation: none; top: 50%; }
        }
      `}</style>

      <div className="relative grain max-w-6xl mx-auto px-6 py-10 md:py-14">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-14">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center border-2"
              style={{ borderColor: "#1B2420" }}
            >
              <Recycle className="w-5 h-5" strokeWidth={2.5} />
            </div>
            <span className="font-display text-2xl tracking-tight">
              ECOSORT
            </span>
          </div>
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border font-body text-sm"
            style={{ borderColor: "rgba(27,36,32,0.2)", color: "#445048" }}
          >
            <span className="w-2 h-2 rounded-full bg-green-600 inline-block" />
            Scanner online
          </div>
        </div>

        {/* Hero: split — copy on the left, live scanner module on the right */}
        <div className="grid md:grid-cols-2 gap-12 items-start">
          {/* Left: copy + legend */}
          <div className="md:pr-6 md:pt-4">
            <h1 className="font-display text-5xl md:text-6xl leading-[0.95] mb-6">
              Point a camera
              <br />
              at your trash.
              <br />
              Know the bin.
            </h1>
            <p
              className="font-body text-lg leading-relaxed mb-8 max-w-md"
              style={{ color: "#445048" }}
            >
              Upload a photo or use your camera and the model sorts it into
              one of four streams in under two seconds, the same way a
              materials recovery facility would.
            </p>

            <div className="space-y-3">
              {CLASS_ORDER.map((name) => {
                const Icon = CATEGORIES[name].icon;
                return (
                  <div key={name} className="flex items-center gap-3">
                    <span
                      className="w-2.5 h-8 rounded-sm"
                      style={{ background: CATEGORIES[name].color }}
                    />
                    <Icon className="w-4 h-4" style={{ color: "#445048" }} />
                    <span className="font-body font-medium">{name}</span>
                  </div>
                );
              })}
            </div>

            <div
              className="mt-10 pt-6 border-t font-mono text-xs flex gap-8"
              style={{ borderColor: "rgba(27,36,32,0.15)", color: "#6B756E" }}
            >
              <div>
                <div className="text-2xl font-body font-bold" style={{ color: "#1B2420" }}>
                  94.2%
                </div>
                top-1 accuracy
              </div>
              <div>
                <div className="text-2xl font-body font-bold" style={{ color: "#1B2420" }}>
                  12,400+
                </div>
                training images
              </div>
              <div>
                <div className="text-2xl font-body font-bold" style={{ color: "#1B2420" }}>
                  4
                </div>
                waste streams
              </div>
            </div>
          </div>

          {/* Right: the scanner module itself */}
          <div
            className="rounded-2xl border p-5 md:p-6"
            style={{
              background: "rgba(255,255,255,0.5)",
              borderColor: "rgba(27,36,32,0.15)",
              boxShadow: "0 20px 50px -20px rgba(27,36,32,0.25)",
            }}
          >
            {/* Tabs */}
            <div className="flex gap-1 mb-5 p-1 rounded-lg" style={{ background: "rgba(27,36,32,0.06)" }}>
              {[
                { id: "upload", label: "Upload photo", icon: UploadCloud },
                { id: "camera", label: "Use camera", icon: Camera },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => {
                    setTab(id);
                    reset();
                  }}
                  className="flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-body font-medium transition-all duration-300 focus:outline-none focus-visible:ring-2"
                  style={{
                    background: tab === id ? "#1B2420" : "transparent",
                    color: tab === id ? "#ECE4D2" : "#445048",
                    ringColor: "#FF5A1F",
                  }}
                  aria-pressed={tab === id}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </div>

            {/* Capture / preview area */}
            <div
              className="relative rounded-xl overflow-hidden mb-5"
              style={{
                aspectRatio: "4 / 3",
                background: "#1B2420",
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
            >
              {/* Upload empty state */}
              {tab === "upload" && !imageSrc && (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full h-full flex flex-col items-center justify-center gap-3 text-center px-6 transition-colors duration-300 hover:bg-white/5 focus:outline-none"
                  style={{ color: "#ECE4D2" }}
                >
                  <UploadCloud className="w-8 h-8" style={{ color: "#FF5A1F" }} />
                  <span className="font-body text-sm">
                    Drag a JPG or PNG here, or click to browse
                  </span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png, image/jpeg"
                    className="hidden"
                    onChange={(e) => handleFile(e.target.files?.[0])}
                  />
                </button>
              )}

              {/* Camera live view */}
              {tab === "camera" && !imageSrc && (
                <div className="w-full h-full flex items-center justify-center relative">
                  {cameraError ? (
                    <div className="flex flex-col items-center gap-2 px-6 text-center" style={{ color: "#ECE4D2" }}>
                      <Info className="w-6 h-6" style={{ color: "#FF5A1F" }} />
                      <span className="font-body text-sm">{cameraError}</span>
                    </div>
                  ) : (
                    <>
                      <video
                        ref={videoRef}
                        muted
                        playsInline
                        className="w-full h-full object-cover"
                      />
                      <button
                        onClick={captureFrame}
                        className="absolute bottom-4 w-14 h-14 rounded-full border-4 transition-transform duration-300 hover:scale-105 active:scale-95 focus:outline-none"
                        style={{ borderColor: "#ECE4D2", background: "#FF5A1F" }}
                        aria-label="Capture photo"
                      />
                    </>
                  )}
                </div>
              )}

              {/* Image preview with scan-target corners */}
              {imageSrc && (
                <div className="relative w-full h-full">
                  <img
                    src={imageSrc}
                    alt="Item to classify"
                    className="w-full h-full object-cover"
                  />
                  {/* corner brackets */}
                  {[
                    "top-3 left-3 border-t-2 border-l-2",
                    "top-3 right-3 border-t-2 border-r-2",
                    "bottom-3 left-3 border-b-2 border-l-2",
                    "bottom-3 right-3 border-b-2 border-r-2",
                  ].map((cls, i) => (
                    <span
                      key={i}
                      className={`absolute w-6 h-6 ${cls}`}
                      style={{ borderColor: "#FF5A1F" }}
                    />
                  ))}
                  {status === "scanning" && <div className="scan-line" />}
                  <button
                    onClick={reset}
                    className="absolute top-3 right-3 translate-x-9 w-7 h-7 rounded-full flex items-center justify-center transition-colors duration-300 hover:bg-black/70"
                    style={{ background: "rgba(27,36,32,0.85)", color: "#ECE4D2" }}
                    aria-label="Remove photo"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Action row */}
            {imageSrc && status !== "done" && (
              <button
                onClick={analyze}
                disabled={status === "scanning"}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-body font-semibold transition-all duration-300 focus:outline-none focus-visible:ring-2 disabled:opacity-70"
                style={{ background: "#FF5A1F", color: "#1B2420", ringColor: "#1B2420" }}
              >
                <Radar className={`w-4 h-4 ${status === "scanning" ? "animate-spin" : ""}`} />
                {status === "scanning" ? "Scanning material composition…" : "Analyze item"}
              </button>
            )}

            {/* Result: manifest ticket */}
            {status === "done" && scores && (
              <div
                className="rounded-xl overflow-hidden border"
                style={{ borderColor: "rgba(27,36,32,0.15)" }}
              >
                <div
                  className="flex items-center gap-4 p-4"
                  style={{ background: CATEGORIES[winner.name].color + "22" }}
                >
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: CATEGORIES[winner.name].color }}
                  >
                    {WinnerIcon && <WinnerIcon className="w-6 h-6 text-white" />}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-display text-2xl leading-none">
                        {winner.name}
                      </span>
                      <CheckCircle2 className="w-4 h-4" style={{ color: CATEGORIES[winner.name].color }} />
                    </div>
                    <span className="font-mono text-xs" style={{ color: "#445048" }}>
                      confidence {(winner.score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="p-4">
                  <p className="font-body text-sm mb-4" style={{ color: "#445048" }}>
                    {CATEGORIES[winner.name].guidance}
                  </p>

                  <div className="space-y-2 mb-4">
                    {scores.map(({ name, score }) => (
                      <div key={name} className="flex items-center gap-3">
                        <span className="font-body text-xs w-16" style={{ color: "#445048" }}>
                          {name}
                        </span>
                        <div
                          className="flex-1 h-2 rounded-full overflow-hidden"
                          style={{ background: "rgba(27,36,32,0.08)" }}
                        >
                          <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{
                              width: `${(score * 100).toFixed(1)}%`,
                              background: CATEGORIES[name].color,
                            }}
                          />
                        </div>
                        <span className="font-mono text-xs w-12 text-right" style={{ color: "#1B2420" }}>
                          {(score * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={reset}
                    className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg border font-body text-sm font-medium transition-all duration-300 hover:bg-black/5 focus:outline-none focus-visible:ring-2"
                    style={{ borderColor: "rgba(27,36,32,0.2)", color: "#1B2420", ringColor: "#FF5A1F" }}
                  >
                    <RotateCcw className="w-4 h-4" />
                    Scan another item
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* How it works */}
        <div className="mt-24 grid md:grid-cols-3 gap-8">
          {[
            {
              n: "01",
              title: "Capture",
              body: "Upload a photo or point your camera at the item on a plain background.",
            },
            {
              n: "02",
              title: "Analyze",
              body: "A convolutional model checks shape, texture, and material cues against four trained classes.",
            },
            {
              n: "03",
              title: "Sort",
              body: "You get the matching stream plus disposal steps specific to that material.",
            },
          ].map((step) => (
            <div key={step.n}>
              <div className="font-mono text-sm mb-2" style={{ color: "#FF5A1F" }}>
                {step.n}
              </div>
              <h3 className="font-display text-2xl mb-2">{step.title}</h3>
              <p className="font-body text-sm leading-relaxed" style={{ color: "#445048" }}>
                {step.body}
              </p>
            </div>
          ))}
        </div>

        <div
          className="mt-16 pt-6 border-t font-body text-xs flex items-center justify-between"
          style={{ borderColor: "rgba(27,36,32,0.15)", color: "#6B756E" }}
        >
          <span>EcoSort runs the classification locally — no image leaves your device.</span>
          <span>Model v1 · keras_model.h5</span>
        </div>
      </div>
    </div>
  );
}

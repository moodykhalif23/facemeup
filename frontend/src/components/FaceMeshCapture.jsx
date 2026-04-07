import { useEffect, useRef, useState } from 'react';
import { FaceMesh } from '@mediapipe/face_mesh';
import { Camera } from '@mediapipe/camera_utils';

// ─── Phase definitions ────────────────────────────────────────────────────────
const HOLD_MS = 1500; // ms to hold pose before auto-capture

const PHASES = [
  {
    id: 'front',
    label: 'Look Straight',
    instruction: 'Face the camera directly — eyes level',
    emoji: '🎯',
    check: (yaw, pitch) => yaw >= 0.35 && yaw <= 0.65 && pitch >= 0.38 && pitch <= 0.62,
  },
  {
    id: 'up',
    label: 'Tilt Up',
    instruction: 'Slowly tilt your chin upward',
    emoji: '⬆',
    check: (yaw, pitch) => Math.abs(yaw - 0.5) < 0.22 && pitch < 0.36,
  },
  {
    id: 'down',
    label: 'Tilt Down',
    instruction: 'Slowly tilt your chin downward',
    emoji: '⬇',
    check: (yaw, pitch) => Math.abs(yaw - 0.5) < 0.22 && pitch > 0.64,
  },
  {
    id: 'left',
    label: 'Turn Left',
    instruction: 'Turn your face to the left',
    emoji: '⬅',
    check: (yaw, pitch) => yaw < 0.36 && Math.abs(pitch - 0.5) < 0.22,
  },
  {
    id: 'right',
    label: 'Turn Right',
    instruction: 'Turn your face to the right',
    emoji: '➡',
    check: (yaw, pitch) => yaw > 0.64 && Math.abs(pitch - 0.5) < 0.22,
  },
];

// ─── MediaPipe landmark index groups ─────────────────────────────────────────
const FACE_OVAL     = [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109];
const LEFT_EYE      = [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246];
const RIGHT_EYE     = [362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398];
const LEFT_BROW     = [46,53,52,65,55];
const RIGHT_BROW    = [276,283,282,295,285];
const LIPS_OUTER    = [61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146];
const NOSE_BRIDGE   = [168,6,197,195,5];

// ─── Helpers ──────────────────────────────────────────────────────────────────
/** Estimate yaw (left/right) and pitch (up/down) from landmarks. Both 0-1, 0.5 = neutral. */
const estimatePose = (landmarks) => {
  const nose     = landmarks[4];
  const forehead = landmarks[10];
  const chin     = landmarks[152];
  const leftEar  = landmarks[234];
  const rightEar = landmarks[454];

  const faceH = chin.y - forehead.y;
  const faceW = rightEar.x - leftEar.x;
  if (faceH <= 0 || faceW <= 0) return { yaw: 0.5, pitch: 0.5 };

  return {
    yaw:   Math.max(0, Math.min(1, (nose.x - leftEar.x) / faceW)),
    pitch: Math.max(0, Math.min(1, (nose.y - forehead.y) / faceH)),
  };
};

/** Draw contour path through an array of landmark indices. */
const drawContour = (ctx, landmarks, indices, w, h, close = true) => {
  ctx.beginPath();
  indices.forEach((idx, i) => {
    const { x, y } = landmarks[idx];
    i === 0 ? ctx.moveTo(x * w, y * h) : ctx.lineTo(x * w, y * h);
  });
  if (close) ctx.closePath();
  ctx.stroke();
};

/** Draw an arrowhead at (ex,ey) pointing from (sx,sy). */
const drawArrow = (ctx, sx, sy, ex, ey, color, size = 12) => {
  const angle = Math.atan2(ey - sy, ex - sx);
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(sx, sy);
  ctx.lineTo(ex, ey);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(ex, ey);
  ctx.lineTo(ex - size * Math.cos(angle - 0.4), ey - size * Math.sin(angle - 0.4));
  ctx.lineTo(ex - size * Math.cos(angle + 0.4), ey - size * Math.sin(angle + 0.4));
  ctx.closePath();
  ctx.fill();
  ctx.restore();
};

/** Capture a clean frame from the video element (no mesh overlay). */
const captureCleanFrame = (video, quality = 0.92) =>
  new Promise((resolve) => {
    if (!video || video.readyState < 2) { resolve(null); return; }
    const tmp = document.createElement('canvas');
    tmp.width  = video.videoWidth  || 640;
    tmp.height = video.videoHeight || 480;
    tmp.getContext('2d').drawImage(video, 0, 0, tmp.width, tmp.height);
    tmp.toBlob((blob) => resolve(blob), 'image/jpeg', quality);
  });

// ─── Main component ───────────────────────────────────────────────────────────
const FaceMeshCapture = ({ onCapture, onFaceDetected }) => {
  const videoRef   = useRef(null);
  const canvasRef  = useRef(null);
  const faceMeshRef = useRef(null);
  const cameraRef   = useRef(null);

  // Refs for values accessed inside the stable onResults closure
  const isProcessingRef    = useRef(false);
  const holdStartRef       = useRef(null);
  const capturedPhasesRef  = useRef([]);
  const currentPhaseRef    = useRef(0);
  const isCapturedRef      = useRef(false);   // debounce double-capture
  const onCaptureRef       = useRef(onCapture);
  const onFaceDetectedRef  = useRef(onFaceDetected);

  // Keep callback refs fresh
  useEffect(() => { onCaptureRef.current = onCapture; }, [onCapture]);
  useEffect(() => { onFaceDetectedRef.current = onFaceDetected; }, [onFaceDetected]);

  // State for rendering
  const [isInitialized, setIsInitialized]   = useState(false);
  const [error, setError]                   = useState(null);
  const [faceDetected, setFaceDetected]     = useState(false);
  const [isFaceClose, setIsFaceClose]       = useState(false);
  const [currentPhase, setCurrentPhase]     = useState(0);
  const [completedPhases, setCompletedPhases] = useState([]);
  const [holdProgress, setHoldProgress]     = useState(0);   // 0-100
  const [poseMatch, setPoseMatch]           = useState(false);
  const [allDone, setAllDone]               = useState(false);

  // Keep currentPhaseRef in sync with state
  useEffect(() => { currentPhaseRef.current = currentPhase; }, [currentPhase]);

  // ── Canvas drawing ──────────────────────────────────────────────────────────
  const drawScene = (ctx, landmarks, w, h, poseMatches, progress, phaseId) => {
    const primary   = poseMatches ? '#10B981' : '#F97316';
    const secondary = poseMatches ? 'rgba(16,185,129,0.5)' : 'rgba(249,115,22,0.5)';
    const dim       = poseMatches ? 'rgba(16,185,129,0.25)' : 'rgba(249,115,22,0.25)';

    // Subtle landmark dots
    ctx.fillStyle = dim;
    landmarks.forEach(({ x, y }) => {
      ctx.beginPath();
      ctx.arc(x * w, y * h, 1.2, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Feature contours
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = primary;
    drawContour(ctx, landmarks, FACE_OVAL, w, h);

    ctx.lineWidth = 1.5;
    ctx.strokeStyle = secondary;
    drawContour(ctx, landmarks, LEFT_EYE, w, h);
    drawContour(ctx, landmarks, RIGHT_EYE, w, h);
    drawContour(ctx, landmarks, LIPS_OUTER, w, h);

    ctx.lineWidth = 1.5;
    ctx.strokeStyle = dim;
    drawContour(ctx, landmarks, LEFT_BROW, w, h, false);
    drawContour(ctx, landmarks, RIGHT_BROW, w, h, false);
    drawContour(ctx, landmarks, NOSE_BRIDGE, w, h, false);

  };

  // ── faceMesh initialization ────────────────────────────────────────────────
  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        if (!videoRef.current || !canvasRef.current) return;

        const faceMesh = new FaceMesh({
          locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`,
        });

        faceMesh.setOptions({
          maxNumFaces: 1,
          refineLandmarks: true,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5,
        });

        faceMesh.onResults((results) => {
          if (!mounted || !canvasRef.current) return;

          const canvas = canvasRef.current;
          const ctx    = canvas.getContext('2d');
          const { width: w, height: h } = canvas;

          ctx.clearRect(0, 0, w, h);

          if (results.image) {
            try { ctx.drawImage(results.image, 0, 0, w, h); }
            catch { isProcessingRef.current = false; return; }
          }

          if (results.multiFaceLandmarks?.length > 0) {
            const landmarks = results.multiFaceLandmarks[0];
            const xs = landmarks.map(lm => lm.x);
            const faceFraction = Math.max(...xs) - Math.min(...xs);
            const close = faceFraction > 0.32;

            setFaceDetected(true);
            setIsFaceClose(close);

            if (onFaceDetectedRef.current) onFaceDetectedRef.current(landmarks);

            const { yaw, pitch } = estimatePose(landmarks);
            const phaseIdx = currentPhaseRef.current;
            const phase    = PHASES[phaseIdx];
            const matches  = close && phase.check(yaw, pitch);

            setPoseMatch(matches);

            // Hold-timer logic
            if (matches && !isCapturedRef.current) {
              const now = Date.now();
              if (!holdStartRef.current) holdStartRef.current = now;
              const elapsed  = now - holdStartRef.current;
              const progress = Math.min(100, (elapsed / HOLD_MS) * 100);
              setHoldProgress(progress);

              // Draw scene with progress
              drawScene(ctx, landmarks, w, h, true, progress, phase.id);

              if (elapsed >= HOLD_MS) {
                // Auto-capture this phase — use video element for a clean frame
                isCapturedRef.current = true;
                captureCleanFrame(videoRef.current).then((blob) => {
                  if (!blob || !mounted) { isCapturedRef.current = false; return; }

                  capturedPhasesRef.current = [
                    ...capturedPhasesRef.current,
                    { phase: phase.id, blob, landmarks },
                  ];

                  setCompletedPhases(prev => [...prev, phaseIdx]);

                  const nextIdx = phaseIdx + 1;
                  if (nextIdx < PHASES.length) {
                    currentPhaseRef.current = nextIdx;
                    setCurrentPhase(nextIdx);
                    holdStartRef.current   = null;
                    setHoldProgress(0);
                    setPoseMatch(false);
                    isCapturedRef.current  = false;
                  } else {
                    // All phases done
                    const all = capturedPhasesRef.current;
                    const front = all.find(c => c.phase === 'front');
                    const mainBlob = front?.blob || all[0]?.blob;
                    setAllDone(true);
                    if (onCaptureRef.current) onCaptureRef.current(mainBlob, all);
                  }
                }, 'image/jpeg', 0.95);
              }
            } else {
              if (!matches) {
                holdStartRef.current = null;
                setHoldProgress(0);
              }
              drawScene(ctx, landmarks, w, h, matches, 0, phase.id);
            }
          } else {
            setFaceDetected(false);
            setIsFaceClose(false);
            setPoseMatch(false);
            holdStartRef.current = null;
            setHoldProgress(0);
          }

          isProcessingRef.current = false;
        });

        faceMeshRef.current = faceMesh;

        const camera = new Camera(videoRef.current, {
          onFrame: async () => {
            if (!mounted || !videoRef.current || isProcessingRef.current) return;
            if (videoRef.current.readyState < 2) return;
            try {
              isProcessingRef.current = true;
              await faceMesh.send({ image: videoRef.current });
            } catch { isProcessingRef.current = false; }
          },
          width: 640,
          height: 480,
        });

        cameraRef.current = camera;
        await camera.start();
        if (mounted) setIsInitialized(true);
      } catch (err) {
        if (mounted) setError(err.message || 'Failed to initialize camera');
      }
    };

    init();

    return () => {
      mounted = false;
      try { cameraRef.current?.stop(); } catch {}
      try { faceMeshRef.current?.close(); } catch {}
    };
  }, []); // stable — never re-runs

  // ── Manual capture (fallback) ──────────────────────────────────────────────
  const manualCapture = () => {
    if (!faceDetected || isCapturedRef.current) return;
    isCapturedRef.current = true;
    const phaseIdx = currentPhaseRef.current;
    captureCleanFrame(videoRef.current).then((blob) => {
      if (!blob) { isCapturedRef.current = false; return; }
      capturedPhasesRef.current = [
        ...capturedPhasesRef.current,
        { phase: PHASES[phaseIdx].id, blob, landmarks: null },
      ];
      setCompletedPhases(prev => [...prev, phaseIdx]);
      const nextIdx = phaseIdx + 1;
      if (nextIdx < PHASES.length) {
        currentPhaseRef.current = nextIdx;
        setCurrentPhase(nextIdx);
        holdStartRef.current  = null;
        setHoldProgress(0);
        setPoseMatch(false);
        isCapturedRef.current = false;
      } else {
        const all = capturedPhasesRef.current;
        const front = all.find(c => c.phase === 'front');
        setAllDone(true);
        if (onCaptureRef.current) onCaptureRef.current(front?.blob || all[0]?.blob, all);
      }
    }, 'image/jpeg', 0.95);
  };

  const skipPhase = () => {
    if (isCapturedRef.current) return;
    isCapturedRef.current = true;
    const phaseIdx = currentPhaseRef.current;
    setCompletedPhases(prev => [...prev, phaseIdx]);
    const nextIdx = phaseIdx + 1;
    if (nextIdx < PHASES.length) {
      currentPhaseRef.current = nextIdx;
      setCurrentPhase(nextIdx);
      holdStartRef.current   = null;
      setHoldProgress(0);
      setPoseMatch(false);
      isCapturedRef.current  = false;
    } else {
      const all = capturedPhasesRef.current;
      const front = all.find(c => c.phase === 'front');
      setAllDone(true);
      if (onCaptureRef.current && all.length > 0) onCaptureRef.current(front?.blob || all[0]?.blob, all);
    }
  };

  // ── Error state ────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--destructive)', fontSize: 15, marginBottom: 8 }}>
          Camera initialisation failed
        </p>
        <p style={{ color: 'var(--muted-foreground)', fontSize: 13 }}>{error}</p>
        <p style={{ color: 'var(--muted-foreground)', fontSize: 13, marginTop: 8 }}>
          Grant camera permissions and refresh the page.
        </p>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  const phase = PHASES[currentPhase];
  const borderColor = allDone
    ? '#10B981'
    : poseMatch
      ? '#10B981'
      : isFaceClose
        ? '#F97316'
        : faceDetected
          ? '#facc15'
          : 'var(--border)';

  // Hold ring SVG (drawn as HTML overlay for smooth animation)
  const RING_R    = 48;
  const RING_CIRC = 2 * Math.PI * RING_R;
  const ringDash  = (holdProgress / 100) * RING_CIRC;

  return (
    <div style={{ width: '100%' }}>
      {/* ── Phase progress dots ── */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 12 }}>
        {PHASES.map((p, i) => (
          <div
            key={p.id}
            title={p.label}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
              cursor: 'default',
            }}
          >
            <div style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: completedPhases.includes(i)
                ? '#10B981'
                : i === currentPhase
                  ? '#F97316'
                  : 'var(--border)',
              transition: 'background 0.3s',
            }} />
          </div>
        ))}
      </div>

      {/* ── Camera canvas ── */}
      <div style={{ position: 'relative', width: '100%' }}>
        <video ref={videoRef} style={{ display: 'none' }} playsInline autoPlay />

        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          style={{
            width: '100%',
            maxWidth: 640,
            display: 'block',
            borderRadius: 6,
            border: `3px solid ${borderColor}`,
            background: '#000',
            transition: 'border-color 0.3s',
          }}
        />

        {/* Hold-progress ring overlay */}
        {poseMatch && holdProgress > 0 && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            pointerEvents: 'none',
          }}>
            <svg width={RING_R * 2 + 12} height={RING_R * 2 + 12}>
              <circle
                cx={RING_R + 6}
                cy={RING_R + 6}
                r={RING_R}
                fill="none"
                stroke="rgba(16,185,129,0.2)"
                strokeWidth={5}
              />
              <circle
                cx={RING_R + 6}
                cy={RING_R + 6}
                r={RING_R}
                fill="none"
                stroke="#10B981"
                strokeWidth={5}
                strokeLinecap="round"
                strokeDasharray={`${ringDash} ${RING_CIRC}`}
                strokeDashoffset={RING_CIRC / 4} /* start at top */
                style={{ filter: 'drop-shadow(0 0 6px #10B981)' }}
              />
            </svg>
          </div>
        )}

        {/* Phase label badge */}
        {!allDone && isInitialized && (
          <div style={{
            position: 'absolute',
            top: 12,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0,0,0,0.65)',
            color: '#fff',
            padding: '4px 14px',
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: 0.5,
            backdropFilter: 'blur(4px)',
            pointerEvents: 'none',
            whiteSpace: 'nowrap',
          }}>
            {phase.emoji} {phase.label} ({currentPhase + 1}/{PHASES.length})
          </div>
        )}

        {/* "initializing" overlay */}
        {!isInitialized && (
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0,0,0,0.5)',
            borderRadius: 6,
            color: '#fff',
            fontSize: 15,
          }}>
            Initialising camera…
          </div>
        )}
      </div>

      {/* ── Status + instructions ── */}
      {isInitialized && !allDone && (
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          {/* Pose status */}
          <p style={{
            fontSize: 14,
            fontWeight: 600,
            color: poseMatch
              ? '#10B981'
              : isFaceClose
                ? '#F97316'
                : faceDetected
                  ? '#facc15'
                  : 'var(--muted-foreground)',
            marginBottom: 4,
          }}>
            {!faceDetected && '✗ No face detected — position yourself in the frame'}
            {faceDetected && !isFaceClose && '⚠ Move closer for better quality'}
            {isFaceClose && !poseMatch && `${phase.emoji} ${phase.instruction}`}
            {poseMatch && holdProgress < 100 && `Hold still… ${Math.round(holdProgress)}%`}
            {poseMatch && holdProgress >= 100 && '✓ Capturing…'}
          </p>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 10 }}>
            <button
              onClick={manualCapture}
              disabled={!faceDetected}
              style={{
                padding: '8px 20px',
                fontSize: 13,
                fontWeight: 600,
                background: faceDetected ? 'var(--primary)' : 'var(--border)',
                color: faceDetected ? 'var(--primary-foreground)' : 'var(--muted-foreground)',
                border: 'none',
                borderRadius: 6,
                cursor: faceDetected ? 'pointer' : 'not-allowed',
              }}
            >
              Capture Now
            </button>
            {currentPhase > 0 && (
              <button
                onClick={skipPhase}
                style={{
                  padding: '8px 16px',
                  fontSize: 13,
                  background: 'transparent',
                  color: 'var(--muted-foreground)',
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
              >
                Skip
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── All done message ── */}
      {allDone && (
        <p style={{ textAlign: 'center', marginTop: 12, color: '#10B981', fontWeight: 600 }}>
          ✓ All {PHASES.length} poses captured successfully
        </p>
      )}
    </div>
  );
};

export default FaceMeshCapture;


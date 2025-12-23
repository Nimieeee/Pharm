"use client";

import React, { useRef, useEffect, useState, useMemo } from "react";

// =============================================================================
// TYPES
// =============================================================================

interface LiquidGlassProps {
    children: React.ReactNode;
    className?: string;
    bezelWidth?: number; // Width of curved edge (px)
    glassThickness?: number; // Optical thickness (affects refraction strength)
    refractiveIndex?: number; // Glass refractive index (1.5 = standard glass)
    highlightIntensity?: number; // Specular highlight brightness (0-1)
    borderRadius?: number; // CSS border radius
    style?: React.CSSProperties;
}

interface DisplacementVector {
    x: number;
    y: number;
}

// =============================================================================
// CHROME DETECTION
// =============================================================================

function isChrome(): boolean {
    if (typeof window === "undefined") return false;
    const userAgent = navigator.userAgent;
    // Check for Chrome but not Edge or other Chromium browsers that might have issues
    return /Chrome/.test(userAgent) && !/Edge|Edg|OPR|Opera/.test(userAgent);
}

// =============================================================================
// REFRACTION PHYSICS
// =============================================================================

/**
 * Calculate the refracted ray direction using Snell's Law
 * n1 * sin(θ1) = n2 * sin(θ2)
 */
function calculateRefraction(
    incidentAngle: number,
    n1: number, // Refractive index of first medium (air = 1)
    n2: number  // Refractive index of second medium (glass ≈ 1.5)
): number {
    const sinTheta1 = Math.sin(incidentAngle);
    const sinTheta2 = (n1 / n2) * sinTheta1;

    // Total internal reflection check
    if (Math.abs(sinTheta2) > 1) {
        return incidentAngle; // Reflect back
    }

    return Math.asin(sinTheta2);
}

/**
 * Surface height function - Convex Squircle (Apple's preferred shape)
 * Smooth transition from flat to curved
 */
function surfaceHeight(t: number): number {
    // t is 0 at edge, 1 at end of bezel
    const clampedT = Math.max(0, Math.min(1, t));
    // Squircle formula: y = (1 - (1-x)^4)^(1/4)
    return Math.pow(1 - Math.pow(1 - clampedT, 4), 0.25);
}

/**
 * Calculate surface normal at a given point (derivative of height function)
 */
function surfaceNormal(t: number): number {
    const delta = 0.001;
    const y1 = surfaceHeight(t - delta);
    const y2 = surfaceHeight(t + delta);
    const derivative = (y2 - y1) / (2 * delta);
    // Normal angle (perpendicular to tangent)
    return Math.atan2(1, -derivative);
}

/**
 * Calculate displacement at a distance from the edge
 */
function calculateDisplacement(
    distanceFromEdge: number,
    bezelWidth: number,
    glassThickness: number,
    refractiveIndex: number
): number {
    if (distanceFromEdge >= bezelWidth) {
        return 0; // Inside flat area, no displacement
    }

    const t = distanceFromEdge / bezelWidth;
    const normal = surfaceNormal(t);
    const incidentAngle = Math.PI / 2 - normal; // Rays come straight down

    const refractedAngle = calculateRefraction(incidentAngle, 1, refractiveIndex);
    const displacement = glassThickness * Math.tan(refractedAngle) * (1 - t);

    return displacement;
}

// =============================================================================
// DISPLACEMENT MAP GENERATOR
// =============================================================================

function generateDisplacementMap(
    width: number,
    height: number,
    bezelWidth: number,
    glassThickness: number,
    refractiveIndex: number,
    borderRadius: number
): { dataUrl: string; maxDisplacement: number } {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d")!;

    const imageData = ctx.createImageData(width, height);
    const data = imageData.data;

    let maxDisplacement = 0;
    const displacements: DisplacementVector[] = [];

    // Calculate displacement for each pixel
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            // Distance from each edge
            const distLeft = x;
            const distRight = width - 1 - x;
            const distTop = y;
            const distBottom = height - 1 - y;

            // Find minimum distance to edge (considering border radius)
            let minDist = Math.min(distLeft, distRight, distTop, distBottom);

            // Handle corners with border radius
            const cornerX = x < borderRadius ? borderRadius - x : (x > width - borderRadius ? x - (width - borderRadius) : 0);
            const cornerY = y < borderRadius ? borderRadius - y : (y > height - borderRadius ? y - (height - borderRadius) : 0);
            if (cornerX > 0 && cornerY > 0) {
                const cornerDist = borderRadius - Math.sqrt(cornerX * cornerX + cornerY * cornerY);
                minDist = Math.max(0, cornerDist);
            }

            // Calculate displacement magnitude
            const displacement = calculateDisplacement(minDist, bezelWidth, glassThickness, refractiveIndex);
            maxDisplacement = Math.max(maxDisplacement, Math.abs(displacement));

            // Calculate direction (toward center)
            const centerX = width / 2;
            const centerY = height / 2;
            const dx = centerX - x;
            const dy = centerY - y;
            const length = Math.sqrt(dx * dx + dy * dy) || 1;

            displacements.push({
                x: (dx / length) * displacement,
                y: (dy / length) * displacement
            });
        }
    }

    // Normalize and encode to RGBA
    for (let i = 0; i < displacements.length; i++) {
        const d = displacements[i];
        const normalizedX = maxDisplacement > 0 ? d.x / maxDisplacement : 0;
        const normalizedY = maxDisplacement > 0 ? d.y / maxDisplacement : 0;

        const idx = i * 4;
        data[idx] = 128 + Math.round(normalizedX * 127);     // Red = X displacement
        data[idx + 1] = 128 + Math.round(normalizedY * 127); // Green = Y displacement
        data[idx + 2] = 128;                                  // Blue = unused
        data[idx + 3] = 255;                                  // Alpha = fully opaque
    }

    ctx.putImageData(imageData, 0, 0);

    return {
        dataUrl: canvas.toDataURL(),
        maxDisplacement
    };
}

/**
 * Generate specular highlight map
 */
function generateHighlightMap(
    width: number,
    height: number,
    bezelWidth: number,
    intensity: number,
    borderRadius: number
): string {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d")!;

    // Create gradient for rim light effect
    const gradient = ctx.createRadialGradient(
        width * 0.3, height * 0.3, 0,
        width * 0.5, height * 0.5, Math.max(width, height) * 0.7
    );

    gradient.addColorStop(0, `rgba(255, 255, 255, ${intensity * 0.4})`);
    gradient.addColorStop(0.3, `rgba(255, 255, 255, ${intensity * 0.1})`);
    gradient.addColorStop(1, "rgba(255, 255, 255, 0)");

    // Draw rounded rectangle
    ctx.beginPath();
    ctx.roundRect(0, 0, width, height, borderRadius);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Add edge highlight
    ctx.strokeStyle = `rgba(255, 255, 255, ${intensity * 0.3})`;
    ctx.lineWidth = 1;
    ctx.stroke();

    return canvas.toDataURL();
}

// =============================================================================
// LIQUID GLASS COMPONENT
// =============================================================================

export default function LiquidGlass({
    children,
    className = "",
    bezelWidth = 20,
    glassThickness = 8,
    refractiveIndex = 1.5,
    highlightIntensity = 0.6,
    borderRadius = 24,
    style = {}
}: LiquidGlassProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
    const [isClient, setIsClient] = useState(false);
    const [useAdvanced, setUseAdvanced] = useState(false);
    const filterId = useRef(`liquid-glass-${Math.random().toString(36).substr(2, 9)}`);

    // Client-side initialization
    useEffect(() => {
        setIsClient(true);
        setUseAdvanced(isChrome());
    }, []);

    // Observe container size
    useEffect(() => {
        if (!containerRef.current || !isClient) return;

        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                setDimensions({ width: Math.ceil(width), height: Math.ceil(height) });
            }
        });

        observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, [isClient]);

    // Generate displacement and highlight maps
    const { displacementMap, highlightMap, maxDisplacement } = useMemo(() => {
        if (!useAdvanced || dimensions.width === 0 || dimensions.height === 0) {
            return { displacementMap: "", highlightMap: "", maxDisplacement: 0 };
        }

        const displacement = generateDisplacementMap(
            dimensions.width,
            dimensions.height,
            bezelWidth,
            glassThickness,
            refractiveIndex,
            borderRadius
        );

        const highlight = generateHighlightMap(
            dimensions.width,
            dimensions.height,
            bezelWidth,
            highlightIntensity,
            borderRadius
        );

        return {
            displacementMap: displacement.dataUrl,
            highlightMap: highlight,
            maxDisplacement: displacement.maxDisplacement
        };
    }, [useAdvanced, dimensions, bezelWidth, glassThickness, refractiveIndex, highlightIntensity, borderRadius]);

    // Fallback CSS class for non-Chrome browsers
    const fallbackClasses = !useAdvanced ? "glass-effect" : "";

    return (
        <>
            {/* SVG Filter Definition (Chrome only) */}
            {useAdvanced && displacementMap && (
                <svg
                    width="0"
                    height="0"
                    style={{ position: "absolute", visibility: "hidden" }}
                    colorInterpolationFilters="sRGB"
                >
                    <defs>
                        <filter
                            id={filterId.current}
                            x="0"
                            y="0"
                            width="100%"
                            height="100%"
                            filterUnits="userSpaceOnUse"
                            primitiveUnits="userSpaceOnUse"
                        >
                            {/* Displacement Map */}
                            <feImage
                                href={displacementMap}
                                x="0"
                                y="0"
                                width={dimensions.width}
                                height={dimensions.height}
                                result="dispMap"
                                preserveAspectRatio="none"
                            />

                            {/* Apply Displacement */}
                            <feDisplacementMap
                                in="SourceGraphic"
                                in2="dispMap"
                                scale={maxDisplacement * 0.8}
                                xChannelSelector="R"
                                yChannelSelector="G"
                                result="displaced"
                            />

                            {/* Highlight Overlay */}
                            <feImage
                                href={highlightMap}
                                x="0"
                                y="0"
                                width={dimensions.width}
                                height={dimensions.height}
                                result="highlight"
                                preserveAspectRatio="none"
                            />

                            {/* Blend highlight with displaced content */}
                            <feBlend
                                in="displaced"
                                in2="highlight"
                                mode="screen"
                                result="final"
                            />
                        </filter>
                    </defs>
                </svg>
            )}

            {/* Container */}
            <div
                ref={containerRef}
                className={`${className} ${fallbackClasses}`}
                style={{
                    ...style,
                    borderRadius,
                    ...(useAdvanced && displacementMap ? {
                        backdropFilter: `url(#${filterId.current})`,
                        WebkitBackdropFilter: `url(#${filterId.current})`,
                    } : {})
                }}
            >
                {children}
            </div>
        </>
    );
}

// =============================================================================
// SIMPLIFIED PRESET COMPONENTS
// =============================================================================

export function LiquidGlassCard({
    children,
    className = "",
    ...props
}: Omit<LiquidGlassProps, "bezelWidth" | "glassThickness">) {
    return (
        <LiquidGlass
            className={className}
            bezelWidth={16}
            glassThickness={6}
            refractiveIndex={1.45}
            highlightIntensity={0.5}
            borderRadius={20}
            {...props}
        >
            {children}
        </LiquidGlass>
    );
}

export function LiquidGlassNavbar({
    children,
    className = "",
    ...props
}: Omit<LiquidGlassProps, "bezelWidth" | "glassThickness">) {
    return (
        <LiquidGlass
            className={className}
            bezelWidth={12}
            glassThickness={4}
            refractiveIndex={1.4}
            highlightIntensity={0.4}
            borderRadius={9999} // Pill shape
            {...props}
        >
            {children}
        </LiquidGlass>
    );
}

export function LiquidGlassPanel({
    children,
    className = "",
    ...props
}: Omit<LiquidGlassProps, "bezelWidth" | "glassThickness">) {
    return (
        <LiquidGlass
            className={className}
            bezelWidth={24}
            glassThickness={10}
            refractiveIndex={1.5}
            highlightIntensity={0.6}
            borderRadius={28}
            {...props}
        >
            {children}
        </LiquidGlass>
    );
}

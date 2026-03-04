"use client";
import { motion } from "framer-motion";
export default function StreamingLogo({ className = "inline-block w-5 h-5 ml-1 align-text-bottom" }: { className?: string }) {
  // Exact Benchside brand orange
  const brandOrange = "#D7712A";
  // 4x4 Grid Coordinates mapped to a 100x100 viewBox
  const gridPoints = [
    { cx: 20, cy: 20 }, { cx: 40, cy: 20 }, { cx: 60, cy: 20 }, { cx: 80, cy: 20 },
    { cx: 20, cy: 40 }, { cx: 40, cy: 40 }, { cx: 60, cy: 40 }, { cx: 80, cy: 40 },
    { cx: 20, cy: 60 }, { cx: 40, cy: 60 }, { cx: 60, cy: 60 }, { cx: 80, cy: 60 },
    { cx: 20, cy: 80 }, { cx: 40, cy: 80 }, { cx: 60, cy: 80 }, { cx: 80, cy: 80 },
  ];
  return (
    <div className={className}>
      <motion.svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* The Bonds (Connecting Lines) */}
        <motion.g
          stroke={brandOrange}
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {/* Main Diagonal Branch */}
          <motion.path
            d="M 20 20 L 40 40 L 40 60 L 60 60 L 80 80"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
              repeatType: "reverse",
            }}
          />
          {/* Side Branch 1 */}
          <motion.path
            d="M 40 40 L 60 20"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
              repeatType: "reverse",
              delay: 0.3,
            }}
          />
          {/* Side Branch 2 */}
          <motion.path
            d="M 60 60 L 80 40"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
              repeatType: "reverse",
              delay: 0.6,
            }}
          />
        </motion.g>
        {/* The Nodes (Dots) */}
        {gridPoints.map((point, index) => (
          <motion.circle
            key={index}
            cx={point.cx}
            cy={point.cy}
            r="5"
            fill={brandOrange}
            animate={{
              opacity: [0.3, 1, 0.3],
              scale: [0.8, 1.2, 0.8],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
              // The delay creates a cascading wave effect across the grid
              delay: index * 0.05,
            }}
          />
        ))}
      </motion.svg>
    </div>
  );
}
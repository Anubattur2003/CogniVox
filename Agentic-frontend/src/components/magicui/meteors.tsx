import { cn } from "../../lib/utils";

interface MeteorsProps {
  number?: number;
  minDelay?: number;
  maxDelay?: number;
  minDuration?: number;
  maxDuration?: number;
  angle?: number;
  className?: string;
}

export const Meteors = ({
  number = 20,
  minDelay = 0.2,
  maxDelay = 1.2,
  minDuration = 2,
  maxDuration = 10,
  angle = 215,
  className,
}: MeteorsProps) => {
  const meteors = new Array(number || 20).fill(true);

  return (
    <div className={cn("absolute inset-0 w-full h-full overflow-hidden", className)}>
      {meteors.map((_, idx) => (
        <span
          key={idx}
          className={cn(
            "absolute h-0.5 w-0.5 animate-meteor-effect rounded-[9999px] bg-slate-500 shadow-[0_0_0_1px_#ffffff10]",
            "before:content-[''] before:absolute before:top-1/2 before:transform before:-translate-y-1/2 before:w-[50px] before:h-[1px] before:bg-gradient-to-r before:from-[#64748b] before:to-transparent"
          )}
          style={{
            top: Math.random() * -200 + "px",
            left: Math.random() * 120 + "%",
            animationDelay: Math.random() * (maxDelay - minDelay) + minDelay + "s",
            animationDuration: Math.floor(Math.random() * (maxDuration - minDuration) + minDuration) + "s",
            transform: `rotate(${angle}deg)`,
          }}
        ></span>
      ))}
    </div>
  );
};

export default Meteors; 
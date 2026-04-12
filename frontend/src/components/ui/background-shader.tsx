import { MeshGradient } from "@paper-design/shaders-react";
import type { CSSProperties, ReactNode } from "react";

type BackgroundShaderLayerProps = {
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
};

function BackgroundShaderLayer({ className = "", style, children }: BackgroundShaderLayerProps) {
  return (
    <div className={`absolute inset-0 overflow-hidden ${className}`.trim()} style={style}>
      <div className="absolute inset-0 bg-[linear-gradient(135deg,#5f94dd_0%,#4f85d3_20%,#3c6bc6_42%,#4f90de_76%,#70ade8_100%)]" />
      <div className="absolute -left-[20%] top-[-8%] h-[150%] w-[82%] rounded-full bg-[radial-gradient(circle_at_70%_52%,rgba(20,46,145,1)_0%,rgba(27,60,176,0.98)_34%,rgba(57,120,223,0.86)_49%,rgba(120,200,255,0.52)_59%,rgba(120,200,255,0.12)_67%,transparent_74%)] blur-[5px]" />
      <div className="absolute left-[45%] top-[10%] h-[90%] w-[18%] rounded-full bg-[radial-gradient(circle_at_30%_50%,rgba(154,223,255,0.58)_0%,rgba(154,223,255,0.22)_40%,rgba(154,223,255,0.06)_54%,transparent_66%)] blur-[9px]" />
      <div className="absolute right-[-10%] top-[-18%] h-[70%] w-[44%] rounded-full bg-[radial-gradient(circle_at_35%_50%,rgba(255,255,255,0.12)_0%,rgba(255,255,255,0.04)_42%,transparent_66%)] blur-[14px]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_16%_18%,rgba(255,255,255,0.06),transparent_13%),radial-gradient(circle_at_86%_20%,rgba(255,255,255,0.05),transparent_13%)]" />

      <div className="absolute inset-[-8%] scale-[1.06] opacity-[0.12] mix-blend-overlay">
        <MeshGradient
          style={{ height: "100%", width: "100%" }}
          distortion={0.62}
          swirl={0.04}
          offsetX={-0.04}
          offsetY={0}
          scale={1}
          rotation={-4}
          speed={0.5}
          colors={[
            "hsl(221, 72%, 58%)",
            "hsl(228, 65%, 46%)",
            "hsl(202, 83%, 69%)",
            "hsl(215, 63%, 58%)",
          ]}
        />
      </div>
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(7,17,36,0.04),rgba(4,10,22,0.18))]" />
      {children}
    </div>
  );
}

export default function Waitlist() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="fixed inset-0 z-0">
        <MeshGradient
          style={{ height: "100vh", width: "100vw" }}
          distortion={0.8}
          swirl={0.1}
          offsetX={0}
          offsetY={0}
          scale={1}
          rotation={0}
          speed={1}
          colors={[
            "hsl(216, 90%, 27%)",
            "hsl(243, 68%, 36%)",
            "hsl(205, 91%, 64%)",
            "hsl(211, 61%, 57%)",
          ]}
        />
      </div>

      <div className="relative z-10">
        <main className="my-0 flex min-h-screen items-center justify-center p-4">
          <div className="mx-auto w-full max-w-2xl space-y-8 text-center">
            <div className="font-sans text-4xl font-bold tracking-tight text-white drop-shadow-2xl md:text-6xl">
              <h1 className="py-[23px] text-4xl font-semibold tracking-tight text-white drop-shadow-2xl md:text-6xl">
                We are launching SickUI soon!
              </h1>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export { BackgroundShaderLayer };

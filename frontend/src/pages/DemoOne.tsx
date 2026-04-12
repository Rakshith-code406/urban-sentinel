import RippleButton from "@/components/ui/ripple-button";

export default function DemoOne() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-white">
      <div className="flex flex-col gap-6 items-center">
        <RippleButton onClick={() => alert('Button clicked!')}>Click Me</RippleButton>
      </div>
    </div>
  );
}

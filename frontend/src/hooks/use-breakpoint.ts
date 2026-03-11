import * as React from "react";

export type Breakpoint = "sm" | "md" | "lg";

const MD_BREAKPOINT = 768;
const LG_BREAKPOINT = 1024;

export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = React.useState<Breakpoint>("lg");

  React.useEffect(() => {
    function compute(): Breakpoint {
      const w = window.innerWidth;
      if (w < MD_BREAKPOINT) return "sm";
      if (w < LG_BREAKPOINT) return "md";
      return "lg";
    }

    const update = () => setBreakpoint(compute());

    const mdMql = window.matchMedia(`(max-width: ${MD_BREAKPOINT - 1}px)`);
    const lgMql = window.matchMedia(`(max-width: ${LG_BREAKPOINT - 1}px)`);

    mdMql.addEventListener("change", update);
    lgMql.addEventListener("change", update);
    update();

    return () => {
      mdMql.removeEventListener("change", update);
      lgMql.removeEventListener("change", update);
    };
  }, []);

  return breakpoint;
}

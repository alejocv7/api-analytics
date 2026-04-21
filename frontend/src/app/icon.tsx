import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "#4f46e5",
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: "8px",
        }}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 3v16a2 2 0 0 0 2 2h16" />
          <rect x="7" y="5" width="2" height="12" fill="white" stroke="none" />
          <rect x="12" y="9" width="2" height="8" fill="white" stroke="none" />
          <rect x="17" y="13" width="2" height="4" fill="white" stroke="none" />
        </svg>
      </div>
    ),
    { ...size },
  );
}

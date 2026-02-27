"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Granularity } from "@/types/api";

const options: { value: Granularity; label: string }[] = [
  { value: "minute", label: "Per minute" },
  { value: "hour", label: "Per hour" },
  { value: "day", label: "Per day" },
];

interface GranularitySelectProps {
  value: Granularity;
  onChange: (value: Granularity) => void;
}

export function GranularitySelect({ value, onChange }: GranularitySelectProps) {
  return (
    <Select value={value} onValueChange={(v) => onChange(v as Granularity)}>
      <SelectTrigger className="h-9 w-36">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

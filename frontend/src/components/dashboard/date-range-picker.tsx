"use client";

import { useState } from "react";
import { format, subDays, subHours } from "date-fns";
import { CalendarIcon, ChevronDown } from "lucide-react";
import { DateRange } from "react-day-picker";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DATE_PRESETS, MAX_DATE_RANGE_DAYS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export interface DateRangeValue {
  startTime: Date;
  endTime: Date;
}

interface DateRangePickerProps {
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
  className?: string;
}

export function DateRangePicker({ value, onChange }: DateRangePickerProps) {
  const [open, setOpen] = useState(false);
  const [calendarRange, setCalendarRange] = useState<DateRange | undefined>({
    from: value.startTime,
    to: value.endTime,
  });

  function applyPreset(hours: number) {
    const end = new Date();
    const start = subHours(end, hours);
    onChange({ startTime: start, endTime: end });
    setCalendarRange({ from: start, to: end });
    setOpen(false);
  }

  function applyCalendarRange() {
    if (calendarRange?.from && calendarRange?.to) {
      const diffDays =
        (calendarRange.to.getTime() - calendarRange.from.getTime()) / 86400000;
      if (diffDays > MAX_DATE_RANGE_DAYS) return;
      onChange({ startTime: calendarRange.from, endTime: calendarRange.to });
      setOpen(false);
    }
  }

  function getEndMonth() {
    const now = new Date();
    if (!calendarRange?.to) return now;

    const isCurrentMonth =
      calendarRange.to.getUTCMonth() === now.getUTCMonth() &&
      calendarRange.to.getUTCFullYear() === now.getUTCFullYear();

    if (isCurrentMonth) return now;

    return new Date(
      calendarRange.to.getUTCFullYear(),
      calendarRange.to.getUTCMonth() + 1,
    );
  }

  const label = `${format(value.startTime, "MMM d, yyyy")} – ${format(value.endTime, "MMM d, yyyy")}`;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="h-9 gap-2 font-normal w-full sm:w-auto"
        >
          <CalendarIcon className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">{label}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex">
          {/* Preset sidebar */}
          <div className="border-r border-border p-3 space-y-1 w-auto max-w-[140px]">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-tight mb-2">
              Presets
            </p>
            {DATE_PRESETS.map((preset) => (
              <Button
                key={preset.label}
                variant="ghost"
                size="sm"
                onClick={() => applyPreset(preset.hours)}
                className="w-full justify-start font-normal"
              >
                {preset.label}
              </Button>
            ))}
          </div>

          {/* Calendar */}
          <div className="p-3">
            <Calendar
              mode="range"
              selected={calendarRange}
              onSelect={setCalendarRange}
              numberOfMonths={2}
              endMonth={getEndMonth()}
              disabled={{ after: new Date() }}
            />
            <div className="flex justify-end pt-2 border-t border-border mt-2">
              <Button
                size="sm"
                onClick={applyCalendarRange}
                disabled={!calendarRange?.from || !calendarRange?.to}
              >
                Apply
              </Button>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

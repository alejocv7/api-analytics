import {
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SearchInput } from "@/components/shared/search-input";

interface SearchableCardHeaderProps {
  title: string;
  description: string;
  search: {
    value: string;
    onChange: (value: string) => void;
    placeholder: string;
  };
  action?: React.ReactNode;
}

export function SearchableCardHeader({
  title,
  description,
  search,
  action,
}: SearchableCardHeaderProps) {
  return (
    <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-1">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </div>
      <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
        <SearchInput
          placeholder={search.placeholder}
          value={search.value}
          onChange={search.onChange}
        />
        {action}
      </div>
    </CardHeader>
  );
}

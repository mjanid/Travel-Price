"use client";

import { useState } from "react";
import { Combobox } from "@/components/ui/combobox";
import { useAirportSearch } from "@/hooks/use-airport-search";

interface AirportSearchProps {
  label: string;
  value: string;
  onChange: (code: string) => void;
  placeholder?: string;
  error?: string;
}

export function AirportSearch({
  label,
  value,
  onChange,
  placeholder = "JFK",
  error,
}: AirportSearchProps) {
  const [query, setQuery] = useState(value);
  const results = useAirportSearch(query);

  const options = results.map((a) => ({
    value: a.code,
    label: `${a.name}, ${a.city}`,
    description: a.country,
  }));

  return (
    <Combobox
      label={label}
      value={value}
      options={options}
      onChange={onChange}
      onQueryChange={setQuery}
      placeholder={placeholder}
      error={error}
    />
  );
}

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { classNames } from "@/lib/utils";

interface ComboboxOption {
  value: string;
  label: string;
  description?: string;
}

interface ComboboxProps {
  label: string;
  value: string;
  options: ComboboxOption[];
  onChange: (value: string) => void;
  onQueryChange: (query: string) => void;
  placeholder?: string;
  error?: string;
}

export function Combobox({
  label,
  value,
  options,
  onChange,
  onQueryChange,
  placeholder,
  error,
}: ComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState(value);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const inputId = label.toLowerCase().replace(/\s+/g, "-");

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const item = listRef.current.children[activeIndex] as HTMLElement;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  const handleSelect = useCallback(
    (opt: ComboboxOption) => {
      onChange(opt.value);
      setInputValue(opt.value);
      setIsOpen(false);
      setActiveIndex(-1);
    },
    [onChange],
  );

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value.toUpperCase();
    setInputValue(v);
    onQueryChange(v);
    setIsOpen(true);
    setActiveIndex(-1);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!isOpen && e.key === "ArrowDown") {
      setIsOpen(true);
      return;
    }

    if (!isOpen) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, options.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex >= 0 && options[activeIndex]) {
          handleSelect(options[activeIndex]);
        }
        break;
      case "Escape":
        setIsOpen(false);
        setActiveIndex(-1);
        break;
    }
  }

  function handleBlur() {
    // If the input value matches a valid option, auto-select it
    const match = options.find(
      (o) => o.value.toUpperCase() === inputValue.toUpperCase(),
    );
    if (match) {
      onChange(match.value);
    } else if (inputValue.length === 3) {
      // Allow raw 3-letter codes even if not in our dataset
      onChange(inputValue.toUpperCase());
    }
  }

  function highlightMatch(text: string, query: string) {
    if (!query) return text;
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return text;
    return (
      <>
        {text.slice(0, idx)}
        <span className="font-semibold text-primary">
          {text.slice(idx, idx + query.length)}
        </span>
        {text.slice(idx + query.length)}
      </>
    );
  }

  return (
    <div ref={containerRef} className="relative space-y-1">
      <label
        htmlFor={inputId}
        className="block text-sm font-medium text-foreground"
      >
        {label}
      </label>
      <input
        ref={inputRef}
        id={inputId}
        type="text"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-autocomplete="list"
        aria-controls={`${inputId}-listbox`}
        aria-activedescendant={
          activeIndex >= 0 ? `${inputId}-option-${activeIndex}` : undefined
        }
        className={classNames(
          "block w-full rounded-lg border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1",
          error
            ? "border-danger focus:ring-danger"
            : "border-border bg-input-bg focus:border-primary",
        )}
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => inputValue && setIsOpen(true)}
        onBlur={handleBlur}
        placeholder={placeholder}
        maxLength={3}
        autoComplete="off"
      />

      {isOpen && options.length > 0 && (
        <ul
          ref={listRef}
          id={`${inputId}-listbox`}
          role="listbox"
          className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-border bg-white shadow-lg"
        >
          {options.map((opt, idx) => (
            <li
              key={opt.value}
              id={`${inputId}-option-${idx}`}
              role="option"
              aria-selected={activeIndex === idx}
              className={classNames(
                "cursor-pointer px-3 py-2 text-sm",
                activeIndex === idx
                  ? "bg-primary text-white"
                  : "text-foreground hover:bg-card-hover",
              )}
              onMouseDown={(e) => {
                e.preventDefault();
                handleSelect(opt);
              }}
              onMouseEnter={() => setActiveIndex(idx)}
            >
              <span className="font-medium">
                {highlightMatch(opt.value, inputValue)}
              </span>
              {opt.label && (
                <span
                  className={classNames(
                    "ml-2",
                    activeIndex === idx ? "text-white/80" : "text-muted",
                  )}
                >
                  {highlightMatch(opt.label, inputValue)}
                </span>
              )}
              {opt.description && (
                <span
                  className={classNames(
                    "ml-1 text-xs",
                    activeIndex === idx ? "text-white/60" : "text-muted",
                  )}
                >
                  ({opt.description})
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {isOpen && inputValue.length > 0 && options.length === 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-muted shadow-lg">
          No airports found
        </div>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  );
}

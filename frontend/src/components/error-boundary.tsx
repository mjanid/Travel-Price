"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="mx-auto mt-8 max-w-md">
          <Card>
            <h2 className="text-lg font-semibold text-danger">
              Something went wrong
            </h2>
            <p className="mt-2 text-sm text-muted">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <Button
              className="mt-4"
              variant="secondary"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try again
            </Button>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * ErrorBoundary component for graceful error handling.
 *
 * Catches React render errors and displays fallback UI instead of crashing.
 * Useful for production environments where component errors shouldn't break the entire app.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <YourComponent />
 *   </ErrorBoundary>
 *
 * Custom fallback:
 *   <ErrorBoundary fallback={<div>Custom error message</div>}>
 *     <YourComponent />
 *   </ErrorBoundary>
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so next render shows fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    // Log error to console (could also send to error tracking service)
    console.error("ErrorBoundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided, otherwise show default
      return (
        this.props.fallback || (
          <div className="card" style={{ textAlign: "center", padding: "40px" }}>
            <h2>Something went wrong</h2>
            <p style={{ color: "#666", marginBottom: "20px" }}>
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <button
              className="button"
              onClick={() => window.location.reload()}
              style={{ fontSize: "16px", padding: "10px 20px" }}
            >
              Reload Page
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

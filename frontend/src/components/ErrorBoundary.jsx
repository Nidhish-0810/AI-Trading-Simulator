import { Component } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

/**
 * React Error Boundary — catches render errors in child components
 * and shows a friendly fallback UI instead of crashing the whole page.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card p-8 flex flex-col items-center gap-4 text-center">
          <div className="w-14 h-14 rounded-full bg-loss/10 border border-loss/20 flex items-center justify-center">
            <AlertTriangle className="text-loss" size={28} />
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg mb-1">
              {this.props.title || 'Something went wrong'}
            </h3>
            <p className="text-white/50 text-sm max-w-sm">
              {this.props.message ||
                'This section encountered an error. Your data is safe — try refreshing.'}
            </p>
            {import.meta.env.DEV && this.state.error && (
              <pre className="mt-3 text-xs text-loss/70 bg-loss/5 rounded-lg p-3 text-left overflow-auto max-w-xs">
                {this.state.error.message}
              </pre>
            )}
          </div>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/8 text-white/70 hover:text-white hover:bg-white/12 transition-all text-sm font-medium"
          >
            <RefreshCw size={14} /> Try Again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

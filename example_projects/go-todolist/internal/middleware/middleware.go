package middleware

import (
	"encoding/json"
	"log"
	"net/http"
	"runtime/debug"
	"strings"
	"time"
)

// ResponseWriterWrapper wraps http.ResponseWriter to capture status code
type ResponseWriterWrapper struct {
	http.ResponseWriter
	StatusCode int
	Body       []byte
}

// NewResponseWriterWrapper creates a new ResponseWriterWrapper
func NewResponseWriterWrapper(w http.ResponseWriter) *ResponseWriterWrapper {
	return &ResponseWriterWrapper{
		ResponseWriter: w,
		StatusCode:     http.StatusOK,
	}
}

// WriteHeader captures the status code
func (rw *ResponseWriterWrapper) WriteHeader(code int) {
	rw.StatusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Write captures the response body
func (rw *ResponseWriterWrapper) Write(b []byte) (int, error) {
	rw.Body = append(rw.Body, b...)
	return rw.ResponseWriter.Write(b)
}

// LoggingMiddleware logs HTTP requests and responses
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		
		// Wrap the response writer to capture status code and body
		ww := NewResponseWriterWrapper(w)
		
		// Call the next handler
		next.ServeHTTP(ww, r)
		
		duration := time.Since(start)
		
		// Log the request details
		log.Printf(
			"%s %s %d %s %s",
			r.Method,
			r.URL.Path,
			ww.StatusCode,
			duration.String(),
			r.RemoteAddr,
		)
	})
}

// CORSMiddleware handles Cross-Origin Resource Sharing
func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		
		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

// JSONContentTypeMiddleware sets the Content-Type header to application/json
func JSONContentTypeMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		next.ServeHTTP(w, r)
	})
}

// ErrorResponse represents a standardized error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
	Code    int    `json:"code"`
}

// RecoveryMiddleware recovers from panics and returns a 500 error
func RecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				log.Printf("panic recovered: %v\n%s", err, debug.Stack())
				
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusInternalServerError)
				
				errorResponse := ErrorResponse{
					Error:   "Internal Server Error",
					Message: "An unexpected error occurred",
					Code:    http.StatusInternalServerError,
				}
				
				if err := json.NewEncoder(w).Encode(errorResponse); err != nil {
					log.Printf("failed to encode error response: %v", err)
				}
			}
		}()
		
		next.ServeHTTP(w, r)
	})
}

// AuthMiddleware is a placeholder for authentication middleware
// In a real application, this would validate JWT tokens or other auth mechanisms
func AuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip auth for OPTIONS requests and health check endpoints
		if r.Method == "OPTIONS" || strings.HasPrefix(r.URL.Path, "/health") {
			next.ServeHTTP(w, r)
			return
		}
		
		// TODO: Implement proper authentication logic
		// For now, this is a placeholder that allows all requests
		// In a real application, you would:
		// 1. Extract token from Authorization header
		// 2. Validate the token
		// 3. Set user context in the request
		
		next.ServeHTTP(w, r)
	})
}

// RateLimitMiddleware is a placeholder for rate limiting
// In a real application, this would implement proper rate limiting logic
func RateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// TODO: Implement rate limiting logic
		// This could use a token bucket algorithm, fixed window, or sliding window
		// For now, this is a placeholder that allows all requests
		
		next.ServeHTTP(w, r)
	})
}

// RequestIDMiddleware adds a unique request ID to each request
func RequestIDMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Generate a simple request ID (in production, use a proper UUID generator)
		requestID := time.Now().Format("20060102150405.000000")
		
		// Add request ID to response headers
		w.Header().Set("X-Request-ID", requestID)
		
		next.ServeHTTP(w, r)
	})
}

// TimeoutMiddleware sets a timeout for request processing
func TimeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			http.TimeoutHandler(next, timeout, "Request timeout").ServeHTTP(w, r)
		})
	}
}

// HealthCheckMiddleware handles health check requests
func HealthCheckMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" && r.Method == "GET" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(map[string]string{
				"status": "healthy",
				"time":   time.Now().Format(time.RFC3339),
			})
			return
		}
		
		next.ServeHTTP(w, r)
	})
}
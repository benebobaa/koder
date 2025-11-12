package router

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	"github.com/yourusername/todo-api/internal/handler"
	"github.com/yourusername/todo-api/internal/middleware"
)

// RouterConfig holds configuration for the router
type RouterConfig struct {
	TodoHandler *handler.TodoHandler
	EnableCORS  bool
	EnableDebug bool
}

// NewRouter creates a new HTTP router with all routes configured
func NewRouter(config *RouterConfig) http.Handler {
	r := chi.NewRouter()

	// Add core middleware
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Recoverer)
	
	// Add custom logging middleware
	r.Use(custom_middleware.LoggingMiddleware)
	
	// Add CORS middleware if enabled
	if config.EnableCORS {
		r.Use(cors.Handler(cors.Options{
			AllowedOrigins:   []string{"https://*", "http://*"},
			AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
			AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
			ExposedHeaders:   []string{"Link"},
			AllowCredentials: false,
			MaxAge:           300,
		}))
	}

	// Health check endpoint
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status": "ok", "message": "Todo API is running"}`))
	})

	// API routes
	r.Route("/api/v1", func(r chi.Router) {
		// Todo routes
		r.Route("/todos", func(r chi.Router) {
			// GET /api/v1/todos - Get all todos
			r.Get("/", config.TodoHandler.GetAllTodos)
			
			// POST /api/v1/todos - Create a new todo
			r.Post("/", config.TodoHandler.CreateTodo)
			
			// Routes that require a todo ID
			r.Route("/{id}", func(r chi.Router) {
				// GET /api/v1/todos/{id} - Get a specific todo
				r.Get("/", config.TodoHandler.GetTodo)
				
				// PUT /api/v1/todos/{id} - Update a todo
				r.Put("/", config.TodoHandler.UpdateTodo)
				
				// DELETE /api/v1/todos/{id} - Delete a todo
				r.Delete("/", config.TodoHandler.DeleteTodo)
			})
		})
	})

	// Add debug endpoints if enabled
	if config.EnableDebug {
		r.Mount("/debug", middleware.Profiler())
	}

	// Add custom error handling middleware
	r.Use(custom_middleware.ErrorHandlingMiddleware)

	return r
}

// NewRouterConfig creates a new router configuration
func NewRouterConfig(todoHandler *handler.TodoHandler) *RouterConfig {
	return &RouterConfig{
		TodoHandler: todoHandler,
		EnableCORS:  true,
		EnableDebug: false,
	}
}
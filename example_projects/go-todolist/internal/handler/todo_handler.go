package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"

	"github.com/todo-app/internal/models"
	"github.com/todo-app/internal/service"
)

// TodoHandler handles HTTP requests for todo operations
type TodoHandler struct {
	todoService *service.TodoService
}

// NewTodoHandler creates a new TodoHandler instance
func NewTodoHandler(todoService *service.TodoService) *TodoHandler {
	return &TodoHandler{
		todoService: todoService,
	}
}

// CreateTodo handles POST /todos requests
func (h *TodoHandler) CreateTodo(w http.ResponseWriter, r *http.Request) {
	var req models.CreateTodoRequest
	
	// Decode request body
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Validate request
	if validationErrors := req.Validate(); len(validationErrors) > 0 {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"error": "Validation failed",
			"details": validationErrors,
		})
		return
	}
	
	// Create todo
	todo, err := h.todoService.CreateTodo(r.Context(), &req)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to create todo: %v", err), http.StatusInternalServerError)
		return
	}
	
	// Return created todo
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(todo)
}

// GetTodo handles GET /todos/{id} requests
func (h *TodoHandler) GetTodo(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL parameters
	vars := mux.Vars(r)
	idStr := vars["id"]
	
	// Parse ID
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		http.Error(w, "Invalid todo ID", http.StatusBadRequest)
		return
	}
	
	// Get todo
	todo, err := h.todoService.GetTodo(r.Context(), id)
	if err != nil {
		if err == service.ErrTodoNotFound {
			http.Error(w, "Todo not found", http.StatusNotFound)
			return
		}
		http.Error(w, fmt.Sprintf("Failed to get todo: %v", err), http.StatusInternalServerError)
		return
	}
	
	// Return todo
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(todo)
}

// GetAllTodos handles GET /todos requests
func (h *TodoHandler) GetAllTodos(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	query := r.URL.Query()
	completedParam := query.Get("completed")
	
	var completed *bool
	if completedParam != "" {
		completedBool, err := strconv.ParseBool(completedParam)
		if err != nil {
			http.Error(w, "Invalid completed parameter", http.StatusBadRequest)
			return
		}
		completed = &completedBool
	}
	
	// Get all todos
	todos, err := h.todoService.GetAllTodos(r.Context(), completed)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get todos: %v", err), http.StatusInternalServerError)
		return
	}
	
	// Return todos
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"todos": todos,
		"count": len(todos),
	})
}

// UpdateTodo handles PUT /todos/{id} requests
func (h *TodoHandler) UpdateTodo(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL parameters
	vars := mux.Vars(r)
	idStr := vars["id"]
	
	// Parse ID
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		http.Error(w, "Invalid todo ID", http.StatusBadRequest)
		return
	}
	
	var req models.UpdateTodoRequest
	
	// Decode request body
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	// Validate request
	if validationErrors := req.Validate(); len(validationErrors) > 0 {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"error": "Validation failed",
			"details": validationErrors,
		})
		return
	}
	
	// Update todo
	todo, err := h.todoService.UpdateTodo(r.Context(), id, &req)
	if err != nil {
		if err == service.ErrTodoNotFound {
			http.Error(w, "Todo not found", http.StatusNotFound)
			return
		}
		http.Error(w, fmt.Sprintf("Failed to update todo: %v", err), http.StatusInternalServerError)
		return
	}
	
	// Return updated todo
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(todo)
}

// DeleteTodo handles DELETE /todos/{id} requests
func (h *TodoHandler) DeleteTodo(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL parameters
	vars := mux.Vars(r)
	idStr := vars["id"]
	
	// Parse ID
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		http.Error(w, "Invalid todo ID", http.StatusBadRequest)
		return
	}
	
	// Delete todo
	err = h.todoService.DeleteTodo(r.Context(), id)
	if err != nil {
		if err == service.ErrTodoNotFound {
			http.Error(w, "Todo not found", http.StatusNotFound)
			return
		}
		http.Error(w, fmt.Sprintf("Failed to delete todo: %v", err), http.StatusInternalServerError)
		return
	}
	
	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNoContent)
}

// HealthCheck handles GET /health requests
func (h *TodoHandler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"timestamp": "todo-app",
	})
}
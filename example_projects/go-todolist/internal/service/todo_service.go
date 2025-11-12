package service

import (
	"context"
	"errors"
	"time"

	"github.com/yourusername/todo-api/internal/models"
)

// TodoService defines the interface for todo business logic operations
type TodoService interface {
	// CreateTodo creates a new todo item
	CreateTodo(ctx context.Context, req *models.CreateTodoRequest) (*models.Todo, error)
	
	// GetTodo retrieves a todo by its ID
	GetTodo(ctx context.Context, id int64) (*models.Todo, error)
	
	// GetAllTodos retrieves all todos with optional filtering
	GetAllTodos(ctx context.Context, completed *bool) ([]models.Todo, error)
	
	// UpdateTodo updates an existing todo
	UpdateTodo(ctx context.Context, id int64, req *models.UpdateTodoRequest) (*models.Todo, error)
	
	// DeleteTodo removes a todo from the system
	DeleteTodo(ctx context.Context, id int64) error
}

// todoServiceImpl is the concrete implementation of TodoService
type todoServiceImpl struct {
	repo models.TodoRepository
}

// NewTodoService creates a new instance of TodoService
func NewTodoService(repo models.TodoRepository) TodoService {
	return &todoServiceImpl{
		repo: repo,
	}
}

// CreateTodo creates a new todo item with validation
func (s *todoServiceImpl) CreateTodo(ctx context.Context, req *models.CreateTodoRequest) (*models.Todo, error) {
	// Validate the request
	if validationErrors := req.Validate(); len(validationErrors) > 0 {
		return nil, &ValidationError{
			Errors: validationErrors,
		}
	}

	// Create the todo via repository
	todo, err := s.repo.Create(req)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

// GetTodo retrieves a todo by its ID
func (s *todoServiceImpl) GetTodo(ctx context.Context, id int64) (*models.Todo, error) {
	// Validate ID
	if id <= 0 {
		return nil, ErrInvalidID
	}

	// Get todo from repository
	todo, err := s.repo.GetByID(id)
	if err != nil {
		return nil, err
	}

	// Check if todo exists
	if todo == nil {
		return nil, ErrTodoNotFound
	}

	return todo, nil
}

// GetAllTodos retrieves all todos with optional filtering
func (s *todoServiceImpl) GetAllTodos(ctx context.Context, completed *bool) ([]models.Todo, error) {
	// Get todos from repository
	todos, err := s.repo.GetAll(completed)
	if err != nil {
		return nil, err
	}

	// Return empty slice instead of nil for consistency
	if todos == nil {
		todos = []models.Todo{}
	}

	return todos, nil
}

// UpdateTodo updates an existing todo
func (s *todoServiceImpl) UpdateTodo(ctx context.Context, id int64, req *models.UpdateTodoRequest) (*models.Todo, error) {
	// Validate ID
	if id <= 0 {
		return nil, ErrInvalidID
	}

	// Validate the request
	if validationErrors := req.Validate(); len(validationErrors) > 0 {
		return nil, &ValidationError{
			Errors: validationErrors,
		}
	}

	// Check if todo exists
	exists, err := s.repo.Exists(id)
	if err != nil {
		return nil, err
	}
	if !exists {
		return nil, ErrTodoNotFound
	}

	// Update the todo via repository
	todo, err := s.repo.Update(id, req)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

// DeleteTodo removes a todo from the system
func (s *todoServiceImpl) DeleteTodo(ctx context.Context, id int64) error {
	// Validate ID
	if id <= 0 {
		return ErrInvalidID
	}

	// Check if todo exists
	exists, err := s.repo.Exists(id)
	if err != nil {
		return err
	}
	if !exists {
		return ErrTodoNotFound
	}

	// Delete the todo via repository
	err = s.repo.Delete(id)
	if err != nil {
		return err
	}

	return nil
}

// Service errors
var (
	ErrTodoNotFound = errors.New("todo not found")
	ErrInvalidID    = errors.New("invalid todo ID")
)

// ValidationError represents validation errors from the service layer
type ValidationError struct {
	Errors []models.ValidationError
}

// Error implements the error interface
func (e *ValidationError) Error() string {
	if len(e.Errors) == 0 {
		return "validation error"
	}
	return e.Errors[0].Message
}

// HasErrors returns true if there are validation errors
func (e *ValidationError) HasErrors() bool {
	return len(e.Errors) > 0
}

// GetErrors returns the list of validation errors
func (e *ValidationError) GetErrors() []models.ValidationError {
	return e.Errors
}
package models

import (
	"time"
)

// Todo represents a todo item in the system
type Todo struct {
	ID          int64     `json:"id"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Completed   bool      `json:"completed"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// CreateTodoRequest represents the data needed to create a new todo
type CreateTodoRequest struct {
	Title       string `json:"title" validate:"required,min=1,max=255"`
	Description string `json:"description" validate:"max=1000"`
}

// UpdateTodoRequest represents the data needed to update an existing todo
type UpdateTodoRequest struct {
	Title       *string `json:"title,omitempty" validate:"omitempty,min=1,max=255"`
	Description *string `json:"description,omitempty" validate:"omitempty,max=1000"`
	Completed   *bool   `json:"completed,omitempty"`
}

// TodoRepository defines the interface for todo data operations
type TodoRepository interface {
	// Create inserts a new todo into the database
	Create(todo *CreateTodoRequest) (*Todo, error)
	
	// GetByID retrieves a todo by its ID
	GetByID(id int64) (*Todo, error)
	
	// GetAll retrieves all todos with optional filtering
	GetAll(completed *bool) ([]Todo, error)
	
	// Update updates an existing todo
	Update(id int64, update *UpdateTodoRequest) (*Todo, error)
	
	// Delete removes a todo from the database
	Delete(id int64) error
	
	// Exists checks if a todo with the given ID exists
	Exists(id int64) (bool, error)
}

// ValidationError represents a validation error for todo data
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// Validate performs validation on CreateTodoRequest
func (r *CreateTodoRequest) Validate() []ValidationError {
	var errors []ValidationError
	
	if r.Title == "" {
		errors = append(errors, ValidationError{
			Field:   "title",
			Message: "Title is required",
		})
	} else if len(r.Title) > 255 {
		errors = append(errors, ValidationError{
			Field:   "title",
			Message: "Title must be less than 255 characters",
		})
	}
	
	if len(r.Description) > 1000 {
		errors = append(errors, ValidationError{
			Field:   "description",
			Message: "Description must be less than 1000 characters",
		})
	}
	
	return errors
}

// Validate performs validation on UpdateTodoRequest
func (r *UpdateTodoRequest) Validate() []ValidationError {
	var errors []ValidationError
	
	if r.Title != nil {
		if *r.Title == "" {
			errors = append(errors, ValidationError{
				Field:   "title",
				Message: "Title cannot be empty",
			})
		} else if len(*r.Title) > 255 {
			errors = append(errors, ValidationError{
				Field:   "title",
				Message: "Title must be less than 255 characters",
			})
		}
	}
	
	if r.Description != nil && len(*r.Description) > 1000 {
		errors = append(errors, ValidationError{
			Field:   "description",
			Message: "Description must be less than 1000 characters",
		})
	}
	
	return errors
}
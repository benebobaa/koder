package config

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

// Config holds all configuration for the application
type Config struct {
	// Server configuration
	ServerPort string
	ServerHost string
	
	// Database configuration
	DBHost     string
	DBPort     string
	DBUser     string
	DBPassword string
	DBName     string
	DBSSLMode  string
	
	// Application settings
	Environment string
	LogLevel    string
	
	// Timeout settings
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration
}

// Load loads configuration from environment variables and .env file
func Load() (*Config, error) {
	// Load .env file if it exists
	_ = godotenv.Load()
	
	config := &Config{
		// Server configuration
		ServerPort: getEnv("SERVER_PORT", "8080"),
		ServerHost: getEnv("SERVER_HOST", "0.0.0.0"),
		
		// Database configuration
		DBHost:     getEnv("DB_HOST", "localhost"),
		DBPort:     getEnv("DB_PORT", "5432"),
		DBUser:     getEnv("DB_USER", "postgres"),
		DBPassword: getEnv("DB_PASSWORD", "password"),
		DBName:     getEnv("DB_NAME", "tododb"),
		DBSSLMode:  getEnv("DB_SSL_MODE", "disable"),
		
		// Application settings
		Environment: getEnv("ENVIRONMENT", "development"),
		LogLevel:    getEnv("LOG_LEVEL", "info"),
	}
	
	// Parse timeout durations
	readTimeout, err := strconv.Atoi(getEnv("READ_TIMEOUT", "10"))
	if err != nil {
		log.Printf("Invalid READ_TIMEOUT, using default: %v", err)
		readTimeout = 10
	}
	
	writeTimeout, err := strconv.Atoi(getEnv("WRITE_TIMEOUT", "10"))
	if err != nil {
		log.Printf("Invalid WRITE_TIMEOUT, using default: %v", err)
		writeTimeout = 10
	}
	
	idleTimeout, err := strconv.Atoi(getEnv("IDLE_TIMEOUT", "60"))
	if err != nil {
		log.Printf("Invalid IDLE_TIMEOUT, using default: %v", err)
		idleTimeout = 60
	}
	
	config.ReadTimeout = time.Duration(readTimeout) * time.Second
	config.WriteTimeout = time.Duration(writeTimeout) * time.Second
	config.IdleTimeout = time.Duration(idleTimeout) * time.Second
	
	return config, nil
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// GetDatabaseDSN returns the database connection string
func (c *Config) GetDatabaseDSN() string {
	return fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		c.DBHost,
		c.DBPort,
		c.DBUser,
		c.DBPassword,
		c.DBName,
		c.DBSSLMode,
	)
}

// IsDevelopment returns true if the environment is development
func (c *Config) IsDevelopment() bool {
	return c.Environment == "development"
}

// IsProduction returns true if the environment is production
func (c *Config) IsProduction() bool {
	return c.Environment == "production"
}

// GetServerAddress returns the server address for binding
func (c *Config) GetServerAddress() string {
	return fmt.Sprintf("%s:%s", c.ServerHost, c.ServerPort)
}
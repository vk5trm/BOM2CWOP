# Compiler and Flags
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
LDFLAGS = -lcurl

# Target executable name
TARGET = bom2cwop

# Source files
SRC = bom2cwop.cpp

# Header files (if you split code later)
HDRS = 

# Object files
OBJ = $(SRC:.cpp=.o)

# Default target
all: $(TARGET)

# Linking
$(TARGET): $(OBJ)
	@echo "Linking $(TARGET)..."
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "Build complete: $(TARGET)"

# Compilation
%.o: %.cpp $(HDRS)
	@echo "Compiling $<..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Run the program
run: $(TARGET)
	@echo "Running $(TARGET)..."
	./$(TARGET)

# Clean build artifacts
clean:
	@echo "Cleaning up..."
	rm -f $(OBJ) $(TARGET)
	@echo "Clean complete."

# Phony targets (prevent conflicts with files named 'clean', 'all', etc.)
.PHONY: all clean run

# Dependency check for nlohmann/json
# Ensure nlohmann/json.hpp is in the current directory or include path
check-deps:
	@if [ ! -f "nlohmann/json.hpp" ]; then \
		echo "Warning: nlohmann/json.hpp not found in current directory."; \
		echo "Download it from: https://github.com/nlohmann/json/releases"; \
	else \
		echo "Dependency nlohmann/json.hpp found."; \
	fi

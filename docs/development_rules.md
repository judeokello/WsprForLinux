# 🛠️ W4L Development Rules & Standards

## 📁 Directory Structure Enforcement

### **Mandatory Structure Compliance**
- **ALWAYS** follow the structure defined in `docs/directory_structure.md`
- **NEVER** create files outside the designated directories
- **ALWAYS** use the exact module names and file locations specified
- **NEVER** skip creating `__init__.py` files in package directories

### **File Naming Conventions**
- **Python files**: Use snake_case (e.g., `main_window.py`, `audio_recorder.py`)
- **Directories**: Use snake_case (e.g., `src/`, `gui/`, `audio/`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `AUDIO_SAMPLE_RATE`, `MAX_RECORDING_TIME`)
- **Classes**: Use PascalCase (e.g., `MainWindow`, `AudioRecorder`)
- **Functions**: Use snake_case (e.g., `start_recording()`, `process_audio()`)

### **Import Structure Rules**
- **ALWAYS** use relative imports within modules: `from .main_window import MainWindow`
- **ALWAYS** use absolute imports from src: `from src.gui import MainWindow`
- **NEVER** use wildcard imports: `from src.gui import *`
- **ALWAYS** define `__all__` in `__init__.py` files

---

## 🏗️ Module Development Standards

### **Module Responsibilities**
- **gui/**: ONLY user interface components
- **audio/**: ONLY audio recording and processing
- **transcription/**: ONLY speech-to-text functionality
- **system/**: ONLY Linux system integration
- **config/**: ONLY configuration and settings
- **utils/**: ONLY shared utility functions

### **Cross-Module Communication**
- **NEVER** import GUI components in audio modules
- **NEVER** import system modules in GUI modules
- **ALWAYS** use dependency injection for module communication
- **ALWAYS** define clear interfaces between modules

---

## 📝 Code Quality Standards

### **Documentation Requirements**
- **ALWAYS** add docstrings to all classes and functions
- **ALWAYS** include type hints for function parameters and return values
- **ALWAYS** document complex algorithms and business logic
- **NEVER** leave TODO comments without context

### **Error Handling**
- **ALWAYS** handle exceptions gracefully
- **ALWAYS** provide user-friendly error messages
- **ALWAYS** log errors with appropriate detail
- **NEVER** let exceptions bubble up to the user interface

### **Testing Requirements**
- **ALWAYS** write unit tests for new functionality
- **ALWAYS** test module boundaries and interfaces
- **ALWAYS** mock external dependencies in tests
- **NEVER** skip testing critical paths

---

## 🔧 Development Workflow

### **Phase-Based Development**
- **ALWAYS** complete all tasks in a phase before moving to the next
- **ALWAYS** update progress checkboxes in `devplan.md`
- **ALWAYS** test phase completion before proceeding
- **NEVER** skip phase tasks or combine phases

### **File Creation Order**
1. **ALWAYS** create directory structure first
2. **ALWAYS** create `__init__.py` files immediately
3. **ALWAYS** create module skeletons before implementation
4. **ALWAYS** add imports and exports in `__init__.py` files

### **Resource Management**
- **ALWAYS** create placeholder files in `resources/` directories
- **ALWAYS** use relative paths for resource loading
- **ALWAYS** handle missing resources gracefully
- **NEVER** hardcode resource paths

---

## 🎯 Quality Assurance

### **Before Each Commit**
- **ALWAYS** run code formatting: `black src/`
- **ALWAYS** run linting: `flake8 src/`
- **ALWAYS** run tests: `pytest tests/`
- **ALWAYS** verify directory structure compliance

### **Code Review Checklist**
- [ ] Follows directory structure
- [ ] Uses correct naming conventions
- [ ] Has proper documentation
- [ ] Includes error handling
- [ ] Has corresponding tests
- [ ] Follows module boundaries

---

## 🚨 Common Violations to Avoid

### **❌ DON'T DO:**
- Create files in wrong directories
- Skip `__init__.py` files
- Use incorrect import patterns
- Mix module responsibilities
- Hardcode configuration values
- Skip error handling
- Forget to update progress tracking

### **✅ ALWAYS DO:**
- Follow the exact directory structure
- Create proper package structure
- Use clean import patterns
- Maintain module separation
- Use configuration management
- Handle errors gracefully
- Update progress checkboxes

---

## 📊 Progress Tracking Rules

### **Checkbox Management**
- **ALWAYS** check off completed tasks immediately
- **ALWAYS** update progress percentages
- **ALWAYS** note any deviations from plan
- **NEVER** mark tasks complete without verification

### **Documentation Updates**
- **ALWAYS** update relevant documentation when structure changes
- **ALWAYS** keep `directory_structure.md` current
- **ALWAYS** document any deviations from plan
- **NEVER** leave documentation outdated

---

## 🔄 Iteration Rules

### **Refactoring Guidelines**
- **ALWAYS** maintain backward compatibility during refactoring
- **ALWAYS** update all affected modules
- **ALWAYS** update tests after refactoring
- **NEVER** break existing functionality

### **Extension Points**
- **ALWAYS** design for future extensibility
- **ALWAYS** use interfaces for module communication
- **ALWAYS** keep configuration external
- **NEVER** hardcode implementation details

---

## 🎯 Success Metrics

### **Structure Compliance**
- 100% adherence to directory structure
- All `__init__.py` files properly configured
- Clean import structure throughout
- No circular dependencies

### **Code Quality**
- 100% test coverage for critical paths
- Zero linting errors
- Complete documentation coverage
- Proper error handling everywhere

### **Progress Tracking**
- Accurate progress percentages
- All completed tasks checked off
- Clear documentation of any changes
- Up-to-date development status

---

## 🚀 Getting Started Checklist

Before beginning any development:

- [ ] Review `docs/directory_structure.md`
- [ ] Review `docs/devplan.md` for current phase
- [ ] Ensure development environment is set up
- [ ] Verify all dependencies are installed
- [ ] Check that no structural violations exist
- [ ] Confirm progress tracking is current

**Remember**: These rules ensure consistent, maintainable, and scalable code. Following them strictly will make the development process smoother and the final product more robust. 
# **Contributing to Stock Sentinel**

Thank you for considering contributing to Stock Sentinel. This guide outlines the process for contributing to ensure a smooth and efficient collaboration.  

---

## **Table of Contents**  
1. [Setting Up the Development Environment](#setting-up-the-development-environment)  
2. [Branching Strategy](#branching-strategy)  
3. [Commit Messages](#commit-messages)  
4. [Development Workflow](#development-workflow)  
5. [Pull Requests](#pull-requests)  
6. [Releases](#releases)  
7. [Code of Conduct](#code-of-conduct)  

---

## **Setting Up the Development Environment**  

This section explains how to configure the local development environment using `uv` for dependency management and `docker-compose.dev` for running services.  

### **Prerequisites**  
Ensure you have the following installed:  
- Python **3.12.1**  
- `uv` (dependency management)  
- Docker & Docker Compose  

### **Installing `uv` and Setting Up the Virtual Environment**  

#### **1. Install `uv` (if not installed)**  
```bash
pip install uv
```

#### **2. Create and Activate the Virtual Environment**  
```bash
uv venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows (PowerShell)
```

#### **3. Install Dependencies**  
```bash
uv pip install -r requirements.dev.txt
```

This will install `black`, `ruff`, `mypy`, and other dependencies required for development.  

---

### **Configuring the IDE for Autocompletion**  

To enable autocompletion and type hints, configure your IDE to use the `uv` virtual environment:

#### **VS Code**  
1. Open `Command Palette` (`Cmd+Shift+P` or `Ctrl+Shift+P`).  
2. Search for `Python: Select Interpreter`.  
3. Select `.venv` created by `uv`.  

#### **PyCharm**  
1. Go to `Preferences` → `Project: <project-name>` → `Python Interpreter`.  
2. Click `Add Interpreter` → `Existing Environment`.  
3. Select `.venv` as the interpreter.  

---

### **Running Code Checks and Formatting**  

#### **Run Formatters & Linters**  
Before committing code, run the following:  

```bash
black .
ruff .
mypy --ignore-missing-imports .
```

#### **Enable `pre-commit` Hooks**  
To automatically run formatters and linters before every commit:  

```bash
pre-commit install
```

To manually trigger `pre-commit` on all files:  

```bash
pre-commit run --all-files
```

---

### **Running the Development Environment**  

The project includes a `docker-compose.dev.yml` file for local development.  

#### **Start the Development Environment**  
```bash
make up-dev
```
or  
```bash
docker-compose -f docker/docker-compose.dev.yml up -d --force-recreate
```

#### **Rebuild Containers**  
```bash
make build-dev
```
or  
```bash
docker-compose -f docker/docker-compose.dev.yml build --no-cache
```

#### **Stop the Development Environment**  
```bash
make down-dev
```
or  
```bash
docker-compose -f docker/docker-compose.dev.yml down
```

#### **Check Logs**  
```bash
make logs-dev
```
or  
```bash
docker-compose -f docker/docker-compose.dev.yml logs -f
```

---

### **Summary of Commands**  

| Task                          | Command |
|--------------------------------|---------|
| Install dependencies          | `uv pip install -r requirements.dev.txt` |
| Activate virtual environment  | `source .venv/bin/activate` (Mac/Linux) / `.venv\Scripts\activate` (Windows) |
| Run formatters and linters    | `black . && ruff . && mypy --ignore-missing-imports .` |
| Install pre-commit hooks      | `pre-commit install` |
| Start development environment | `make up-dev` |
| Stop development environment  | `make down-dev` |
| Rebuild containers            | `make build-dev` |
| View logs                     | `make logs-dev` |

---

## **Branching Strategy**  

This project follows a structured branching model:  

- **`main`**: The production-ready branch containing only stable releases.  
- **`develop`**: The main development branch where all new features, fixes, and changes are merged.  
- **Feature Branches**: Created for specific tasks using the following naming conventions:  
  - `feat/feature-name` for new features.  
  - `fix/bug-name` for bug fixes.  
  - `chore/task-name` for maintenance or tooling updates.  
  - `docs/documentation-name` for documentation updates.  

---

## **Commit Messages**  

We follow [Conventional Commits](https://www.conventionalcommits.org/) to maintain a structured commit history.  

### **Commit Format**  
```bash
<type>: <description>
```

### **Commit Types**  
- `feat`: A new feature.  
- `fix`: A bug fix.  
- `docs`: Documentation updates.  
- `chore`: Maintenance tasks (e.g., dependency updates).  

### **Examples**  
```bash
feat: add user authentication  
fix: resolve issue with data validation  
docs: update API documentation  
```

---

## **Development Workflow**  

### **1. Cloning the Repository**
```bash
git clone https://github.com/playgude2/stock-sentinel.git
cd stock-sentinel
```

### **2. Creating a New Branch**  
```bash
git checkout -b feat/your-feature-name
```

### **3. Making Changes and Committing**  
```bash
git add .
git commit -m "feat: describe your change"
```

### **4. Syncing with `develop`**  
```bash
git pull origin develop
```

### **5. Testing and Code Checks**  
Before submitting a pull request, ensure your code passes all tests and linting checks.  

---

## **Pull Requests**  

All new contributions must go through a pull request (PR) process:  

1. **Target Branch**: PRs must target the `develop` branch.  
2. **Description**: Provide a clear summary of the changes in the PR.  
3. **Checklist Before Submitting**:  
    - Code follows project guidelines.  
    - Commits follow the Conventional Commit format.  
    - Linting and formatting checks pass.  
    - All necessary tests are included.  
4. **Review Process**: PRs will be reviewed and may require changes before merging.  

---

## **Releases**  

Releases follow **Semantic Versioning**:  
- **Major**: Breaking changes.  
- **Minor**: New features, backward-compatible.  
- **Patch**: Bug fixes.  

### **Release Process**  
1. The `develop` branch is merged into `main`.  
2. The release is tagged, e.g., `v1.0.0`.  
3. The commit message follows the format:  
   ```bash
   chore(release): v1.0.0
   ```  

---

## **Code of Conduct**  

By contributing, you agree to follow the project's Code of Conduct to ensure a welcoming and inclusive environment.  

---

## **Questions and Support**

For any questions, open an issue on GitHub:

- GitHub: [@playgude2](https://github.com/playgude2)

Thank you for contributing!
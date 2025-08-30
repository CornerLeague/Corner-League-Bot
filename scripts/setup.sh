#!/bin/bash

# Sports Media Platform Setup Script
# This script sets up the local development environment

set -e

echo "🏆 Setting up Sports Media Platform..."

# Check if required tools are installed
check_requirements() {
    echo "📋 Checking requirements..."

    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3.11+ is required"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        echo "❌ Node.js 18+ is required"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is required"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is required"
        exit 1
    fi

    echo "✅ All requirements satisfied"
}

# Setup Python environment
setup_python() {
    echo "🐍 Setting up Python environment..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    pip install -e .

    echo "✅ Python environment ready"
}

# Setup Node.js environment
setup_node() {
    echo "📦 Setting up Node.js environment..."

    cd frontend

    # Install pnpm if not available
    if ! command -v pnpm &> /dev/null; then
        npm install -g pnpm
    fi

    # Install dependencies
    pnpm install

    cd ..

    echo "✅ Node.js environment ready"
}

# Setup infrastructure services
setup_infrastructure() {
    echo "🐳 Setting up infrastructure services..."

    # Start PostgreSQL and Redis
    docker-compose up -d postgres redis

    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10

    # Check if services are running
    if ! docker-compose ps | grep -q "postgres.*Up"; then
        echo "❌ PostgreSQL failed to start"
        exit 1
    fi

    if ! docker-compose ps | grep -q "redis.*Up"; then
        echo "❌ Redis failed to start"
        exit 1
    fi

    echo "✅ Infrastructure services ready"
}

# Setup database
setup_database() {
    echo "🗄️ Setting up database..."

    # Activate Python environment
    source venv/bin/activate

    # Run database migrations
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
    else
        echo "⚠️ No Alembic configuration found, skipping migrations"
    fi

    # Seed database with initial data
    if [ -f "scripts/seed_database.py" ]; then
        python scripts/seed_database.py
    else
        echo "⚠️ No seed script found, skipping database seeding"
    fi

    echo "✅ Database ready"
}

# Setup environment variables
setup_environment() {
    echo "🔧 Setting up environment variables..."

    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "📝 Created .env file from .env.example"
        echo "⚠️ Please update .env with your actual configuration values"
    else
        echo "✅ .env file already exists"
    fi
}

# Setup pre-commit hooks
setup_hooks() {
    echo "🪝 Setting up pre-commit hooks..."

    # Activate Python environment
    source venv/bin/activate

    # Install pre-commit hooks
    pre-commit install

    echo "✅ Pre-commit hooks installed"
}

# Main setup function
main() {
    echo "🚀 Starting Sports Media Platform setup..."

    check_requirements
    setup_environment
    setup_python
    setup_node
    setup_infrastructure
    setup_database
    setup_hooks

    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update .env file with your configuration"
    echo "2. Start the API server: source venv/bin/activate && python -m apps.api.main"
    echo "3. Start the frontend: cd frontend && pnpm run dev"
    echo "4. Start background workers: source venv/bin/activate && python -m apps.workers.crawler_worker"
    echo ""
    echo "🌐 Access the application:"
    echo "- Frontend: http://localhost:3000"
    echo "- API Documentation: http://localhost:8000/docs"
    echo "- Health Check: http://localhost:8000/health"
    echo ""
    echo "📚 Documentation: docs/"
    echo "🧪 Run tests: pytest"
    echo "🔍 Code quality: pre-commit run --all-files"
}

# Run main function
main "$@"

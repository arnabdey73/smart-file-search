# Smart File Search - Makefile for GitOps Deployment

.PHONY: help build deploy status cleanup test-local

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_NAME := smart-file-search
NAMESPACE := smart-file-search
IMAGE_NAME := smart-file-search
IMAGE_TAG := latest
REGISTRY_HOST := localhost:30500

# Help target
help: ## Show this help message
	@echo "Smart File Search - GitOps Deployment"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Build Docker image
build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) \
		--build-arg BUILD_DATE="$$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
		--build-arg VERSION="1.0.0" \
		--build-arg VCS_REF="$$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
		.

# Push to local registry
push: build ## Build and push image to registry
	@echo "Tagging and pushing image..."
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY_HOST)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(REGISTRY_HOST)/$(IMAGE_NAME):$(IMAGE_TAG)

# Deploy using script
deploy: ## Deploy application to Kubernetes
	@echo "Deploying application..."
	chmod +x deploy-gitops.sh
	./deploy-gitops.sh deploy

# Quick deploy for local development
deploy-local: build ## Build and deploy locally (no registry push)
	@echo "Deploying locally..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f k8s/pvc.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl wait --for=condition=available --timeout=300s deployment/$(PROJECT_NAME) -n $(NAMESPACE)

# Show deployment status
status: ## Show deployment status
	@echo "Deployment Status:"
	@echo "=================="
	@kubectl get pods,svc,pvc -n $(NAMESPACE) 2>/dev/null || echo "Namespace $(NAMESPACE) not found"
	@echo ""
	@echo "Health Check:"
	@NODE_IP=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null); \
	if [ -n "$$NODE_IP" ]; then \
		echo "Checking http://$$NODE_IP:30900/health"; \
		curl -s http://$$NODE_IP:30900/health 2>/dev/null || echo "Service not accessible"; \
	fi

# Cleanup deployment
cleanup: ## Remove all deployed resources
	@echo "Cleaning up deployment..."
	chmod +x deploy-gitops.sh
	./deploy-gitops.sh cleanup

# Test application locally
test-local: ## Test application locally (without Kubernetes)
	@echo "Testing application locally..."
	python -m venv test-env
	test-env/Scripts/pip install -r requirements.txt
	test-env/Scripts/python mcp_server/server.py &
	@echo "Server started in background. Test with: curl http://localhost:9000/health"

# View logs
logs: ## View application logs
	kubectl logs -n $(NAMESPACE) -l app.kubernetes.io/name=$(PROJECT_NAME) -f

# Shell into pod
shell: ## Get shell access to the running pod
	kubectl exec -n $(NAMESPACE) -it deployment/$(PROJECT_NAME) -- /bin/bash

# Port forward for local access
port-forward: ## Forward port 9000 to local machine
	@echo "Port forwarding 9000:9000. Access at http://localhost:9000"
	kubectl port-forward -n $(NAMESPACE) svc/$(PROJECT_NAME)-service 9000:9000

# Restart deployment
restart: ## Restart the deployment
	kubectl rollout restart deployment/$(PROJECT_NAME) -n $(NAMESPACE)
	kubectl rollout status deployment/$(PROJECT_NAME) -n $(NAMESPACE)

# Lint Kubernetes manifests
lint: ## Lint Kubernetes manifests
	@echo "Linting Kubernetes manifests..."
	@for file in k8s/*.yaml; do \
		echo "Checking $$file..."; \
		kubectl apply --dry-run=client --validate=true -f $$file > /dev/null && echo "✓ $$file" || echo "✗ $$file"; \
	done

# Security scan
security-scan: ## Run security scan on Docker image
	@echo "Running security scan..."
	@if command -v trivy >/dev/null 2>&1; then \
		trivy image $(IMAGE_NAME):$(IMAGE_TAG); \
	else \
		echo "Trivy not installed. Install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"; \
	fi

# Performance test
perf-test: ## Run basic performance test
	@echo "Running performance test..."
	@NODE_IP=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null); \
	if [ -n "$$NODE_IP" ]; then \
		echo "Testing endpoint: http://$$NODE_IP:30900/health"; \
		for i in $$(seq 1 10); do \
			curl -s -w "Request $$i: %{time_total}s\n" -o /dev/null http://$$NODE_IP:30900/health; \
		done; \
	else \
		echo "Cannot determine node IP"; \
	fi

# Generate documentation
docs: ## Generate API documentation
	@echo "Generating documentation..."
	@if [ -f "mcp_server/server.py" ]; then \
		echo "API Endpoints:" > API.md; \
		echo "==============" >> API.md; \
		grep -n "@app\." mcp_server/server.py | sed 's/@app\./- /' >> API.md; \
		echo "Documentation generated in API.md"; \
	fi

# Environment setup
setup-env: ## Setup development environment
	@echo "Setting up development environment..."
	python -m venv venv
	venv/Scripts/pip install -r requirements.txt
	@echo "Environment setup complete. Activate with: venv/Scripts/activate"

# Clean development environment
clean-env: ## Clean development environment
	@echo "Cleaning development environment..."
	rm -rf venv/ test-env/ __pycache__/ *.pyc
	docker system prune -f

# Initialize sample data
init-data: ## Initialize sample data in the deployed application
	@echo "Initializing sample data..."
	@NODE_IP=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null); \
	if [ -n "$$NODE_IP" ]; then \
		curl -X POST "http://$$NODE_IP:30900/tools/indexFolder" \
			-H "Content-Type: application/json" \
			-d '{"path": "/app/sample_data"}'; \
	fi

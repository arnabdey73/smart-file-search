#!/bin/bash

# Smart File Search - GitOps Deployment Script
# This script prepares and deploys the smart-file-search application to the single-node GitOps platform

set -e

# Configuration
PROJECT_NAME="smart-file-search"
NAMESPACE="smart-file-search"
IMAGE_NAME="smart-file-search"
IMAGE_TAG="latest"
REGISTRY_HOST="${REGISTRY_HOST:-localhost:30500}"
GITOPS_REPO="${GITOPS_REPO:-https://github.com/arnabdey73/single-node-gitops}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to Kubernetes
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log_step "Building Docker image..."
    
    # Build the image
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VERSION="1.0.0" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        .
    
    if [ $? -eq 0 ]; then
        log_info "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Tag and push image to registry
push_image() {
    log_step "Pushing image to registry..."
    
    # Tag for registry
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY_HOST}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Push to registry
    docker push "${REGISTRY_HOST}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    if [ $? -eq 0 ]; then
        log_info "Image pushed to registry successfully"
    else
        log_error "Failed to push image to registry"
        exit 1
    fi
}

# Update deployment manifest with correct image
update_deployment_manifest() {
    log_step "Updating deployment manifest..."
    
    # Update the image in deployment.yaml
    sed -i "s|image: smart-file-search:latest|image: ${REGISTRY_HOST}/${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/deployment.yaml
    
    log_info "Deployment manifest updated"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    log_step "Deploying to Kubernetes..."
    
    # Apply all Kubernetes manifests
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml
    kubectl apply -f k8s/pvc.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    if [ $? -eq 0 ]; then
        log_info "Application deployed successfully"
    else
        log_error "Failed to deploy application"
        exit 1
    fi
}

# Setup ArgoCD Application
setup_argocd() {
    log_step "Setting up ArgoCD Application..."
    
    # Check if ArgoCD namespace exists
    if kubectl get namespace argocd &> /dev/null; then
        # Update ArgoCD application manifest with your repo URL
        if [ -n "${GITHUB_REPO}" ]; then
            sed -i "s|repoURL: https://github.com/your-username/smart-file-search|repoURL: ${GITHUB_REPO}|g" k8s/argocd-application.yaml
        fi
        
        # Apply ArgoCD application
        kubectl apply -f k8s/argocd-application.yaml
        log_info "ArgoCD Application configured"
    else
        log_warn "ArgoCD not found. Skipping ArgoCD setup."
    fi
}

# Wait for deployment
wait_for_deployment() {
    log_step "Waiting for deployment to be ready..."
    
    kubectl wait --for=condition=available --timeout=300s deployment/${PROJECT_NAME} -n ${NAMESPACE}
    
    if [ $? -eq 0 ]; then
        log_info "Deployment is ready"
    else
        log_error "Deployment failed to become ready"
        exit 1
    fi
}

# Show deployment status
show_status() {
    log_step "Deployment Status:"
    
    echo ""
    echo "Namespace: ${NAMESPACE}"
    echo "Service: ${PROJECT_NAME}-service"
    echo "NodePort: 30900"
    echo ""
    
    # Get node IP
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null)
    if [ -z "$NODE_IP" ]; then
        NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
    fi
    
    echo "Access URLs:"
    echo "  External: http://${NODE_IP}:30900"
    echo "  Internal: http://${PROJECT_NAME}-service.${NAMESPACE}.svc.cluster.local:9000"
    echo ""
    
    # Show pod status
    echo "Pod Status:"
    kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=${PROJECT_NAME}
    echo ""
    
    # Show service status
    echo "Service Status:"
    kubectl get services -n ${NAMESPACE}
    echo ""
}

# Create sample data ConfigMap
create_sample_data() {
    log_step "Creating sample data ConfigMap..."
    
    # Check if sample_data directory exists
    if [ -d "sample_data" ]; then
        kubectl create configmap smart-file-search-sample-data \
            --from-file=sample_data/ \
            --namespace=${NAMESPACE} \
            --dry-run=client -o yaml | kubectl apply -f -
        log_info "Sample data ConfigMap created"
    else
        log_warn "No sample_data directory found"
    fi
}

# Main deployment function
deploy() {
    log_info "Starting deployment of ${PROJECT_NAME}..."
    
    check_prerequisites
    build_image
    
    # Only push to registry if registry host is not localhost
    if [[ "${REGISTRY_HOST}" != "localhost"* ]]; then
        push_image
        update_deployment_manifest
    fi
    
    deploy_to_kubernetes
    create_sample_data
    setup_argocd
    wait_for_deployment
    show_status
    
    log_info "Deployment completed successfully!"
}

# Cleanup function
cleanup() {
    log_step "Cleaning up resources..."
    
    kubectl delete -f k8s/ --ignore-not-found=true
    
    # Remove configmap
    kubectl delete configmap smart-file-search-sample-data -n ${NAMESPACE} --ignore-not-found=true
    
    log_info "Cleanup completed"
}

# Show help
show_help() {
    echo "Smart File Search - GitOps Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy    - Deploy the application (default)"
    echo "  cleanup   - Remove all deployed resources"
    echo "  status    - Show deployment status"
    echo "  help      - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  REGISTRY_HOST - Container registry host (default: localhost:30500)"
    echo "  GITHUB_REPO   - GitHub repository URL for ArgoCD"
    echo ""
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    cleanup)
        cleanup
        ;;
    status)
        show_status
        ;;
    help)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

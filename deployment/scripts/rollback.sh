#!/bin/bash

################################################################################
# Rollback Script for DYGSOM Fraud API
# Usage: ./rollback.sh [staging|production] [backup-file]
#
# This script handles rollback to a previous deployment:
# 1. Find latest backup or use specified backup file
# 2. Load environment configuration
# 3. Restore configuration from backup
# 4. Rollback with docker compose
# 5. Health check to verify rollback success
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_HEALTH_CHECK_RETRIES=5
HEALTH_CHECK_DELAY=5
STARTUP_WAIT=10

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_usage() {
    echo "Usage: $0 [staging|production] [backup-file]"
    echo ""
    echo "Arguments:"
    echo "  environment  - Target environment (staging or production)"
    echo "  backup-file  - (Optional) Specific backup file to restore"
    echo "                 If not specified, uses the latest backup"
    echo ""
    echo "Examples:"
    echo "  $0 staging"
    echo "  $0 production /opt/dygsom-fraud-api/backups/backup-20250125-143000.tar.gz"
    exit 1
}

health_check() {
    local url=$1
    local retries=0

    log_info "Running health checks on $url..."

    while [ $retries -lt $MAX_HEALTH_CHECK_RETRIES ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "Health check passed!"
            return 0
        else
            retries=$((retries + 1))
            log_warning "Health check failed (attempt $retries/$MAX_HEALTH_CHECK_RETRIES)"

            if [ $retries -lt $MAX_HEALTH_CHECK_RETRIES ]; then
                sleep $HEALTH_CHECK_DELAY
            fi
        fi
    done

    log_error "Health check failed after $MAX_HEALTH_CHECK_RETRIES attempts"
    return 1
}

find_latest_backup() {
    local backup_dir=$1

    log_info "Finding latest backup in $backup_dir..."

    local latest_backup=$(ls -t "$backup_dir"/backup-*.tar.gz 2>/dev/null | head -n1)

    if [ -z "$latest_backup" ]; then
        log_error "No backups found in $backup_dir"
        return 1
    fi

    echo "$latest_backup"
}

list_backups() {
    local backup_dir=$1

    log_info "Available backups:"

    local backups=$(ls -t "$backup_dir"/backup-*.tar.gz 2>/dev/null)

    if [ -z "$backups" ]; then
        log_warning "No backups found"
        return 1
    fi

    local count=1
    while IFS= read -r backup; do
        local size=$(du -h "$backup" | cut -f1)
        local date=$(echo "$backup" | grep -oP '\d{8}-\d{6}')
        echo "  $count. $backup ($size) - $date"
        count=$((count + 1))
    done <<< "$backups"
}

restore_backup() {
    local backup_file=$1
    local deploy_dir=$2

    log_info "Restoring backup: $backup_file"

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    # Create temporary directory for extraction
    local temp_dir="/tmp/rollback-$(date +%s)"
    mkdir -p "$temp_dir"

    # Extract backup
    if ! tar -xzf "$backup_file" -C "$temp_dir"; then
        log_error "Failed to extract backup"
        rm -rf "$temp_dir"
        return 1
    fi

    # Backup current configuration (in case rollback fails)
    cp "$deploy_dir/docker-compose.yml" "$deploy_dir/docker-compose.yml.pre-rollback" 2>/dev/null || true
    cp "$deploy_dir/.env" "$deploy_dir/.env.pre-rollback" 2>/dev/null || true

    # Restore configuration
    cp "$temp_dir/docker-compose.yml" "$deploy_dir/" || true
    cp "$temp_dir/.env" "$deploy_dir/" || true

    # Cleanup
    rm -rf "$temp_dir"

    log_success "Backup restored successfully"
    return 0
}

################################################################################
# Main Rollback Logic
################################################################################

main() {
    # Validate arguments
    if [ $# -lt 1 ]; then
        log_error "Missing required arguments"
        print_usage
    fi

    ENVIRONMENT=$1
    BACKUP_FILE=$2

    # Validate environment
    if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
        log_error "Invalid environment: $ENVIRONMENT"
        print_usage
    fi

    log_warning "=========================================="
    log_warning "  DYGSOM Fraud API Rollback"
    log_warning "=========================================="
    log_warning "Environment: $ENVIRONMENT"
    log_warning "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    log_warning "=========================================="
    echo ""

    # Navigate to deployment directory
    DEPLOY_DIR="/opt/dygsom-fraud-api/deployment/$ENVIRONMENT"

    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "Deployment directory not found: $DEPLOY_DIR"
        exit 1
    fi

    cd "$DEPLOY_DIR"
    log_success "Changed to deployment directory: $DEPLOY_DIR"

    # Backup directory
    BACKUP_DIR="/opt/dygsom-fraud-api/backups"

    # List available backups
    list_backups "$BACKUP_DIR"
    echo ""

    # Find or use specified backup
    if [ -z "$BACKUP_FILE" ]; then
        BACKUP_FILE=$(find_latest_backup "$BACKUP_DIR")

        if [ $? -ne 0 ]; then
            exit 1
        fi

        log_info "Using latest backup: $BACKUP_FILE"

        # Ask for confirmation
        read -p "Do you want to rollback to this backup? (yes/no): " confirmation

        if [ "$confirmation" != "yes" ]; then
            log_warning "Rollback cancelled by user"
            exit 0
        fi
    else
        log_info "Using specified backup: $BACKUP_FILE"
    fi

    # Restore backup configuration
    if ! restore_backup "$BACKUP_FILE" "$DEPLOY_DIR"; then
        log_error "Failed to restore backup"
        exit 1
    fi

    # Load environment variables
    if [ -f ".env" ]; then
        source .env
        log_success "Environment variables loaded"
    fi

    # Stop current containers
    log_info "Stopping current containers..."
    docker compose down || true

    # Rollback with docker compose
    log_info "Rolling back deployment..."

    if ! docker compose up -d --force-recreate api; then
        log_error "Docker compose rollback failed"
        exit 1
    fi

    log_success "Rollback deployment started"

    # Wait for service to start
    log_info "Waiting ${STARTUP_WAIT}s for service to start..."
    sleep $STARTUP_WAIT

    # Health check
    if ! health_check "http://localhost:3000/health/ready"; then
        log_error "Health check failed after rollback!"

        # Show logs for debugging
        log_info "Showing recent logs:"
        docker compose logs --tail=50 api

        log_error "Rollback verification failed!"
        exit 1
    fi

    # Final success message
    echo ""
    log_info "=========================================="
    log_success "Rollback completed successfully!"
    log_info "=========================================="
    log_info "Environment: $ENVIRONMENT"
    log_info "Backup: $BACKUP_FILE"
    log_info "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "=========================================="
    echo ""

    # Show running containers
    log_info "Running containers:"
    docker compose ps

    # Cleanup pre-rollback configurations
    log_info "Cleaning up pre-rollback backups..."
    rm -f "$DEPLOY_DIR/docker-compose.yml.pre-rollback"
    rm -f "$DEPLOY_DIR/.env.pre-rollback"

    exit 0
}

# Run main function
main "$@"

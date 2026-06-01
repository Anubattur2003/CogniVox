#!/bin/bash

# Google Cloud Platform Deployment Helper for Agentic Platform
# Provides guided commands for deploying on GCP Compute Engine

set -euo pipefail

# Color codes
GREEN='\033[92m'
BLUE='\033[94m'
YELLOW='\033[93m'
CYAN='\033[96m'
RESET='\033[0m'
BOLD='\033[1m'

show_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    AGENTIC PLATFORM GCP DEPLOYMENT HELPER                   ║"
    echo "║                      Fast Setup on Google Cloud Platform                    ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo
}

show_prerequisites() {
    echo -e "${YELLOW}📋 Prerequisites:${RESET}"
    echo "   • Google Cloud Account with billing enabled"
    echo "   • gcloud CLI installed and authenticated"
    echo "   • Project created with Compute Engine API enabled"
    echo
}

show_vm_creation() {
    echo -e "${BLUE}🚀 Step 1: Create GCP VM Instance${RESET}"
    echo
    echo "Create a VM with the following command:"
    echo
    echo -e "${CYAN}# Basic VM (suitable for development/testing)${RESET}"
    echo "gcloud compute instances create agentic-platform \\"
    echo "  --zone=us-central1-a \\"
    echo "  --machine-type=e2-standard-4 \\"
    echo "  --image-family=ubuntu-2204-lts \\"
    echo "  --image-project=ubuntu-os-cloud \\"
    echo "  --boot-disk-size=50GB \\"
    echo "  --boot-disk-type=pd-ssd \\"
    echo "  --tags=agentic-platform,http-server,https-server"
    echo
    echo -e "${CYAN}# Production VM (higher performance)${RESET}"
    echo "gcloud compute instances create agentic-platform-prod \\"
    echo "  --zone=us-central1-a \\"
    echo "  --machine-type=e2-standard-8 \\"
    echo "  --image-family=ubuntu-2204-lts \\"
    echo "  --image-project=ubuntu-os-cloud \\"
    echo "  --boot-disk-size=100GB \\"
    echo "  --boot-disk-type=pd-ssd \\"
    echo "  --tags=agentic-platform,http-server,https-server \\"
    echo "  --metadata=startup-script='#!/bin/bash"
    echo "apt-get update"
    echo "apt-get install -y git python3 python3-pip'"
    echo
}

show_firewall_rules() {
    echo -e "${BLUE}🔐 Step 2: Configure Firewall Rules${RESET}"
    echo
    echo "Create firewall rules for the services:"
    echo
    echo -e "${CYAN}# Frontend (port 3000)${RESET}"
    echo "gcloud compute firewall-rules create agentic-frontend \\"
    echo "  --allow tcp:3000 \\"
    echo "  --source-ranges 0.0.0.0/0 \\"
    echo "  --target-tags agentic-platform"
    echo
    echo -e "${CYAN}# Backend API (port 8000)${RESET}"
    echo "gcloud compute firewall-rules create agentic-backend \\"
    echo "  --allow tcp:8000 \\"
    echo "  --source-ranges 0.0.0.0/0 \\"
    echo "  --target-tags agentic-platform"
    echo
    echo -e "${CYAN}# Memory Service (port 8002)${RESET}"
    echo "gcloud compute firewall-rules create agentic-memory \\"
    echo "  --allow tcp:8002 \\"
    echo "  --source-ranges 0.0.0.0/0 \\"
    echo "  --target-tags agentic-platform"
    echo
    echo -e "${CYAN}# GraphRAG Service (port 8003)${RESET}"
    echo "gcloud compute firewall-rules create agentic-graphrag \\"
    echo "  --allow tcp:8003 \\"
    echo "  --source-ranges 0.0.0.0/0 \\"
    echo "  --target-tags agentic-platform"
    echo
}

show_ssh_connection() {
    echo -e "${BLUE}🔌 Step 3: Connect to Your VM${RESET}"
    echo
    echo "Connect to your VM instance:"
    echo
    echo -e "${CYAN}gcloud compute ssh agentic-platform --zone=us-central1-a${RESET}"
    echo
    echo "Or use SSH with external IP:"
    echo -e "${CYAN}# Get external IP first${RESET}"
    echo "gcloud compute instances describe agentic-platform \\"
    echo "  --zone=us-central1-a \\"
    echo "  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'"
    echo
}

show_deployment_steps() {
    echo -e "${BLUE}🛠️ Step 4: Deploy Agentic Platform${RESET}"
    echo
    echo "Once connected to your VM, run these commands:"
    echo
    echo -e "${CYAN}# Clone the repository${RESET}"
    echo "git clone https://github.com/your-repo/agentic-platform.git"
    echo "cd agentic-platform"
    echo
    echo -e "${CYAN}# Make scripts executable${RESET}"
    echo "chmod +x setup_launcher.sh run_services.sh"
    echo
    echo -e "${CYAN}# Quick setup${RESET}"
    echo "./setup_launcher.sh --quick"
    echo
    echo -e "${CYAN}# Or manual setup${RESET}"
    echo "python3 setup_agentic_platform_linux.py --verbose"
    echo "./run_services.sh --verbose"
    echo
}

show_access_urls() {
    echo -e "${BLUE}🌐 Step 5: Access Your Services${RESET}"
    echo
    echo "After deployment, access your services at:"
    echo
    echo -e "${GREEN}Frontend:    ${BOLD}http://EXTERNAL_IP:3000${RESET}"
    echo -e "${GREEN}Backend API: ${BOLD}http://EXTERNAL_IP:8000${RESET}"
    echo -e "${GREEN}API Docs:    ${BOLD}http://EXTERNAL_IP:8000/docs${RESET}"
    echo -e "${GREEN}Memory API:  ${BOLD}http://EXTERNAL_IP:8002/docs${RESET}"
    echo -e "${GREEN}GraphRAG:    ${BOLD}http://EXTERNAL_IP:8003/docs${RESET}"
    echo
    echo "Replace EXTERNAL_IP with your VM's external IP address"
    echo
}

show_monitoring() {
    echo -e "${BLUE}📊 Step 6: Monitoring & Management${RESET}"
    echo
    echo "Monitor your deployment:"
    echo
    echo -e "${CYAN}# Check service status${RESET}"
    echo "sudo systemctl status agentic-platform"
    echo
    echo -e "${CYAN}# View logs${RESET}"
    echo "sudo journalctl -u agentic-platform -f"
    echo
    echo -e "${CYAN}# Check VM resources${RESET}"
    echo "htop"
    echo "df -h"
    echo "free -h"
    echo
    echo -e "${CYAN}# GCP monitoring${RESET}"
    echo "gcloud compute instances list"
    echo "gcloud compute firewall-rules list"
    echo
}

show_security_notes() {
    echo -e "${YELLOW}🔐 Security Notes:${RESET}"
    echo
    echo "⚠️  Important security considerations:"
    echo "   • Change default passwords in configuration files"
    echo "   • Set up SSL/HTTPS for production use"
    echo "   • Configure proper authentication"
    echo "   • Restrict firewall rules to specific IP ranges if possible"
    echo "   • Regular security updates: sudo apt update && sudo apt upgrade"
    echo "   • Enable GCP security features like OS Login"
    echo
}

show_cost_optimization() {
    echo -e "${GREEN}💰 Cost Optimization Tips:${RESET}"
    echo
    echo "   • Use preemptible instances for development (--preemptible flag)"
    echo "   • Stop instances when not in use: gcloud compute instances stop agentic-platform"
    echo "   • Use smaller machine types for testing (e2-medium, e2-standard-2)"
    echo "   • Set up billing alerts in GCP Console"
    echo "   • Use sustained use discounts for long-running instances"
    echo
}

show_troubleshooting() {
    echo -e "${YELLOW}🔧 Common Issues & Solutions:${RESET}"
    echo
    echo "❓ Services not accessible from external IP:"
    echo "   • Check firewall rules are created correctly"
    echo "   • Verify VM has external IP assigned"
    echo "   • Ensure services are bound to 0.0.0.0 not 127.0.0.1"
    echo
    echo "❓ Out of memory errors:"
    echo "   • Upgrade to larger machine type"
    echo "   • Add swap space: sudo fallocate -l 2G /swapfile"
    echo
    echo "❓ SSL/Domain setup:"
    echo "   • Use Cloud DNS for domain management"
    echo "   • Set up SSL with Let's Encrypt or Cloud Load Balancer"
    echo
}

main() {
    show_banner
    
    if [[ $# -eq 0 ]]; then
        echo -e "${BOLD}Complete GCP Deployment Guide${RESET}"
        echo
        show_prerequisites
        show_vm_creation
        show_firewall_rules
        show_ssh_connection
        show_deployment_steps
        show_access_urls
        show_monitoring
        show_security_notes
        show_cost_optimization
        show_troubleshooting
    else
        case "$1" in
            "--create-vm"|"-v")
                show_vm_creation
                ;;
            "--firewall"|"-f")
                show_firewall_rules
                ;;
            "--connect"|"-c")
                show_ssh_connection
                ;;
            "--deploy"|"-d")
                show_deployment_steps
                ;;
            "--urls"|"-u")
                show_access_urls
                ;;
            "--monitor"|"-m")
                show_monitoring
                ;;
            "--security"|"-s")
                show_security_notes
                ;;
            "--cost"|"-o")
                show_cost_optimization
                ;;
            "--troubleshoot"|"-t")
                show_troubleshooting
                ;;
            "--help"|"-h")
                echo "Usage: $0 [option]"
                echo
                echo "Options:"
                echo "  --create-vm, -v      Show VM creation commands"
                echo "  --firewall, -f       Show firewall setup commands"
                echo "  --connect, -c        Show SSH connection commands"
                echo "  --deploy, -d         Show deployment steps"
                echo "  --urls, -u           Show service access URLs"
                echo "  --monitor, -m        Show monitoring commands"
                echo "  --security, -s       Show security notes"
                echo "  --cost, -o           Show cost optimization tips"
                echo "  --troubleshoot, -t   Show troubleshooting guide"
                echo "  --help, -h           Show this help"
                echo
                echo "Run without arguments to see complete guide"
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for available options"
                exit 1
                ;;
        esac
    fi
    
    echo
    echo -e "${GREEN}🎯 Next: Run the commands above to deploy Agentic Platform on GCP!${RESET}"
}

main "$@" 
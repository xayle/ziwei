#!/bin/bash

# ============================================================================
# BaZi API 部署脚本
# 用法: bash deploy.sh [environment] [action]
# 例: bash deploy.sh docker up
#     bash deploy.sh k8s deploy
# ============================================================================

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="bazi-api"
VERSION="5.3.1"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# ============================================================================
# 本地开发部署
# ============================================================================

deploy_local() {
    local action=$1

    case $action in
        up|start)
            log_info "启动本地开发环境..."

            # 检查虚拟环境
            if [ ! -d ".venv" ]; then
                log_info "创建虚拟环境..."
                python -m venv .venv
            fi

            # 激活虚拟环境
            source .venv/bin/activate

            # 安装依赖
            log_info "安装依赖..."
            pip install -q -r requirements.txt

            # 初始化数据库
            log_info "初始化数据库..."
            python -c "from db import init_db; init_db()"

            # 启动服务器
            log_success "启动开发服务器 (端口 8000)..."
            uvicorn run:app --host 127.0.0.1 --port 8000 --reload
            ;;

        down|stop)
            log_info "停止本地服务器..."
            # Python脚本无法直接停止，需要手动Ctrl+C
            log_warn "按 Ctrl+C 停止服务器"
            ;;

        test)
            log_info "运行测试..."
            source .venv/bin/activate
            python -m pytest -v
            ;;

        *)
            log_error "未知操作: $action"
            echo "可用操作: up, down, test"
            exit 1
            ;;
    esac
}

# ============================================================================
# Docker部署
# ============================================================================

deploy_docker() {
    local action=$1

    case $action in
        up|start)
            log_info "启动Docker容器..."

            # 检查docker和docker-compose
            if ! command -v docker &> /dev/null; then
                log_error "Docker未安装"
                exit 1
            fi

            # 构建镜像 (如需要)
            if [ "$2" == "--build" ]; then
                log_info "构建Docker镜像..."
                docker build -t $PROJECT_NAME:$VERSION .
            fi

            # 启动容器
            log_info "启动容器..."
            docker-compose up -d

            # 等待容器启动
            sleep 3

            # 检查健康状态
            log_info "检查应用健康状态..."
            for i in {1..30}; do
                if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                    log_success "应用启动成功！"
                    log_info "API访问地址: http://localhost:8000"
                    log_info "API文档: http://localhost:8000/docs"
                    exit 0
                fi
                sleep 1
            done

            log_error "应用启动失败，请检查日志"
            docker-compose logs app
            exit 1
            ;;

        down|stop)
            log_info "停止Docker容器..."
            docker-compose down
            log_success "容器已停止"
            ;;

        restart)
            log_info "重启Docker容器..."
            docker-compose restart
            log_success "容器已重启"
            ;;

        logs)
            log_info "显示容器日志..."
            docker-compose logs -f app
            ;;

        shell)
            log_info "进入容器shell..."
            docker-compose exec app /bin/bash
            ;;

        test)
            log_info "在容器中运行测试..."
            docker-compose exec app python -m pytest -v
            ;;

        *)
            log_error "未知操作: $action"
            echo "可用操作: up, down, restart, logs, shell, test"
            exit 1
            ;;
    esac
}

# ============================================================================
# Kubernetes部署
# ============================================================================

deploy_k8s() {
    local action=$1

    # 检查kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl未安装或未在PATH中"
        exit 1
    fi

    case $action in
        deploy)
            log_info "部署到Kubernetes..."

            # 创建命名空间
            log_info "创建命名空间..."
            kubectl create namespace bazi-api --dry-run=client -o yaml | kubectl apply -f -

            # 应用配置
            log_info "应用Kubernetes配置..."
            kubectl apply -f k8s-deployment.yaml

            # 等待部署完成
            log_info "等待部署完成..."
            kubectl rollout status deployment/bazi-api -n bazi-api --timeout=5m

            log_success "Kubernetes部署完成！"

            # 显示Service信息
            log_info "Service信息："
            kubectl get svc -n bazi-api bazi-api
            ;;

        undeploy|delete)
            log_warn "删除Kubernetes部署..."
            kubectl delete -f k8s-deployment.yaml --ignore-not-found=true
            log_success "部署已删除"
            ;;

        status)
            log_info "显示部署状态..."
            kubectl get deployment -n bazi-api
            kubectl get pods -n bazi-api
            ;;

        logs)
            log_info "显示Pod日志..."
            kubectl logs -n bazi-api -l app=bazi-api -f
            ;;

        shell)
            log_info "进入Pod..."
            POD=$(kubectl get pod -n bazi-api -l app=bazi-api -o jsonpath='{.items[0].metadata.name}')
            kubectl exec -it -n bazi-api $POD -- /bin/bash
            ;;

        port-forward)
            log_info "端口转发 (localhost:8000 -> service:80)..."
            kubectl port-forward -n bazi-api svc/bazi-api 8000:80
            ;;

        *)
            log_error "未知操作: $action"
            echo "可用操作: deploy, undeploy, status, logs, shell, port-forward"
            exit 1
            ;;
    esac
}

# ============================================================================
# 备份和恢复
# ============================================================================

backup() {
    log_info "创建备份..."

    local backup_file="backup-${TIMESTAMP}.tar.gz"
    tar czf $backup_file \
        --exclude=.venv \
        --exclude=__pycache__ \
        --exclude=.pytest_cache \
        --exclude=.ruff_cache \
        --exclude=.git \
        data/

    log_success "备份完成: $backup_file"
}

restore() {
    local backup_file=$1

    if [ -z "$backup_file" ]; then
        log_error "请指定备份文件"
        exit 1
    fi

    log_warn "恢复备份: $backup_file"
    tar xzf $backup_file
    log_success "备份恢复完成"
}

# ============================================================================
# 帮助信息
# ============================================================================

show_help() {
    cat << EOF
BaZi API v$VERSION 部署工具

用法:
    bash deploy.sh [环境] [命令] [选项]

环境:
    local       本地开发环境
    docker      Docker容器
    k8s         Kubernetes集群
    backup      备份/恢复

本地命令:
    up          启动开发服务器
    down        停止服务器
    test        运行测试

Docker命令:
    up          启动容器
    down        停止容器
    restart     重启容器
    logs        查看日志
    shell       进入容器shell
    test        运行测试

Kubernetes命令:
    deploy      部署到K8s
    undeploy    删除K8s部署
    status      显示部署状态
    logs        查看Pod日志
    shell       进入Pod
    port-forward 端口转发

备份命令:
    backup      创建备份
    restore FILE 恢复备份

示例:
    bash deploy.sh local up              # 启动本地开发
    bash deploy.sh docker up --build     # 构建并启动Docker
    bash deploy.sh k8s deploy            # 部署到Kubernetes
    bash deploy.sh backup backup         # 创建备份
    bash deploy.sh backup restore backup-20260226.tar.gz  # 恢复备份

EOF
}

# ============================================================================
# 主程序
# ============================================================================

if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

ENVIRONMENT=$1
ACTION=$2

case $ENVIRONMENT in
    local)
        deploy_local $ACTION "${@:3}"
        ;;
    docker)
        deploy_docker $ACTION "${@:3}"
        ;;
    k8s)
        deploy_k8s $ACTION "${@:3}"
        ;;
    backup)
        if [ "$ACTION" == "backup" ]; then
            backup
        elif [ "$ACTION" == "restore" ]; then
            restore "$3"
        else
            log_error "未知备份命令: $ACTION"
            exit 1
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "未知环境: $ENVIRONMENT"
        show_help
        exit 1
        ;;
esac

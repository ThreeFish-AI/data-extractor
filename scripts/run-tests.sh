#!/bin/bash

# Data Extractor Test Runner Script
# 综合测试执行脚本，支持多种测试模式和报告生成

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印标题
print_title() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

# 打印状态
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_status "检查测试依赖..."
    if ! uv --version >/dev/null 2>&1; then
        print_error "uv 未安装，请先安装 uv"
        exit 1
    fi
    
    # 安装开发依赖
    uv sync --extra dev --quiet
    print_status "依赖检查完成"
}

# 清理旧的测试结果
cleanup() {
    print_status "清理旧的测试结果..."
    rm -rf tests/reports/htmlcov/ tests/reports/ .coverage tests/reports/coverage.xml tests/reports/coverage.json
    mkdir -p tests/reports
    print_status "清理完成"
}

# 运行单元测试
run_unit_tests() {
    print_title "运行单元测试 (Unit Tests)"
    uv run pytest tests/unit/ \
        --cov=extractor \
        --cov-report=term-missing \
        --html=tests/reports/unit-test-report.html \
        --json-report-file=tests/reports/unit-test-results.json \
        -m "unit or not integration" \
        --tb=short \
        -v
}

# 运行集成测试
run_integration_tests() {
    print_title "运行集成测试 (Integration Tests)"
    uv run pytest tests/integration/ \
        --cov=extractor --cov-append \
        --cov-report=term-missing \
        --html=tests/reports/integration-test-report.html \
        --json-report-file=tests/reports/integration-test-results.json \
        -m "integration or not unit" \
        --tb=short \
        -v
}

# 运行完整测试套件
run_full_tests() {
    print_title "运行完整测试套件 (Full Test Suite)"
    uv run pytest tests/ \
        --cov=extractor \
        --cov-report=html:tests/reports/htmlcov \
        --cov-report=term-missing \
        --cov-report=xml:tests/reports/coverage.xml \
        --cov-report=json:tests/reports/coverage.json \
        --html=tests/reports/full-test-report.html \
        --json-report-file=tests/reports/full-test-results.json \
        --tb=short \
        -v
}

# 运行快速测试（不包含慢速测试）
run_quick_tests() {
    print_title "运行快速测试 (Quick Tests)"
    uv run pytest tests/ \
        --cov=extractor \
        --cov-report=term-missing \
        --html=tests/reports/quick-test-report.html \
        --json-report-file=tests/reports/quick-test-results.json \
        -m "not slow" \
        --tb=short \
        -x \
        -v
}

# 运行性能测试
run_performance_tests() {
    print_title "运行性能测试 (Performance Tests)"
    uv run pytest tests/integration/test_comprehensive_integration.py::TestPerformanceAndLoad \
        --html=tests/reports/performance-test-report.html \
        --json-report-file=tests/reports/performance-test-results.json \
        --tb=short \
        -v
}

# 生成覆盖率报告
generate_coverage_report() {
    print_title "生成覆盖率报告"
    if [ -f .coverage ]; then
        uv run coverage html -d tests/reports/htmlcov
        uv run coverage xml -o tests/reports/coverage.xml
        uv run coverage json -o tests/reports/coverage.json
        uv run coverage report --show-missing
        print_status "覆盖率报告已生成:"
        print_status "  HTML: tests/reports/htmlcov/index.html"
        print_status "  XML: tests/reports/coverage.xml"
        print_status "  JSON: tests/reports/coverage.json"
    else
        print_warning "未找到覆盖率数据文件"
    fi
}

# 显示帮助信息
show_help() {
    echo "Data Extractor 测试运行脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  unit          运行单元测试"
    echo "  integration   运行集成测试" 
    echo "  full          运行完整测试套件 (默认)"
    echo "  quick         运行快速测试 (排除慢速测试)"
    echo "  performance   运行性能测试"
    echo "  coverage      仅生成覆盖率报告"
    echo "  clean         清理测试结果"
    echo "  help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 unit       # 仅运行单元测试"
    echo "  $0 quick      # 快速测试，适用于开发阶段"
    echo "  $0 full       # 完整测试，适用于CI/CD"
    echo ""
}

# 主函数
main() {
    case "${1:-full}" in
        "unit")
            check_dependencies
            cleanup
            run_unit_tests
            generate_coverage_report
            ;;
        "integration")
            check_dependencies
            cleanup
            run_integration_tests
            generate_coverage_report
            ;;
        "full")
            check_dependencies
            cleanup
            run_full_tests
            generate_coverage_report
            ;;
        "quick")
            check_dependencies
            cleanup
            run_quick_tests
            generate_coverage_report
            ;;
        "performance")
            check_dependencies
            cleanup
            run_performance_tests
            ;;
        "coverage")
            generate_coverage_report
            ;;
        "clean")
            cleanup
            print_status "清理完成"
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
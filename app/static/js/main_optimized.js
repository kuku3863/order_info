// 性能优化的JavaScript文件
(function() {
    'use strict';
    
    // 工具函数
    function formatDate(date) {
        var d = new Date(date),
            month = '' + (d.getMonth() + 1),
            day = '' + d.getDate(),
            year = d.getFullYear();

        if (month.length < 2) month = '0' + month;
        if (day.length < 2) day = '0' + day;

        return [year, month, day].join('-');
    }

    // 防抖函数
    function debounce(func, wait) {
        var timeout;
        return function executedFunction() {
            var later = function() {
                clearTimeout(timeout);
                func();
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 节流函数
    function throttle(func, limit) {
        var inThrottle;
        return function() {
            var args = arguments;
            var context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(function() {
                    inThrottle = false;
                }, limit);
            }
        };
    }

    // 图片懒加载
    function initLazyLoading() {
        if ('IntersectionObserver' in window) {
            var imageObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        var img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(function(img) {
                imageObserver.observe(img);
            });
        }
    }

    // 图片预览优化
    function initImagePreview() {
        document.addEventListener('change', function(e) {
            if (e.target.type === 'file' && e.target.files.length > 0) {
                var input = e.target;
                var previewContainer = document.createElement('div');
                previewContainer.className = 'row preview-container';
                input.parentNode.insertBefore(previewContainer, input.nextSibling);
                
                Array.from(input.files).forEach(function(file) {
                    if (!file.type.match('image.*')) return;
                    
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        var col = document.createElement('div');
                        col.className = 'col-md-3 col-sm-4 col-xs-6';
                        
                        var thumbnail = document.createElement('div');
                        thumbnail.className = 'thumbnail';
                        
                        var img = document.createElement('img');
                        img.className = 'img-responsive';
                        img.src = e.target.result;
                        img.title = file.name;
                        
                        thumbnail.appendChild(img);
                        col.appendChild(thumbnail);
                        previewContainer.appendChild(col);
                    };
                    
                    reader.readAsDataURL(file);
                });
            }
        });
    }

    // 快速添加订单表单处理
    function initQuickAddForm() {
        var form = document.getElementById('quickAddForm');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                var formData = {};
                var formElements = this.elements;
                for (var i = 0; i < formElements.length; i++) {
                    var element = formElements[i];
                    if (element.name) {
                        formData[element.name] = element.value;
                    }
                }
                
                fetch('/quick_add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                    },
                    body: JSON.stringify(formData)
                })
                .then(function(response) {
                    if (!response.ok) {
                        throw new Error('网络响应错误');
                    }
                    return response.json();
                })
                .then(function(data) {
                    if (data.success) {
                        alert('订单添加成功！');
                        var modal = document.getElementById('quickAddModal');
                        if (modal) {
                            // 使用Bootstrap的modal方法关闭
                            var modalInstance = bootstrap.Modal.getInstance(modal);
                            if (modalInstance) {
                                modalInstance.hide();
                            }
                        }
                        location.reload();
                    } else {
                        alert('添加失败: ' + data.error);
                    }
                })
                .catch(function(error) {
                    console.error('Error:', error);
                    alert('添加失败: ' + error.message);
                });
            });
        }
    }

    // 自动消失的alert
    function initAutoDismissAlerts() {
        var alerts = document.querySelectorAll('.alert-auto-dismiss');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.style.transition = 'opacity 0.5s';
                    alert.style.opacity = '0';
                    setTimeout(function() {
                        if (alert.parentNode) {
                            alert.parentNode.removeChild(alert);
                        }
                    }, 500);
                }
            }, 3000);
        });
    }

    // 表格性能优化
    function initTableOptimizations() {
        var tables = document.querySelectorAll('.table');
        tables.forEach(function(table) {
            // 添加虚拟滚动支持（如果表格很大）
            if (table.rows.length > 100) {
                table.classList.add('table-virtual-scroll');
            }
            
            // 优化排序功能
            var sortableHeaders = table.querySelectorAll('th[data-sort]');
            sortableHeaders.forEach(function(header) {
                header.addEventListener('click', throttle(function() {
                    // 排序逻辑
                    var column = this.getAttribute('data-sort');
                    var direction = this.classList.contains('sort-asc') ? 'desc' : 'asc';
                    
                    // 更新排序状态
                    sortableHeaders.forEach(function(h) {
                        h.classList.remove('sort-asc', 'sort-desc');
                    });
                    this.classList.add('sort-' + direction);
                    
                    // 执行排序
                    sortTable(table, column, direction);
                }, 300));
            });
        });
    }

    // 表格排序函数
    function sortTable(table, column, direction) {
        var tbody = table.querySelector('tbody');
        var rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort(function(a, b) {
            var aVal = a.querySelector('td[data-' + column + ']').getAttribute('data-' + column);
            var bVal = b.querySelector('td[data-' + column + ']').getAttribute('data-' + column);
            
            if (direction === 'asc') {
                return aVal.localeCompare(bVal);
            } else {
                return bVal.localeCompare(aVal);
            }
        });
        
        // 重新插入排序后的行
        rows.forEach(function(row) {
            tbody.appendChild(row);
        });
    }

    // 搜索优化
    function initSearchOptimizations() {
        var searchInputs = document.querySelectorAll('input[type="search"], .search-input');
        searchInputs.forEach(function(input) {
            var debouncedSearch = debounce(function() {
                // 执行搜索逻辑
                performSearch(input.value);
            }, 300);
            
            input.addEventListener('input', debouncedSearch);
        });
    }

    // 搜索执行函数
    function performSearch(query) {
        // 实现搜索逻辑
        console.log('搜索:', query);
    }

    // 初始化所有功能
    function init() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAll);
        } else {
            initAll();
        }
    }

    function initAll() {
        // 初始化各种功能
        initLazyLoading();
        initImagePreview();
        initQuickAddForm();
        initAutoDismissAlerts();
        initTableOptimizations();
        initSearchOptimizations();
        
        // 日期选择器初始化（如果存在）
        if (typeof $.fn !== 'undefined' && $.fn.datepicker) {
            $('.datepicker').datepicker({
                format: 'yyyy-mm-dd',
                autoclose: true,
                todayHighlight: true,
                language: 'zh-CN'
            });
        }
    }

    // 启动应用
    init();

    // 暴露全局函数
    window.formatDate = formatDate;
    window.debounce = debounce;
    window.throttle = throttle;
})(); 
// 性能监控和优化工具
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }
    
    init() {
        // 监控页面加载性能
        this.monitorPageLoad();
        // 监控用户交互性能
        this.monitorUserInteractions();
        // 监控资源加载
        this.monitorResourceLoading();
        // 监控错误
        this.monitorErrors();
        // 定期清理
        setInterval(() => this.cleanup(), 60000); // 每分钟清理一次
    }
    
    monitorPageLoad() {
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    const paintData = performance.getEntriesByType('paint');
                    
                    this.metrics.pageLoad = {
                        // 核心Web指标
                        fcp: this.getPaintTime(paintData, 'first-contentful-paint'),
                        lcp: this.getLargestContentfulPaint(),
                        fid: this.getFirstInputDelay(),
                        cls: this.getCumulativeLayoutShift(),
                        
                        // 传统指标
                        dns: perfData.domainLookupEnd - perfData.domainLookupStart,
                        tcp: perfData.connectEnd - perfData.connectStart,
                        ttfb: perfData.responseStart - perfData.requestStart,
                        domLoad: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        windowLoad: perfData.loadEventEnd - perfData.loadEventStart,
                        total: perfData.loadEventEnd - perfData.fetchStart
                    };
                    
                    this.reportMetrics('pageLoad');
                }, 1000);
            });
        }
    }
    
    monitorUserInteractions() {
        // 监控点击事件响应时间
        document.addEventListener('click', (e) => {
            const start = performance.now();
            const target = e.target;
            
            // 延迟监控
            setTimeout(() => {
                const duration = performance.now() - start;
                if (duration > 100) { // 超过100ms的交互
                    this.metrics.slowInteraction = {
                        type: 'click',
                        target: target.tagName + (target.className ? '.' + target.className.split(' ')[0] : ''),
                        duration: duration,
                        timestamp: Date.now()
                    };
                    this.reportMetrics('slowInteraction');
                }
            }, 100);
        });
        
        // 监控表单提交
        document.addEventListener('submit', (e) => {
            const start = performance.now();
            const form = e.target;
            
            setTimeout(() => {
                const duration = performance.now() - start;
                this.metrics.formSubmit = {
                    action: form.action,
                    duration: duration,
                    timestamp: Date.now()
                };
                this.reportMetrics('formSubmit');
            }, 100);
        });
    }
    
    monitorResourceLoading() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.initiatorType === 'img' && entry.duration > 1000) {
                        this.metrics.slowResource = {
                            name: entry.name,
                            duration: entry.duration,
                            size: entry.transferSize,
                            timestamp: Date.now()
                        };
                        this.reportMetrics('slowResource');
                    }
                }
            });
            observer.observe({ entryTypes: ['resource'] });
        }
    }
    
    monitorErrors() {
        // JavaScript错误
        window.addEventListener('error', (e) => {
            this.metrics.error = {
                type: 'javascript',
                message: e.message,
                filename: e.filename,
                lineno: e.lineno,
                colno: e.colno,
                timestamp: Date.now()
            };
            this.reportMetrics('error');
        });
        
        // Promise错误
        window.addEventListener('unhandledrejection', (e) => {
            this.metrics.error = {
                type: 'promise',
                reason: e.reason,
                timestamp: Date.now()
            };
            this.reportMetrics('error');
        });
        
        // 网络错误
        window.addEventListener('offline', () => {
            this.metrics.error = {
                type: 'network',
                message: '网络连接断开',
                timestamp: Date.now()
            };
            this.reportMetrics('error');
        });
    }
    
    getPaintTime(paintData, paintName) {
        const paint = paintData.find(p => p.name === paintName);
        return paint ? paint.startTime : 0;
    }
    
    getLargestContentfulPaint() {
        if ('PerformanceObserver' in window) {
            return new Promise((resolve) => {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    resolve(lastEntry.startTime);
                });
                observer.observe({ entryTypes: ['largest-contentful-paint'] });
            });
        }
        return 0;
    }
    
    getFirstInputDelay() {
        if ('PerformanceObserver' in window) {
            return new Promise((resolve) => {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const firstEntry = entries[0];
                    resolve(firstEntry.processingStart - firstEntry.startTime);
                });
                observer.observe({ entryTypes: ['first-input'] });
            });
        }
        return 0;
    }
    
    getCumulativeLayoutShift() {
        if ('PerformanceObserver' in window) {
            return new Promise((resolve) => {
                let cls = 0;
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            cls += entry.value;
                        }
                    }
                    resolve(cls);
                });
                observer.observe({ entryTypes: ['layout-shift'] });
            });
        }
        return 0;
    }
    
    reportMetrics(type) {
        // 发送性能数据到服务器
        if (this.metrics[type]) {
            fetch('/api/performance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: type,
                    data: this.metrics[type],
                    url: window.location.href,
                    userAgent: navigator.userAgent
                })
            }).catch(err => {
                console.warn('性能数据发送失败:', err);
            });
        }
    }
    
    cleanup() {
        // 清理过期的性能数据
        const now = Date.now();
        for (const key in this.metrics) {
            if (this.metrics[key].timestamp && now - this.metrics[key].timestamp > 300000) { // 5分钟
                delete this.metrics[key];
            }
        }
    }
}

// 资源预加载器
class ResourcePreloader {
    constructor() {
        this.preloaded = new Set();
    }
    
    preloadImage(src) {
        if (this.preloaded.has(src)) return;
        
        const img = new Image();
        img.src = src;
        this.preloaded.add(src);
    }
    
    preloadCSS(href) {
        if (this.preloaded.has(href)) return;
        
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        document.head.appendChild(link);
        this.preloaded.add(href);
    }
    
    preloadJS(src) {
        if (this.preloaded.has(src)) return;
        
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        document.head.appendChild(script);
        this.preloaded.add(src);
    }
}

// 缓存管理器
class CacheManager {
    constructor() {
        this.cache = new Map();
        this.maxSize = 100; // 最大缓存条目数
    }
    
    // 设置缓存
    set(key, value, ttl = 300000) { // 默认5分钟
        // 检查缓存大小
        if (this.cache.size >= this.maxSize) {
            this.evictOldest();
        }
        
        this.cache.set(key, {
            value,
            timestamp: Date.now(),
            ttl
        });
    }
    
    // 获取缓存
    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        
        if (Date.now() - item.timestamp > item.ttl) {
            this.cache.delete(key);
            return null;
        }
        
        return item.value;
    }
    
    // 清除缓存
    clear() {
        this.cache.clear();
    }
    
    // 清除过期缓存
    cleanup() {
        const now = Date.now();
        for (const [key, item] of this.cache.entries()) {
            if (now - item.timestamp > item.ttl) {
                this.cache.delete(key);
            }
        }
    }
    
    // 淘汰最旧的缓存
    evictOldest() {
        let oldestKey = null;
        let oldestTime = Date.now();
        
        for (const [key, item] of this.cache.entries()) {
            if (item.timestamp < oldestTime) {
                oldestTime = item.timestamp;
                oldestKey = key;
            }
        }
        
        if (oldestKey) {
            this.cache.delete(oldestKey);
        }
    }
    
    // 获取缓存统计
    getStats() {
        return {
            size: this.cache.size,
            maxSize: this.maxSize,
            hitRate: this.hitCount / (this.hitCount + this.missCount) || 0
        };
    }
}

// 网络状态监控
class NetworkMonitor {
    constructor() {
        this.connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        this.monitorConnection();
    }
    
    monitorConnection() {
        if (this.connection) {
            this.connection.addEventListener('change', () => {
                this.reportConnectionChange();
            });
        }
        
        // 监控网络请求
        this.monitorNetworkRequests();
    }
    
    monitorNetworkRequests() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const start = performance.now();
            try {
                const response = await originalFetch(...args);
                const duration = performance.now() - start;
                
                if (duration > 2000) { // 超过2秒的请求
                    this.reportSlowRequest(args[0], duration);
                }
                
                return response;
            } catch (error) {
                const duration = performance.now() - start;
                this.reportFailedRequest(args[0], error, duration);
                throw error;
            }
        };
    }
    
    reportConnectionChange() {
        const info = {
            effectiveType: this.connection.effectiveType,
            downlink: this.connection.downlink,
            rtt: this.connection.rtt,
            saveData: this.connection.saveData
        };
        
        fetch('/api/network-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(info)
        }).catch(console.warn);
    }
    
    reportSlowRequest(url, duration) {
        fetch('/api/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'slowRequest',
                url: url,
                duration: duration,
                timestamp: Date.now()
            })
        }).catch(console.warn);
    }
    
    reportFailedRequest(url, error, duration) {
        fetch('/api/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'failedRequest',
                url: url,
                error: error.message,
                duration: duration,
                timestamp: Date.now()
            })
        }).catch(console.warn);
    }
}

// 内存监控
class MemoryMonitor {
    constructor() {
        this.monitorMemory();
    }
    
    monitorMemory() {
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                const usage = {
                    used: memory.usedJSHeapSize,
                    total: memory.totalJSHeapSize,
                    limit: memory.jsHeapSizeLimit,
                    percentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
                };
                
                // 内存使用率超过80%时报警
                if (usage.percentage > 80) {
                    this.reportHighMemoryUsage(usage);
                }
            }, 30000); // 每30秒检查一次
        }
    }
    
    reportHighMemoryUsage(usage) {
        fetch('/api/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'highMemoryUsage',
                data: usage,
                timestamp: Date.now()
            })
        }).catch(console.warn);
    }
}

// 初始化性能监控
document.addEventListener('DOMContentLoaded', () => {
    // 初始化所有监控器
    window.performanceMonitor = new PerformanceMonitor();
    window.resourcePreloader = new ResourcePreloader();
    window.cacheManager = new CacheManager();
    window.networkMonitor = new NetworkMonitor();
    window.memoryMonitor = new MemoryMonitor();
    
    // 定期清理
    setInterval(() => {
        window.cacheManager.cleanup();
    }, 60000); // 每分钟清理一次
    
    console.log('性能监控系统已启动');
});

// 导出类供其他模块使用
window.PerformanceMonitor = PerformanceMonitor;
window.ResourcePreloader = ResourcePreloader;
window.CacheManager = CacheManager;
window.NetworkMonitor = NetworkMonitor;
window.MemoryMonitor = MemoryMonitor; 
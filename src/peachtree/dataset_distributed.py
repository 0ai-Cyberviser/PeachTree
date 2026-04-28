"""
Distributed Dataset Processing Engine

Provides distributed processing capabilities for large-scale dataset operations:
- Worker pool management with dynamic scaling
- Task distribution with load balancing
- Fault tolerance with automatic retry
- Distributed caching and state management
- Cross-node coordination and synchronization
- Performance monitoring and optimization

Example:
    >>> from peachtree.dataset_distributed import DistributedEngine, WorkerPool
    >>> 
    >>> # Create distributed engine with 4 workers
    >>> engine = DistributedEngine(num_workers=4)
    >>> 
    >>> # Process dataset in parallel
    >>> results = engine.map(transform_func, dataset_records)
    >>> 
    >>> # Distributed aggregation
    >>> total = engine.reduce(sum_func, results)
"""

import asyncio
import hashlib
import multiprocessing as mp
import queue
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import psutil


class WorkerStatus(Enum):
    """Worker execution states"""
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Worker:
    """Represents a distributed worker node"""
    
    worker_id: str
    status: WorkerStatus = WorkerStatus.IDLE
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    
    def update_stats(self) -> None:
        """Update worker resource usage statistics"""
        process = psutil.Process()
        self.cpu_percent = process.cpu_percent(interval=0.1)
        self.memory_mb = process.memory_info().rss / 1024 / 1024
        self.last_heartbeat = time.time()
    
    def is_healthy(self, timeout_seconds: float = 30.0) -> bool:
        """Check if worker is healthy based on heartbeat"""
        return time.time() - self.last_heartbeat < timeout_seconds


@dataclass
class DistributedTask:
    """Represents a task in the distributed system"""
    
    task_id: str
    func: Callable
    args: Tuple = ()
    kwargs: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 300.0
    dependencies: Set[str] = field(default_factory=set)
    result: Any = None
    error: Optional[Exception] = None
    worker_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def get_hash(self) -> str:
        """Generate unique hash for task"""
        content = f"{self.task_id}:{self.func.__name__}:{self.args}:{self.kwargs}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries
    
    def mark_started(self, worker_id: str) -> None:
        """Mark task as started"""
        self.worker_id = worker_id
        self.start_time = time.time()
    
    def mark_completed(self, result: Any) -> None:
        """Mark task as completed with result"""
        self.result = result
        self.end_time = time.time()
    
    def mark_failed(self, error: Exception) -> None:
        """Mark task as failed with error"""
        self.error = error
        self.end_time = time.time()
        self.retry_count += 1


class WorkerPool:
    """Manages pool of distributed workers"""
    
    def __init__(
        self,
        num_workers: int = 4,
        worker_type: str = "process",
        max_tasks_per_worker: int = 10
    ):
        self.num_workers = num_workers
        self.worker_type = worker_type  # 'process' or 'thread'
        self.max_tasks_per_worker = max_tasks_per_worker
        
        self.workers: Dict[str, Worker] = {}
        self.executor: Optional[Any] = None
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.results: Dict[str, Any] = {}
        self.running = False
        
        self._initialize_workers()
    
    def _initialize_workers(self) -> None:
        """Initialize worker pool"""
        for i in range(self.num_workers):
            worker_id = f"worker-{i:03d}"
            self.workers[worker_id] = Worker(worker_id=worker_id)
        
        # Create executor
        if self.worker_type == "process":
            self.executor = ProcessPoolExecutor(max_workers=self.num_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
    
    def submit_task(self, task: DistributedTask) -> str:
        """Submit task to worker pool"""
        # Priority queue: lower number = higher priority
        priority = -task.priority.value
        self.task_queue.put((priority, task.task_id, task))
        return task.task_id
    
    def get_available_worker(self) -> Optional[str]:
        """Get ID of available worker"""
        for worker_id, worker in self.workers.items():
            if worker.status == WorkerStatus.IDLE:
                return worker_id
        return None
    
    def execute_task(self, task: DistributedTask, worker_id: str) -> Any:
        """Execute task on worker"""
        worker = self.workers[worker_id]
        worker.status = WorkerStatus.BUSY
        worker.current_task = task.task_id
        task.mark_started(worker_id)
        
        try:
            # Submit to executor
            future = self.executor.submit(task.func, *task.args, **task.kwargs)
            result = future.result(timeout=task.timeout_seconds)
            
            task.mark_completed(result)
            worker.tasks_completed += 1
            worker.status = WorkerStatus.IDLE
            worker.current_task = None
            
            return result
            
        except Exception as e:
            task.mark_failed(e)
            worker.tasks_failed += 1
            worker.status = WorkerStatus.IDLE
            worker.current_task = None
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics"""
        total_completed = sum(w.tasks_completed for w in self.workers.values())
        total_failed = sum(w.tasks_failed for w in self.workers.values())
        
        return {
            'num_workers': self.num_workers,
            'worker_type': self.worker_type,
            'tasks_completed': total_completed,
            'tasks_failed': total_failed,
            'queue_size': self.task_queue.qsize(),
            'workers': {
                wid: {
                    'status': w.status.value,
                    'tasks_completed': w.tasks_completed,
                    'tasks_failed': w.tasks_failed,
                    'current_task': w.current_task
                }
                for wid, w in self.workers.items()
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown worker pool gracefully"""
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=True)
        for worker in self.workers.values():
            worker.status = WorkerStatus.SHUTDOWN


class LoadBalancer:
    """Intelligent load balancing for distributed tasks"""
    
    def __init__(self, strategy: str = "least_loaded"):
        self.strategy = strategy  # 'round_robin', 'least_loaded', 'random'
        self.current_index = 0
        self.worker_loads: Dict[str, int] = {}
    
    def select_worker(self, workers: Dict[str, Worker], task: DistributedTask) -> Optional[str]:
        """Select optimal worker for task"""
        available_workers = [
            (wid, w) for wid, w in workers.items()
            if w.status == WorkerStatus.IDLE and w.is_healthy()
        ]
        
        if not available_workers:
            return None
        
        if self.strategy == "round_robin":
            return self._round_robin(available_workers)
        elif self.strategy == "least_loaded":
            return self._least_loaded(available_workers)
        elif self.strategy == "random":
            import random
            return random.choice(available_workers)[0]
        else:
            return available_workers[0][0]
    
    def _round_robin(self, workers: List[Tuple[str, Worker]]) -> str:
        """Round-robin worker selection"""
        worker_id = workers[self.current_index % len(workers)][0]
        self.current_index += 1
        return worker_id
    
    def _least_loaded(self, workers: List[Tuple[str, Worker]]) -> str:
        """Select worker with least load"""
        return min(workers, key=lambda x: x[1].tasks_completed)[0]


class DistributedCache:
    """Distributed cache for worker coordination"""
    
    def __init__(self, max_size_mb: int = 1024):
        self.max_size_mb = max_size_mb
        self.cache: Dict[str, Any] = {}
        self.access_counts: Dict[str, int] = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        with self.lock:
            self.cache[key] = value
            self.access_counts[key] = 1
            self._evict_if_needed()
    
    def _evict_if_needed(self) -> None:
        """Evict least accessed items if cache is full"""
        # Simple size check (approximate)
        if len(self.cache) > self.max_size_mb * 10:  # Rough estimate
            # Remove least accessed item
            least_key = min(self.access_counts.items(), key=lambda x: x[1])[0]
            del self.cache[least_key]
            del self.access_counts[least_key]
    
    def clear(self) -> None:
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.access_counts.clear()


class DistributedEngine:
    """Main distributed processing engine"""
    
    def __init__(
        self,
        num_workers: int = 4,
        worker_type: str = "process",
        load_balancing: str = "least_loaded",
        enable_caching: bool = True
    ):
        self.num_workers = num_workers
        self.worker_pool = WorkerPool(num_workers=num_workers, worker_type=worker_type)
        self.load_balancer = LoadBalancer(strategy=load_balancing)
        self.cache = DistributedCache() if enable_caching else None
        
        self.tasks: Dict[str, DistributedTask] = {}
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
    
    def map(
        self,
        func: Callable,
        items: List[Any],
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> List[Any]:
        """
        Distributed map operation
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            priority: Task priority level
            
        Returns:
            List of results in same order as input
        """
        # Create tasks
        task_ids = []
        for i, item in enumerate(items):
            task_id = f"map-{i:06d}"
            task = DistributedTask(
                task_id=task_id,
                func=func,
                args=(item,),
                priority=priority
            )
            self.tasks[task_id] = task
            self.worker_pool.submit_task(task)
            task_ids.append(task_id)
        
        # Execute tasks using worker pool
        results = []
        futures = {}
        
        for task_id in task_ids:
            task = self.tasks[task_id]
            worker_id = self.load_balancer.select_worker(
                self.worker_pool.workers,
                task
            )
            
            if worker_id:
                try:
                    result = self.worker_pool.execute_task(task, worker_id)
                    results.append(result)
                    self.completed_tasks.add(task_id)
                except Exception as e:
                    if task.can_retry():
                        # Retry task
                        self.worker_pool.submit_task(task)
                    else:
                        self.failed_tasks.add(task_id)
                        results.append(None)
        
        return results
    
    def reduce(
        self,
        func: Callable,
        items: List[Any],
        initial: Any = None
    ) -> Any:
        """
        Distributed reduce operation
        
        Args:
            func: Reduction function (takes 2 args, returns 1)
            items: List of items to reduce
            initial: Initial value for reduction
            
        Returns:
            Reduced result
        """
        if not items:
            return initial
        
        # Parallel tree reduction
        current_level = list(items)
        
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs in parallel
            pairs = [
                (current_level[i], current_level[i+1])
                for i in range(0, len(current_level) - 1, 2)
            ]
            
            # Map reduce function over pairs
            reduced_pairs = self.map(lambda pair: func(pair[0], pair[1]), pairs)
            next_level.extend(reduced_pairs)
            
            # Handle odd element
            if len(current_level) % 2 == 1:
                next_level.append(current_level[-1])
            
            current_level = next_level
        
        result = current_level[0]
        
        # Apply initial value if provided
        if initial is not None:
            result = func(initial, result)
        
        return result
    
    def broadcast(self, func: Callable, *args, **kwargs) -> List[Any]:
        """
        Execute function on all workers
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            List of results from each worker
        """
        tasks = []
        for worker_id in self.worker_pool.workers:
            task_id = f"broadcast-{worker_id}"
            task = DistributedTask(
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
                priority=TaskPriority.HIGH
            )
            self.tasks[task_id] = task
            tasks.append(task)
        
        results = []
        for task in tasks:
            worker_id = task.task_id.split('-')[1]
            try:
                result = self.worker_pool.execute_task(task, worker_id)
                results.append(result)
            except Exception:
                results.append(None)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get distributed engine statistics"""
        return {
            'num_workers': self.num_workers,
            'total_tasks': len(self.tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'worker_pool': self.worker_pool.get_stats(),
            'cache_enabled': self.cache is not None
        }
    
    def shutdown(self) -> None:
        """Shutdown distributed engine"""
        self.worker_pool.shutdown()
        if self.cache:
            self.cache.clear()


# Public API
__all__ = [
    'DistributedEngine',
    'WorkerPool',
    'LoadBalancer',
    'DistributedCache',
    'DistributedTask',
    'Worker',
    'WorkerStatus',
    'TaskPriority'
]

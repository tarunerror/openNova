"""
Task scheduler for running tasks at specific times.
Uses APScheduler for flexible scheduling.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Manages scheduled tasks using APScheduler.
    """
    
    def __init__(self):
        """Initialize the task scheduler."""
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Task scheduler initialized and started")
    
    def schedule_once(self, 
                      task_id: str, 
                      func: Callable, 
                      run_date: datetime, 
                      args: Optional[tuple] = None,
                      kwargs: Optional[Dict[str, Any]] = None) -> bool:
        """
        Schedule a task to run once at a specific time.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            run_date: When to run the task
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            self.scheduler.add_job(
                func=func,
                trigger=DateTrigger(run_date=run_date),
                id=task_id,
                args=args or (),
                kwargs=kwargs or {},
                replace_existing=True
            )
            logger.info(f"Scheduled one-time task '{task_id}' for {run_date}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule one-time task '{task_id}': {e}")
            return False
    
    def schedule_interval(self,
                          task_id: str,
                          func: Callable,
                          seconds: Optional[int] = None,
                          minutes: Optional[int] = None,
                          hours: Optional[int] = None,
                          args: Optional[tuple] = None,
                          kwargs: Optional[Dict[str, Any]] = None) -> bool:
        """
        Schedule a task to run at regular intervals.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            seconds: Interval in seconds
            minutes: Interval in minutes
            hours: Interval in hours
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            trigger = IntervalTrigger(
                seconds=seconds or 0,
                minutes=minutes or 0,
                hours=hours or 0
            )
            
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=task_id,
                args=args or (),
                kwargs=kwargs or {},
                replace_existing=True
            )
            
            interval_str = []
            if hours:
                interval_str.append(f"{hours}h")
            if minutes:
                interval_str.append(f"{minutes}m")
            if seconds:
                interval_str.append(f"{seconds}s")
            
            logger.info(f"Scheduled interval task '{task_id}' every {' '.join(interval_str)}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule interval task '{task_id}': {e}")
            return False
    
    def schedule_cron(self,
                      task_id: str,
                      func: Callable,
                      cron_expression: Optional[str] = None,
                      hour: Optional[str] = None,
                      minute: Optional[str] = None,
                      day_of_week: Optional[str] = None,
                      args: Optional[tuple] = None,
                      kwargs: Optional[Dict[str, Any]] = None) -> bool:
        """
        Schedule a task using cron-style scheduling.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            cron_expression: Full cron expression (alternative to individual params)
            hour: Hour (0-23)
            minute: Minute (0-59)
            day_of_week: Day of week (mon, tue, wed, thu, fri, sat, sun)
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            if cron_expression:
                trigger = CronTrigger.from_crontab(cron_expression)
            else:
                trigger = CronTrigger(
                    hour=hour,
                    minute=minute,
                    day_of_week=day_of_week
                )
            
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=task_id,
                args=args or (),
                kwargs=kwargs or {},
                replace_existing=True
            )
            
            logger.info(f"Scheduled cron task '{task_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule cron task '{task_id}': {e}")
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            self.scheduler.remove_job(task_id)
            logger.info(f"Cancelled task '{task_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task '{task_id}': {e}")
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """
        Pause a scheduled task.
        
        Args:
            task_id: ID of the task to pause
            
        Returns:
            True if paused successfully, False otherwise
        """
        try:
            self.scheduler.pause_job(task_id)
            logger.info(f"Paused task '{task_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to pause task '{task_id}': {e}")
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """
        Resume a paused task.
        
        Args:
            task_id: ID of the task to resume
            
        Returns:
            True if resumed successfully, False otherwise
        """
        try:
            self.scheduler.resume_job(task_id)
            logger.info(f"Resumed task '{task_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to resume task '{task_id}': {e}")
            return False
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get information about all scheduled tasks.
        
        Returns:
            List of task information dictionaries
        """
        tasks = []
        for job in self.scheduler.get_jobs():
            tasks.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            })
        return tasks
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task scheduler shut down")


# Global scheduler instance
task_scheduler = TaskScheduler()

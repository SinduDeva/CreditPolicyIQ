"""Parallel processing for high-performance batch change handling."""
import logging
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import time

logger = logging.getLogger(__name__)


class ParallelProcessor:
    """Process changes in parallel for improved performance."""

    def __init__(self, num_workers: Optional[int] = None):
        """
        Initialize parallel processor.

        Args:
            num_workers: Number of worker threads (default: min(4, cpu_count))
        """
        self.logger = logger
        # Use reasonable number of workers - not too many (memory) or too few (slow)
        if num_workers is None:
            num_workers = min(4, max(1, cpu_count() - 1))
        self.num_workers = num_workers
        self.logger.info(f"Initialized ParallelProcessor with {num_workers} workers")

    def process_batch(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        max_workers: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> List[Any]:
        """
        Process items in parallel using worker threads.

        Args:
            items: List of items to process
            process_func: Function to apply to each item
            max_workers: Override number of workers
            timeout: Timeout per item in seconds

        Returns:
            List of results in original order
        """
        if not items:
            return []

        workers = max_workers or self.num_workers
        results = [None] * len(items)
        start_time = time.time()

        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all tasks
                future_to_idx = {
                    executor.submit(process_func, item): idx for idx, item in enumerate(items)
                }

                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_idx, timeout=timeout):
                    idx = future_to_idx[future]
                    try:
                        result = future.result()
                        results[idx] = result
                        completed += 1

                        # Log progress
                        if completed % max(1, len(items) // 10) == 0:
                            elapsed = time.time() - start_time
                            self.logger.debug(
                                f"Progress: {completed}/{len(items)} items ({elapsed:.2f}s)"
                            )

                    except Exception as e:
                        self.logger.error(f"Error processing item {idx}: {e}")
                        results[idx] = None

            elapsed = time.time() - start_time
            self.logger.info(
                f"Batch processing completed: {len(items)} items in {elapsed:.2f}s ({len(items) / elapsed:.1f} items/sec)"
            )

            return results

        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            return items

    def process_changes_parallel(
        self,
        changes: List[Dict[str, Any]],
        mapping_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        suggestion_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process changes in parallel (mapping + suggestion generation).

        Args:
            changes: List of change dictionaries
            mapping_func: Function to map changes to sections
            suggestion_func: Optional function to generate suggestions

        Returns:
            List of processed changes with mapping and suggestions
        """
        try:
            # Process mappings in parallel
            self.logger.info(f"Processing {len(changes)} changes in parallel")

            mapped_changes = self.process_batch(
                changes,
                mapping_func,
                max_workers=self.num_workers,
            )

            # If suggestion function provided, process suggestions in parallel
            if suggestion_func:
                self.logger.info("Generating suggestions in parallel")
                suggestions = self.process_batch(
                    mapped_changes,
                    suggestion_func,
                    max_workers=self.num_workers,
                )

                # Merge suggestions into changes
                for idx, change in enumerate(mapped_changes):
                    if idx < len(suggestions) and suggestions[idx]:
                        change["suggestion"] = suggestions[idx]

            return mapped_changes

        except Exception as e:
            self.logger.error(f"Error in parallel change processing: {e}")
            return changes

    def chunked_process(
        self,
        items: List[Any],
        process_func: Callable[[List[Any]], List[Any]],
        chunk_size: int = 10,
    ) -> List[Any]:
        """
        Process items in chunks (useful for API calls with batch limits).

        Args:
            items: List of items to process
            process_func: Function that processes a chunk
            chunk_size: Size of each chunk

        Returns:
            Flattened list of results
        """
        try:
            results = []

            for i in range(0, len(items), chunk_size):
                chunk = items[i : i + chunk_size]
                self.logger.debug(f"Processing chunk {i // chunk_size + 1} ({len(chunk)} items)")

                try:
                    chunk_results = process_func(chunk)
                    if chunk_results:
                        results.extend(chunk_results)
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {e}")
                    results.extend([None] * len(chunk))

            return results

        except Exception as e:
            self.logger.error(f"Error in chunked processing: {e}")
            return [None] * len(items)

    def map_reduce(
        self,
        items: List[Any],
        map_func: Callable[[Any], Any],
        reduce_func: Callable[[List[Any]], Any],
    ) -> Any:
        """
        Apply map-reduce pattern for aggregation.

        Args:
            items: List of items
            map_func: Function to apply to each item
            reduce_func: Function to aggregate results

        Returns:
            Aggregated result
        """
        try:
            # Map phase - process items in parallel
            mapped_results = self.process_batch(items, map_func)

            # Reduce phase - aggregate results
            filtered_results = [r for r in mapped_results if r is not None]
            reduced = reduce_func(filtered_results)

            return reduced

        except Exception as e:
            self.logger.error(f"Error in map-reduce: {e}")
            return None

    def parallel_mapping_with_progress(
        self,
        changes: List[Dict[str, Any]],
        master_structure: Dict[str, Any],
        mapping_func: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Map changes to master document with progress tracking.

        Args:
            changes: List of changes to map
            master_structure: Master document structure
            mapping_func: Function to map a single change
            progress_callback: Optional callback(completed, total) for progress

        Returns:
            List of mapped changes
        """
        try:
            mapped = []

            def map_with_context(change):
                """Wrapper to pass master_structure to mapping function."""
                return mapping_func(change, master_structure)

            # Use ThreadPoolExecutor for better control and progress tracking
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = [
                    executor.submit(map_with_context, change) for change in changes
                ]

                completed = 0
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        mapped.append(result)
                        completed += 1

                        if progress_callback:
                            progress_callback(completed, len(changes))

                    except Exception as e:
                        self.logger.error(f"Error mapping change: {e}")
                        mapped.append(None)
                        completed += 1

                        if progress_callback:
                            progress_callback(completed, len(changes))

            # Sort back to original order
            # Note: This is a simplified approach; for actual order preservation,
            # would need to track indices
            return [m for m in mapped if m is not None]

        except Exception as e:
            self.logger.error(f"Error in parallel mapping: {e}")
            return []

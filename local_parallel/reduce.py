"""local_parallel/reduce.py -- merge workers' local bests into the global best."""


def reduce_results(results):
    best_allocation = None
    best_score = float("-inf")
    for worker_id, allocation, score in results:
        if allocation is not None and score > best_score:
            best_score = score
            best_allocation = allocation
    return best_allocation, best_score

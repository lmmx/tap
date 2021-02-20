import multiprocessing as mp
from multiprocessing import Process, Pool
from more_itertools import chunked
from tqdm import tqdm
from functools import partial


__all__ = ["batch_multiprocess", "batch_multiprocess_with_dict_updates"]


def batch_multiprocess(function_list, n_cores=mp.cpu_count(), show_progress=True,
        tqdm_desc=None):
    """
    Run a list of functions on `n_cores` (default: all CPU cores),
    with the option to show a progress bar using tqdm (default: shown).
    """
    iterator = [*chunked(function_list, n_cores)]
    if show_progress:
        iterator = tqdm(iterator, desc=tqdm_desc)
    for func_batch in iterator:
        procs = []
        for f in func_batch:
            procs.append(Process(target=f))
        for p in procs:
            p.start()
        for p in procs:
            p.join()


def update_dict_and_pbar(new_entry, callback_dict, callback_pbar=None):
    callback_dict.update(new_entry)
    if callback_pbar:
        callback_pbar.update()


def batch_multiprocess_with_dict_updates(
    function_list, pool_results_dict=None, n_cores=mp.cpu_count(), show_progress=True,
    tqdm_desc=None, sequential=False,
):
    """
    Run a list of functions on `n_cores` (default: all CPU cores),
    with the option to show a progress bar using tqdm (default: shown).
    """
    iterator = [*chunked(function_list, n_cores)]
    no_preexisting_dict = pool_results_dict is None
    if no_preexisting_dict:
        pool_results_dict = {}
    if not sequential:
        pool = Pool(processes=n_cores)
    if show_progress:
        pbar = tqdm(total=len(function_list), desc=tqdm_desc)
    else:
        pbar=None
    update_pool_results = partial(
        update_dict_and_pbar, callback_dict=pool_results_dict, callback_pbar=pbar
    )
    for func_batch in iterator:
        procs = []
        for f in func_batch:
            if sequential:
                update_pool_results(f())
            else:
                pool.apply_async(func=f, callback=update_pool_results)
    if not sequential:
        pool.close()
        pool.join()
    # if pool_results_dict was supplied, it's been updated, otherwise return new dict
    if no_preexisting_dict:
        return pool_results_dict

#def store_dict_entry(dict_entry, result_dict):
#    result_dict.update(dict_entry)
#    return result_dict
#
#
#def make_some_functions(start_dict, n=30):
#    funcs = []
#    for i in range(1,n):
#        f = partial(store_dict_entry, {str(i).zfill(3): i}, result_dict=start_dict)
#        funcs.append(f)
#    return funcs
#
#
#def main():
#    results_go_here = {"BEGIN": 0}
#    funcs = make_some_functions(results_go_here)
#    more_results = batch_multiprocess_with_dict_return(funcs, {"INIT": -1})
#    return more_results
